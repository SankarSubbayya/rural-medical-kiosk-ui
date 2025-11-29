"""
MCP Tool: SigLIP Embedding-Based RAG

Handles image-based case retrieval using SigLIP embeddings.
"""

from typing import Optional, Any, Dict
from app.services.rag_service import RAGService

# Lazy-initialized service instance
_rag_service: Optional[RAGService] = None


def _get_service() -> RAGService:
    """Get or create service instance (lazy initialization)."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


async def search_by_image(
    image_base64: str,
    top_k: int = 5,
    min_score: float = 0.7
) -> Dict[str, Any]:
    """Search for similar cases using SigLIP image embeddings."""
    try:
        similar_cases = await _get_service().search_by_image(
            image_base64=image_base64,
            top_k=top_k,
            min_score=min_score
        )

        return {
            "success": True,
            "operation": "search_by_image",
            "similar_cases": [
                {
                    "case_id": case.case_id,
                    "diagnosis": case.diagnosis,
                    "similarity_score": case.similarity_score,
                    "symptoms": case.symptoms,
                    "treatment": case.treatment,
                    "visual_match_score": case.similarity_score
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
