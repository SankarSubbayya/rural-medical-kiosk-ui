#!/usr/bin/env python3
"""
SCIN Database Embedding with SigLIP

This script embeds the Harvard SCIN (Skin Condition Image Network) database
using SigLIP (Sigmoid Loss for Language Image Pre-training) and stores
the embeddings in Qdrant for RAG retrieval.

SigLIP is superior to CLIP for this medical use case because:
- Better performance on fine-grained visual tasks
- More efficient training with sigmoid loss
- Better zero-shot classification

Usage:
    python scripts/embed_scin_siglip.py --metadata /path/to/real_labeled_metadata.csv
"""
import asyncio
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
import sys
from tqdm import tqdm
import torch
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from transformers import AutoProcessor, AutoModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Import settings
from app.config import get_settings


class SigLIPEmbedder:
    """SigLIP-based image embedder for medical images."""

    def __init__(self, model_name: str = "google/siglip-base-patch16-224"):
        """
        Initialize SigLIP model.

        Args:
            model_name: HuggingFace model identifier
        """
        print(f"Loading SigLIP model: {model_name}")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

        # Get embedding dimension
        with torch.no_grad():
            dummy_image = Image.new('RGB', (224, 224))
            inputs = self.processor(images=dummy_image, return_tensors="pt").to(self.device)
            outputs = self.model.get_image_features(**inputs)
            self.embedding_dim = outputs.shape[-1]

        print(f"Embedding dimension: {self.embedding_dim}")

    def embed_image(self, image_path: Path) -> np.ndarray:
        """
        Embed a single image using SigLIP.

        Args:
            image_path: Path to image file

        Returns:
            Embedding vector as numpy array
        """
        try:
            image = Image.open(image_path).convert('RGB')

            with torch.no_grad():
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                image_features = self.model.get_image_features(**inputs)

                # Normalize embeddings (important for cosine similarity)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

                return image_features.cpu().numpy()[0]

        except Exception as e:
            print(f"Error embedding image {image_path}: {e}")
            return None

    def embed_batch(self, image_paths: List[Path], batch_size: int = 32) -> List[np.ndarray]:
        """
        Embed multiple images in batches.

        Args:
            image_paths: List of image paths
            batch_size: Number of images to process at once

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = []
            valid_indices = []

            for idx, path in enumerate(batch_paths):
                try:
                    img = Image.open(path).convert('RGB')
                    batch_images.append(img)
                    valid_indices.append(idx)
                except Exception as e:
                    print(f"Error loading {path}: {e}")
                    embeddings.append(None)

            if batch_images:
                with torch.no_grad():
                    inputs = self.processor(images=batch_images, return_tensors="pt").to(self.device)
                    image_features = self.model.get_image_features(**inputs)

                    # Normalize
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)

                    batch_embeddings = image_features.cpu().numpy()

                    # Insert embeddings at correct positions
                    for idx, emb in zip(valid_indices, batch_embeddings):
                        embeddings.insert(i + idx, emb)

        return embeddings


def parse_weighted_labels(labels_str: str) -> Dict[str, float]:
    """Parse weighted labels from string representation."""
    try:
        import ast
        return ast.literal_eval(labels_str)
    except:
        return {}


def create_collection(client: QdrantClient, collection_name: str, vector_size: int):
    """Create or recreate Qdrant collection."""
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except:
        pass

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )
    print(f"Created collection: {collection_name} (vector_size={vector_size})")


async def embed_and_ingest(
    metadata_path: Path,
    images_dir: Path,
    embedder: SigLIPEmbedder,
    client: QdrantClient,
    collection_name: str,
    batch_size: int = 32,
    limit: Optional[int] = None
):
    """
    Embed SCIN images and ingest into Qdrant.

    Args:
        metadata_path: Path to real_labeled_metadata.csv
        images_dir: Directory containing images
        embedder: SigLIPEmbedder instance
        client: QdrantClient instance
        collection_name: Qdrant collection name
        batch_size: Batch size for embedding
        limit: Optional limit on number of images to process
    """
    # Load metadata
    print(f"Loading metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)

    if limit:
        df = df.head(limit)
        print(f"Limited to {limit} records for testing")

    print(f"Loaded {len(df)} records")

    # Process in batches
    points = []

    for idx in tqdm(range(0, len(df), batch_size), desc="Processing batches"):
        batch_df = df.iloc[idx:idx + batch_size]

        # Get image paths
        image_paths = []
        valid_rows = []

        for _, row in batch_df.iterrows():
            image_path = images_dir / row['image_path']
            if image_path.exists():
                image_paths.append(image_path)
                valid_rows.append(row)
            else:
                print(f"Warning: Image not found: {image_path}")

        if not image_paths:
            continue

        # Embed batch
        embeddings = embedder.embed_batch(image_paths, batch_size=batch_size)

        # Create points for Qdrant
        for row, embedding in zip(valid_rows, embeddings):
            if embedding is None:
                continue

            # Parse weighted labels
            weighted_labels = parse_weighted_labels(row.get('weighted_labels', '{}'))

            point = PointStruct(
                id=abs(hash(row['image_id'])) % (10 ** 10),  # Convert to positive int
                vector=embedding.tolist(),
                payload={
                    'image_id': str(row['image_id']),
                    'image_path': row['image_path'],
                    'case_id': str(row['case_id']),
                    'condition': row['condition'],
                    'all_conditions': row.get('all_conditions', '[]'),
                    'weighted_labels': weighted_labels,
                    'age_group': row.get('age_group', 'UNKNOWN'),
                    'sex_at_birth': row.get('sex_at_birth', 'UNKNOWN'),
                    'fitzpatrick_skin_type': row.get('fitzpatrick_skin_type', ''),
                    'condition_label': str(row.get('condition_label', '')),
                    'split': row.get('split', 'unknown'),
                    'description': row.get('description', ''),
                }
            )
            points.append(point)

        # Upload batch to Qdrant
        if len(points) >= batch_size:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"Uploaded {len(points)} points to Qdrant")
            points = []

    # Upload remaining points
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Uploaded final {len(points)} points to Qdrant")


async def main():
    parser = argparse.ArgumentParser(
        description="Embed SCIN database using SigLIP and ingest into Qdrant"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="/home/sankar/data/scin/real_labeled_metadata.csv",
        help="Path to real_labeled_metadata.csv"
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        default="/home/sankar/data/scin/images",
        help="Path to images directory"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="scin_dermatology",
        help="Qdrant collection name"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding (default: 32)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of images to process (for testing)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="google/siglip-base-patch16-224",
        help="SigLIP model name"
    )

    args = parser.parse_args()

    metadata_path = Path(args.metadata)
    images_dir = Path(args.images_dir)

    if not metadata_path.exists():
        print(f"Error: Metadata file not found: {metadata_path}")
        sys.exit(1)

    if not images_dir.exists():
        print(f"Error: Images directory not found: {images_dir}")
        sys.exit(1)

    print("=" * 70)
    print("SCIN Database Embedding with SigLIP")
    print("=" * 70)
    print(f"Metadata: {metadata_path}")
    print(f"Images: {images_dir}")
    print(f"Collection: {args.collection}")
    print(f"Batch size: {args.batch_size}")
    print()

    # Initialize embedder
    embedder = SigLIPEmbedder(model_name=args.model)

    # Initialize Qdrant client
    settings = get_settings()
    if settings.qdrant_embedded:
        client = QdrantClient(path=settings.qdrant_path)
    else:
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )

    # Create collection
    create_collection(client, args.collection, embedder.embedding_dim)

    # Embed and ingest
    await embed_and_ingest(
        metadata_path=metadata_path,
        images_dir=images_dir,
        embedder=embedder,
        client=client,
        collection_name=args.collection,
        batch_size=args.batch_size,
        limit=args.limit
    )

    # Get final stats
    collection_info = client.get_collection(args.collection)
    print()
    print("=" * 70)
    print("Embedding Complete")
    print("=" * 70)
    print(f"Collection: {args.collection}")
    print(f"Total vectors: {collection_info.points_count}")
    print(f"Vector dimension: {embedder.embedding_dim}")
    print()
    print("You can now use this collection for similarity search!")


if __name__ == "__main__":
    asyncio.run(main())
