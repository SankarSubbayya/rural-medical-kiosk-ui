"""
MCP Tool: Medical Image Analysis (MedGemma)

==============================================================================
COURSE CONCEPT #2: CUSTOM TOOLS (MCP - Model Context Protocol)
==============================================================================

This module implements a CUSTOM MCP TOOL for medical image analysis using the
MedGemma 4B vision model. It demonstrates:

1. MCP Tool Pattern: Standard interface with `run(operation, **kwargs)` entry point
2. Lazy Service Initialization: Efficient resource management
3. Structured Output: Consistent response format for agent consumption
4. Multi-Modal Processing: Handles image data (base64) for vision analysis

Tool Integration Flow:
    Agent → Tool Declaration → Gemini Function Call → MCP Tool → Analysis Service
                                                          ↓
    Agent ← Structured Response ← Predictions + Confidence ← MedGemma Model

This tool is called by the SOAP Agent during the OBJECTIVE stage when the
patient provides a dermatology image for analysis.

MCP Compliance:
    - Standard `run()` entry point for all operations
    - Operation-based routing for extensibility
    - Consistent error handling and response format
    - Type-safe parameters with validation

Author: Agentic Health Team
Course: Google Agent Development Kit (ADK) Capstone
"""

from typing import Optional, Any, Dict
from app.services.analysis_service import AnalysisService

# ==============================================================================
# LAZY SERVICE INITIALIZATION
# Demonstrates efficient resource management - service is only created when needed
# ==============================================================================
_analysis_service: Optional[AnalysisService] = None


def _get_service() -> AnalysisService:
    """
    Get or create service instance using lazy initialization pattern.

    This pattern ensures:
    - Service is only created when first needed (not at import time)
    - Single instance is reused across multiple tool invocations
    - Expensive model loading happens once per application lifecycle
    """
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service


# ==============================================================================
# TOOL OPERATION: analyze_image
# Core functionality for dermatological image analysis using MedGemma
# ==============================================================================

async def analyze_image(
    image_base64: str,
    clinical_context: str = "",
    language: str = "en",
    consultation_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Analyze dermatological image using MedGemma vision model.

    This is the primary tool operation that:
    1. Processes base64-encoded image data
    2. Sends to MedGemma 4B model for analysis
    3. Returns structured predictions with confidence scores

    The output is designed for agent consumption - the SOAP Agent uses these
    predictions to explain findings to the patient in simple language.

    Args:
        image_base64: Base64-encoded image data (JPEG/PNG)
        clinical_context: Patient-reported symptoms and history for enhanced analysis
        language: Language code for localized responses
        consultation_id: Session ID for tracking and logging

    Returns:
        Dict containing:
        - success: Boolean indicating operation success
        - operation: Name of the operation performed
        - analysis: Structured analysis results including:
            - visual_description: What the model sees in the image
            - predictions: List of possible conditions with confidence
            - critical_findings: Any urgent findings requiring attention
            - requires_urgent_attention: Boolean for triage
            - confidence_level: Overall confidence in the analysis
        - model_used: Identifier for the analysis model
    """
    try:
        from app.models.analysis import ImageAnalysisRequest, BodyLocation

        # Strip data URL prefix if present
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',', 1)[1]

        # Create request object with required fields
        request = ImageAnalysisRequest(
            consultation_id=consultation_id,
            image_base64=image_base64,
            body_location=BodyLocation(primary="unknown"),
            patient_description=clinical_context,
            symptoms=[]
        )

        result = await _get_service().analyze_image(request)

        return {
            "success": True,
            "operation": "analyze_image",
            "analysis": {
                "visual_description": result.visual_description,
                "predictions": [
                    {
                        "condition": p.condition,
                        "confidence": p.confidence,
                        "reasoning": p.reasoning,
                        "icd_code": p.icd_code,
                        "is_critical": p.is_critical,
                        "urgency_level": p.urgency_level
                    }
                    for p in result.predictions
                ],
                "critical_findings": result.critical_findings,
                "requires_urgent_attention": result.requires_urgent_attention,
                "confidence_level": result.confidence_level
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
                language=kwargs.get("language", "en"),
                consultation_id=kwargs.get("consultation_id", "unknown")
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
