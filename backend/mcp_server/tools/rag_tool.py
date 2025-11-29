"""
MCP Tool: Case-Based Reasoning (RAG)

Handles retrieval of similar dermatology cases from Qdrant vector database.
"""

from typing import Any, Dict, List, Optional
from app.services.rag_service import RAGService

# Lazy-initialized service instance
_rag_service: Optional[RAGService] = None


def _get_rag_service() -> RAGService:
    """Get or create RAG service instance (lazy initialization)."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


async def find_similar_cases(
    symptoms: List[str],
    image_base64: str = None,
    top_k: int = 5,
    language: str = "en"
) -> Dict[str, Any]:
    """Find similar dermatology cases using RAG."""
    try:
        rag_service = _get_rag_service()
        similar_cases = await rag_service.find_similar_cases(
            symptoms=symptoms,
            image_base64=image_base64,
            top_k=top_k
        )

        return {
            "success": True,
            "operation": "find_similar_cases",
            "similar_cases": [
                {
                    "case_id": case.case_id,
                    "diagnosis": case.diagnosis,
                    "similarity_score": case.similarity_score,
                    "symptoms": case.symptoms,
                    "treatment": case.treatment,
                    "outcome": case.outcome
                }
                for case in similar_cases
            ],
            "total_found": len(similar_cases),
            "search_method": "hybrid" if image_base64 else "text_only"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point for case-based reasoning.

    Args:
        operation: Currently only "find_similar_cases" is supported
        **kwargs: Operation-specific parameters

    Returns:
        Dict with operation result
    """
    try:
        if operation == "find_similar_cases":
            return await find_similar_cases(
                symptoms=kwargs.get("symptoms", []),
                image_base64=kwargs.get("image_base64"),
                top_k=kwargs.get("top_k", 5),
                language=kwargs.get("language", "en")
            )

        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
