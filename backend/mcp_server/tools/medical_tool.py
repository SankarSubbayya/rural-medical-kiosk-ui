"""
MCP Tool: Medical Information Processing

Handles symptom extraction and common sense medical checks.
"""

from typing import Optional, Any, Dict
from app.services.chat_service import ChatService

# Lazy-initialized service instance
_chat_service: Optional[ChatService] = None


def _get_service() -> ChatService:
    """Get or create service instance (lazy initialization)."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


async def extract_symptoms(patient_message: str, language: str = "en") -> Dict[str, Any]:
    """Extract medical symptoms from patient message."""
    try:
        from app.models.soap import SOAPConsultation, SOAPStage
        from app.models.chat import ConversationContext

        # Create temporary consultation for MCP calls
        temp_consultation = SOAPConsultation(
            id="temp_mcp",
            patient_id="mcp_test",
            language=language,
            current_stage=SOAPStage.SUBJECTIVE
        )

        # Get or create conversation context
        context = _get_service()._get_or_create_context(temp_consultation)

        # Extract medical information
        result = await _get_service()._extract_medical_info(
            user_message=patient_message,
            assistant_response="",
            context=context
        )

        if result:
            symptoms_list = [
                {
                    "name": s.name,
                    "duration": s.duration,
                    "severity": s.severity,
                    "location": s.location
                }
                for s in result.symptoms
            ]

            return {
                "success": True,
                "operation": "extract_symptoms",
                "symptoms": symptoms_list,
                "medical_history": result.medical_history or [],
                "extracted_count": len(symptoms_list)
            }
        else:
            return {
                "success": True,
                "operation": "extract_symptoms",
                "symptoms": [],
                "medical_history": [],
                "extracted_count": 0
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def check_common_sense(symptom_description: str, language: str = "en") -> Dict[str, Any]:
    """Perform common sense medical check on symptoms."""
    try:
        is_sensible, guidance = await _get_service().common_sense_check(
            symptom_description=symptom_description,
            language=language
        )

        return {
            "success": True,
            "operation": "check_common_sense",
            "is_sensible": is_sensible,
            "makes_sense": is_sensible,  # Test compatibility
            "guidance": guidance,
            "requires_clarification": not is_sensible
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point for medical information processing.

    Args:
        operation: One of "extract_symptoms", "check_common_sense"
        **kwargs: Operation-specific parameters

    Returns:
        Dict with operation result
    """
    try:
        if operation == "extract_symptoms":
            return await extract_symptoms(
                patient_message=kwargs["patient_message"],
                language=kwargs.get("language", "en")
            )

        elif operation == "check_common_sense":
            return await check_common_sense(
                symptom_description=kwargs["symptom_description"],
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
