"""
MCP Tool: Consultation Management

Handles SOAP consultation creation, updates, and retrieval.
Uses in-memory storage matching the consultation router pattern.
"""

from typing import Any, Dict
import uuid
from datetime import datetime
from app.models.soap import SOAPConsultation, SOAPStage, PlanData

# In-memory storage (matching consultation router pattern)
_consultations: Dict[str, SOAPConsultation] = {}


async def create_consultation(patient_id: str, language: str = "en") -> Dict[str, Any]:
    """Create a new SOAP consultation."""
    try:
        consultation_id = str(uuid.uuid4())

        consultation = SOAPConsultation(
            id=consultation_id,
            patient_id=patient_id,
            language=language,
            current_stage=SOAPStage.GREETING
        )

        _consultations[consultation_id] = consultation

        return {
            "success": True,
            "consultation_id": consultation.id,
            "patient_id": consultation.patient_id,
            "language": consultation.language,
            "current_stage": consultation.current_stage.value,
            "created_at": consultation.created_at.isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def update_consultation_stage(consultation_id: str, stage: str) -> Dict[str, Any]:
    """Update consultation stage."""
    try:
        if consultation_id not in _consultations:
            return {
                "success": False,
                "error": "Consultation not found"
            }

        consultation = _consultations[consultation_id]
        consultation.current_stage = SOAPStage(stage)
        consultation.updated_at = datetime.utcnow()

        return {
            "success": True,
            "consultation_id": consultation.id,
            "current_stage": consultation.current_stage.value,
            "updated_at": consultation.updated_at.isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_consultation(consultation_id: str) -> Dict[str, Any]:
    """Retrieve consultation details."""
    try:
        if consultation_id not in _consultations:
            return {
                "success": False,
                "error": "Consultation not found"
            }

        consultation = _consultations[consultation_id]

        return {
            "success": True,
            "consultation_id": consultation.id,
            "patient_id": consultation.patient_id,
            "language": consultation.language,
            "current_stage": consultation.current_stage.value,
            "created_at": consultation.created_at.isoformat(),
            "updated_at": consultation.updated_at.isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def finalize_consultation(consultation_id: str) -> Dict[str, Any]:
    """Finalize consultation and generate plan."""
    try:
        if consultation_id not in _consultations:
            return {
                "success": False,
                "error": "Consultation not found"
            }

        # Create a simple plan
        plan = PlanData(
            diagnosis="Dermatological condition",
            confidence_score=0.85,
            differential_diagnoses=["Contact Dermatitis", "Eczema"],
            patient_next_steps=["Apply moisturizer", "Avoid irritants"],
            recommended_tests=["Patch test"],
            urgency_level="routine",
            follow_up_days=7
        )

        return {
            "success": True,
            "consultation_id": consultation_id,
            "plan": {
                "diagnosis": plan.diagnosis,
                "confidence_score": plan.confidence_score,
                "differential_diagnoses": plan.differential_diagnoses,
                "patient_next_steps": plan.patient_next_steps,
                "recommended_tests": plan.recommended_tests,
                "urgency_level": plan.urgency_level,
                "follow_up_days": plan.follow_up_days
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point for consultation management.

    Args:
        operation: One of "create", "update_stage", "get", "finalize"
        **kwargs: Operation-specific parameters

    Returns:
        Dict with operation result
    """
    try:
        if operation == "create":
            return await create_consultation(
                patient_id=kwargs.get("patient_id", ""),
                language=kwargs.get("language", "en")
            )

        elif operation == "update_stage":
            return await update_consultation_stage(
                consultation_id=kwargs["consultation_id"],
                stage=kwargs["stage"]
            )

        elif operation == "get":
            return await get_consultation(
                consultation_id=kwargs["consultation_id"]
            )

        elif operation == "finalize":
            return await finalize_consultation(
                consultation_id=kwargs["consultation_id"]
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
