"""
MCP Tool: SigLIP Embedding-Based RAG (Retrieval-Augmented Generation)

==============================================================================
COURSE CONCEPT #2: CUSTOM TOOLS (MCP - Model Context Protocol)
==============================================================================

This module implements a CUSTOM MCP TOOL for image-based case retrieval using
SigLIP embeddings and Qdrant vector database. It demonstrates:

1. VISUAL RAG: Retrieval-Augmented Generation using image embeddings
2. VECTOR SEARCH: Qdrant integration for efficient similarity search
3. CONTEXT ENHANCEMENT: Retrieved cases enhance diagnostic accuracy
4. MCP COMPLIANCE: Standard tool interface for agent integration

RAG Pipeline:
    Input Image → SigLIP Embedding (768-dim) → Qdrant Vector Search
                                                      ↓
    Similar Cases ← Top-K Results ← Cosine Similarity ← SCIN Dataset

This tool is crucial for the SEQUENTIAL TOOL ORCHESTRATION pattern:
    1. siglip_rag_tool searches for similar historical cases
    2. Results enhance clinical context
    3. medgemma_tool uses enriched context for better diagnosis

Integration with Agent:
    The SOAP Agent calls this tool BEFORE analyze_image to gather
    historical case context, improving diagnostic accuracy through
    evidence-based similar case retrieval.

Vector Database: Qdrant
Embedding Model: google/siglip-base-patch16-224 (768 dimensions)
Dataset: Harvard SCIN Dermatology (10,000+ labeled cases)

Author: Agentic Health Team
Course: Google Agent Development Kit (ADK) Capstone
"""

from typing import Optional, Any, Dict
from app.services.rag_service import RAGService

# ==============================================================================
# LAZY SERVICE INITIALIZATION
# RAG service manages embedding model and Qdrant connection
# ==============================================================================
_rag_service: Optional[RAGService] = None


def _get_service() -> RAGService:
    """
    Get or create RAG service instance using lazy initialization.

    The RAG service encapsulates:
    - SigLIP model for generating image embeddings
    - Qdrant client for vector similarity search
    - SCIN dataset access for dermatology case retrieval
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


# ==============================================================================
# TOOL OPERATION: search_by_image
# Visual RAG - finds similar dermatology cases using image embeddings
# ==============================================================================

async def search_by_image(
    image_base64: str,
    top_k: int = 5,
    min_score: float = 0.7
) -> Dict[str, Any]:
    """
    Search for similar dermatology cases using SigLIP image embeddings.

    This implements VISUAL RAG (Retrieval-Augmented Generation) where:
    1. Input image is converted to 768-dimensional embedding via SigLIP
    2. Qdrant performs cosine similarity search against SCIN dataset
    3. Top-K most similar cases are returned with metadata

    The retrieved cases are used by the SOAP Agent to:
    - Provide evidence-based context for MedGemma analysis
    - Show patients similar historical cases
    - Improve diagnostic confidence through case comparison

    Args:
        image_base64: Base64-encoded image for similarity search
        top_k: Number of similar cases to retrieve (default: 5)
        min_score: Minimum similarity threshold 0-1 (default: 0.7)

    Returns:
        Dict containing:
        - success: Boolean indicating operation success
        - operation: "search_by_image"
        - similar_cases: List of similar cases with:
            - case_id: Unique identifier from SCIN dataset
            - diagnosis: Confirmed diagnosis for the case
            - similarity_score: Cosine similarity (0-1)
            - symptoms: Key features/symptoms of the case
            - treatment: Treatment information if available
            - icd_code: ICD-10 classification code
        - total_found: Number of cases meeting threshold
        - embedding_model: Model used for embedding generation
        - embedding_dimensions: Vector dimensionality (768)
    """
    try:
        similar_cases = await _get_service().find_similar_cases(
            image_base64=image_base64,
            symptoms=None,  # Image-only search
            body_location=None,
            top_k=top_k
        )

        return {
            "success": True,
            "operation": "search_by_image",
            "similar_cases": [
                {
                    "case_id": case.case_id,
                    "diagnosis": case.condition,  # SimilarCase uses 'condition' not 'diagnosis'
                    "similarity_score": case.similarity_score,
                    "symptoms": case.key_features or [],  # Use key_features as symptoms
                    "treatment": case.description or "",  # Use description as treatment info
                    "visual_match_score": case.similarity_score,
                    "icd_code": case.icd_code or ""
                }
                for case in similar_cases
            ],
            "total_found": len(similar_cases),
            "embedding_model": "google/siglip-base-patch16-224",
            "embedding_dimensions": 768
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point for SigLIP-based RAG.

    Args:
        operation: Currently only "search_by_image" is supported
        **kwargs: Operation-specific parameters

    Returns:
        Dict with operation result
    """
    try:
        if operation == "search_by_image":
            return await search_by_image(
                image_base64=kwargs["image_base64"],
                top_k=kwargs.get("top_k", 5),
                min_score=kwargs.get("min_score", 0.7)
            )

        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }

    except KeyError as e:
        return {
            "success": False,
            "error": f"Missing required parameter: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
