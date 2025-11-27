"""
RAG Service - Retrieval-Augmented Generation using SCIN database with Qdrant.

This service handles:
- Embedding generation using SigLIP-2 (images) and text embeddings
- Vector storage and retrieval using Qdrant
- Similar case finding for dermatological conditions
"""
import os
import uuid
import base64
from typing import List, Optional
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
import numpy as np
from PIL import Image
import io

from ..config import get_settings, ICD_CODES
from ..models.analysis import SimilarCase, RAGResult, SCINRecord


class RAGService:
    """
    RAG service for SCIN database retrieval using Qdrant.

    Supports:
    - Embedded mode (no separate server)
    - Client-server mode
    - Multi-vector search (image + text)

    Uses:
    - SigLIP-2 for image embeddings
    - MiniLM for text embeddings
    - Qdrant for vector storage
    """

    IMAGE_EMBEDDING_DIM = 768   # SigLIP-2
    TEXT_EMBEDDING_DIM = 384    # MiniLM

    def __init__(self):
        self.settings = get_settings()

        # Initialize Qdrant client
        if self.settings.qdrant_embedded:
            # Embedded mode - no separate server needed
            self.client = QdrantClient(path=self.settings.qdrant_path)
        else:
            # Client-server mode
            self.client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port
            )

        self.collection_name = self.settings.qdrant_collection_name
        self._ensure_collection()

        # Embedding models (lazy load)
        self._siglip_model = None
        self._siglip_processor = None
        self._text_model = None

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "image": VectorParams(
                        size=self.IMAGE_EMBEDDING_DIM,
                        distance=Distance.COSINE
                    ),
                    "text": VectorParams(
                        size=self.TEXT_EMBEDDING_DIM,
                        distance=Distance.COSINE
                    ),
                }
            )
            print(f"Created Qdrant collection: {self.collection_name}")

    def _load_siglip(self):
        """Lazy load SigLIP-2 model for image embeddings."""
        if self._siglip_model is None:
            try:
                from transformers import AutoProcessor, AutoModel
                import torch

                model_name = "google/siglip-base-patch16-224"
                self._siglip_processor = AutoProcessor.from_pretrained(model_name)
                self._siglip_model = AutoModel.from_pretrained(model_name)
                self._siglip_model.eval()

                if torch.cuda.is_available():
                    self._siglip_model = self._siglip_model.cuda()

            except ImportError:
                print("Warning: transformers not installed. Using placeholder embeddings.")
                self._siglip_model = "placeholder"

    def _load_text_model(self):
        """Lazy load text embedding model."""
        if self._text_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._text_model = SentenceTransformer('all-MiniLM-L6-v2')

            except ImportError:
                print("Warning: sentence-transformers not installed. Using placeholder embeddings.")
                self._text_model = "placeholder"

    async def generate_image_embedding(self, image_base64: str) -> List[float]:
        """
        Generate embedding for an image using SigLIP-2.

        Args:
            image_base64: Base64 encoded image

        Returns:
            List of floats representing the image embedding
        """
        self._load_siglip()

        if self._siglip_model == "placeholder":
            # Return random embedding for testing
            return list(np.random.randn(self.IMAGE_EMBEDDING_DIM).astype(float))

        import torch

        # Decode image
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Process image
        inputs = self._siglip_processor(images=image, return_tensors="pt")

        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Generate embedding
        with torch.no_grad():
            outputs = self._siglip_model.get_image_features(**inputs)
            embedding = outputs.cpu().numpy().flatten().tolist()

        return embedding

    async def generate_text_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text description.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the text embedding
        """
        self._load_text_model()

        if self._text_model == "placeholder":
            return list(np.random.randn(self.TEXT_EMBEDDING_DIM).astype(float))

        embedding = self._text_model.encode(text)
        return embedding.tolist()

    async def find_similar_cases(
        self,
        image_base64: Optional[str] = None,
        symptoms: Optional[List[str]] = None,
        body_location: Optional[str] = None,
        top_k: int = 5
    ) -> List[SimilarCase]:
        """
        Find similar cases from the SCIN database using Qdrant.

        Uses multimodal retrieval combining:
        - Image similarity (if image provided)
        - Text similarity (symptoms + location)

        Args:
            image_base64: Base64 encoded image
            symptoms: List of symptom descriptions
            body_location: Body location of the condition
            top_k: Number of results to return

        Returns:
            List of similar cases with similarity scores
        """
        results = []

        # Image-based retrieval
        if image_base64:
            image_embedding = await self.generate_image_embedding(image_base64)

            try:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=("image", image_embedding),
                    limit=top_k,
                    with_payload=True
                )

                for hit in search_results:
                    results.append(SimilarCase(
                        case_id=str(hit.id),
                        condition=hit.payload.get("condition", "Unknown"),
                        icd_code=hit.payload.get("icd_code", ""),
                        similarity_score=hit.score,
                        image_url=hit.payload.get("image_path"),
                        description=hit.payload.get("description"),
                        key_features=hit.payload.get("features", [])
                    ))
            except Exception as e:
                print(f"Image retrieval error: {e}")

        # Text-based retrieval
        if symptoms or body_location:
            query_text = " ".join([
                " ".join(symptoms) if symptoms else "",
                body_location or ""
            ]).strip()

            if query_text:
                text_embedding = await self.generate_text_embedding(query_text)

                try:
                    text_results = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=("text", text_embedding),
                        limit=top_k,
                        with_payload=True
                    )

                    for hit in text_results:
                        # Check if already in results (from image search)
                        existing = next((r for r in results if r.case_id == str(hit.id)), None)
                        if existing:
                            # Boost score for matches in both modalities
                            existing.similarity_score = (existing.similarity_score + hit.score) / 2 + 0.1
                        else:
                            results.append(SimilarCase(
                                case_id=str(hit.id),
                                condition=hit.payload.get("condition", "Unknown"),
                                icd_code=hit.payload.get("icd_code", ""),
                                similarity_score=hit.score * 0.8,  # Weight text lower than image
                                description=hit.payload.get("description"),
                                key_features=hit.payload.get("features", [])
                            ))
                except Exception as e:
                    print(f"Text retrieval error: {e}")

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    async def add_scin_record(self, record: SCINRecord) -> str:
        """
        Add a record from the SCIN database to Qdrant.

        Args:
            record: SCIN database record

        Returns:
            Record ID
        """
        record_id = record.id or str(uuid.uuid4())

        vectors = {}

        # Generate image embedding
        if record.image_path and Path(record.image_path).exists():
            with open(record.image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode()
            vectors["image"] = await self.generate_image_embedding(image_base64)
        else:
            # Placeholder if no image
            vectors["image"] = [0.0] * self.IMAGE_EMBEDDING_DIM

        # Generate text embedding
        text_content = f"{record.condition} {record.description} {' '.join(record.characteristics)}"
        vectors["text"] = await self.generate_text_embedding(text_content)

        # Prepare features as list
        features = record.characteristics if isinstance(record.characteristics, list) else []

        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=record_id,
                vector=vectors,
                payload={
                    "condition": record.condition,
                    "icd_code": record.icd_code,
                    "description": record.description,
                    "image_path": record.image_path or "",
                    "body_location": record.body_location or "",
                    "skin_type": record.skin_type or "",
                    "features": features
                }
            )]
        )

        return record_id

    async def ingest_scin_database(self, data_dir: str) -> int:
        """
        Ingest the SCIN database from a directory.

        Expected structure:
        data_dir/
        ├── images/
        │   ├── condition_1/
        │   │   ├── image_001.jpg
        │   │   └── ...
        │   └── condition_2/
        │       └── ...
        └── metadata.json  (or .csv)

        Args:
            data_dir: Path to SCIN data directory

        Returns:
            Number of records ingested
        """
        import json

        data_path = Path(data_dir)
        count = 0

        # Check for metadata file
        metadata_path = data_path / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)

            for record_data in metadata.get("records", []):
                record = SCINRecord(
                    id=record_data.get("id", str(uuid.uuid4())),
                    condition=record_data["condition"],
                    icd_code=record_data.get("icd_code", ICD_CODES.get(
                        record_data["condition"].lower().replace(" ", "_"),
                        "L98.9"
                    )),
                    description=record_data.get("description", ""),
                    image_path=str(data_path / record_data.get("image_path", "")),
                    body_location=record_data.get("body_location"),
                    skin_type=record_data.get("skin_type"),
                    characteristics=record_data.get("characteristics", [])
                )
                await self.add_scin_record(record)
                count += 1

                if count % 100 == 0:
                    print(f"Ingested {count} records...")

        else:
            # Fallback: Scan directory structure
            images_dir = data_path / "images"
            if images_dir.exists():
                for condition_dir in images_dir.iterdir():
                    if condition_dir.is_dir():
                        condition = condition_dir.name.replace("_", " ").title()
                        icd_code = ICD_CODES.get(
                            condition_dir.name.lower(),
                            "L98.9"
                        )

                        for image_file in condition_dir.glob("*.jpg"):
                            record = SCINRecord(
                                id=str(uuid.uuid4()),
                                condition=condition,
                                icd_code=icd_code,
                                description=f"Image of {condition}",
                                image_path=str(image_file),
                                characteristics=[]
                            )
                            await self.add_scin_record(record)
                            count += 1

                            if count % 100 == 0:
                                print(f"Ingested {count} records...")

        return count

    def get_collection_stats(self) -> dict:
        """Get statistics about the Qdrant collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": str(info.status)
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_collection(self):
        """Delete the collection (for testing/reset)."""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"Error deleting collection: {e}")
