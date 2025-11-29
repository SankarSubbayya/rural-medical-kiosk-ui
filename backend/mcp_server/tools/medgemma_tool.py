"""
MCP Tool: Medical Image Analysis (MedGemma)

Handles dermatological image analysis using MedGemma model.
"""

from typing import Optional, Any, Dict
from app.services.analysis_service import AnalysisService

# Lazy-initialized service instance
_analysis_service: Optional[AnalysisService] = None


def _get_service() -> AnalysisService:
    """Get or create service instance (lazy initialization)."""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service


async def analyze_image(image_base64: str, clinical_context: str = "", language: str = "en") -> Dict[str, Any]:
    """Analyze dermatological image using MedGemma."""
    try:
        result = await _get_service().analyze_image(
            image_base64=image_base64,
            clinical_context=clinical_context,
            language=language
        )

        return {
            "success": True,
            "operation": "analyze_image",
            "analysis": {
                "visual_description": result.visual_description,
                "predictions": [
                    {
                        "condition": p.condition,
                        "confidence": p.confidence,
                        "description": p.description
                    }
                    for p in result.predictions
                ],
                "risk_assessment": result.risk_assessment,
                "recommendations": result.recommendations
            },
            "model_used": "medgemma-4b-it:q8"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point for medical image analysis.

    Args:
        operation: Currently only "analyze_image" is supported
        **kwargs: Operation-specific parameters

    Returns:
        Dict with operation result
    """
    try:
        if operation == "analyze_image":
            return await analyze_image(
                image_base64=kwargs["image_base64"],
                clinical_context=kwargs.get("clinical_context", ""),
                language=kwargs.get("language", "en")
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
