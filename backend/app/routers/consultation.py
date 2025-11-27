"""
Consultation Router - Main SOAP consultation management endpoints.
"""
import uuid
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.soap import (
    SOAPConsultation, SOAPStage, UrgencyLevel,
    SubjectiveData, ObjectiveData, AssessmentData, PlanData,
    ConsultationSummary
)


router = APIRouter(prefix="/consultation", tags=["consultation"])

# In-memory storage (replace with database in production)
_consultations: Dict[str, SOAPConsultation] = {}


class CreateConsultationRequest(BaseModel):
    """Request to create a new consultation."""
    patient_id: str
    language: str = "en"
    kiosk_id: str | None = None


class CreateConsultationResponse(BaseModel):
    """Response with new consultation details."""
    consultation_id: str
    current_stage: SOAPStage
    message: str


@router.post("/create", response_model=CreateConsultationResponse)
async def create_consultation(request: CreateConsultationRequest):
    """
    Create a new SOAP consultation session.

    This initializes a consultation and starts the SOAP flow.
    """
    consultation_id = str(uuid.uuid4())

    consultation = SOAPConsultation(
        id=consultation_id,
        patient_id=request.patient_id,
        kiosk_id=request.kiosk_id,
        language=request.language,
        current_stage=SOAPStage.GREETING
    )

    _consultations[consultation_id] = consultation

    return CreateConsultationResponse(
        consultation_id=consultation_id,
        current_stage=SOAPStage.GREETING,
        message="Consultation created. Ready to begin."
    )


@router.get("/{consultation_id}", response_model=SOAPConsultation)
async def get_consultation(consultation_id: str):
    """
    Get the current state of a consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    return _consultations[consultation_id]


@router.get("/{consultation_id}/summary", response_model=ConsultationSummary)
async def get_consultation_summary(consultation_id: str):
    """
    Get a brief summary of a consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    c = _consultations[consultation_id]

    top_condition = None
    if c.assessment.possible_conditions:
        top_condition = c.assessment.possible_conditions[0].condition

    return ConsultationSummary(
        id=c.id,
        patient_id=c.patient_id,
        created_at=c.created_at,
        chief_complaint=c.subjective.chief_complaint or "Not specified",
        urgency_level=c.assessment.urgency_level,
        current_stage=c.current_stage,
        top_condition=top_condition
    )


class UpdateStageRequest(BaseModel):
    """Request to update consultation stage."""
    stage: SOAPStage


@router.put("/{consultation_id}/stage")
async def update_stage(consultation_id: str, request: UpdateStageRequest):
    """
    Update the current stage of a consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation = _consultations[consultation_id]
    consultation.current_stage = request.stage
    consultation.updated_at = datetime.utcnow()

    if request.stage == SOAPStage.COMPLETED:
        consultation.completed_at = datetime.utcnow()

    return {"status": "updated", "current_stage": request.stage}


class ConsentRequest(BaseModel):
    """Request to record consent."""
    consent_given: bool


@router.post("/{consultation_id}/consent")
async def record_consent(consultation_id: str, request: ConsentRequest):
    """
    Record patient consent for the consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation = _consultations[consultation_id]
    consultation.consent_given = request.consent_given

    if request.consent_given:
        consultation.consent_timestamp = datetime.utcnow()

    return {"status": "recorded", "consent_given": request.consent_given}


@router.put("/{consultation_id}/subjective")
async def update_subjective(consultation_id: str, data: SubjectiveData):
    """
    Update the subjective section of the consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation = _consultations[consultation_id]
    consultation.subjective = data
    consultation.updated_at = datetime.utcnow()

    return {"status": "updated"}


@router.put("/{consultation_id}/objective")
async def update_objective(consultation_id: str, data: ObjectiveData):
    """
    Update the objective section of the consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation = _consultations[consultation_id]
    consultation.objective = data
    consultation.updated_at = datetime.utcnow()

    return {"status": "updated"}


@router.put("/{consultation_id}/assessment")
async def update_assessment(consultation_id: str, data: AssessmentData):
    """
    Update the assessment section of the consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation = _consultations[consultation_id]
    consultation.assessment = data
    consultation.updated_at = datetime.utcnow()

    return {"status": "updated"}


@router.put("/{consultation_id}/plan")
async def update_plan(consultation_id: str, data: PlanData):
    """
    Update the plan section of the consultation.
    """
    if consultation_id not in _consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation = _consultations[consultation_id]
    consultation.plan = data
    consultation.updated_at = datetime.utcnow()

    return {"status": "updated"}


@router.get("/patient/{patient_id}/history")
async def get_patient_history(patient_id: str):
    """
    Get consultation history for a patient.
    """
    history = [
        ConsultationSummary(
            id=c.id,
            patient_id=c.patient_id,
            created_at=c.created_at,
            chief_complaint=c.subjective.chief_complaint or "Not specified",
            urgency_level=c.assessment.urgency_level,
            current_stage=c.current_stage,
            top_condition=c.assessment.possible_conditions[0].condition if c.assessment.possible_conditions else None
        )
        for c in _consultations.values()
        if c.patient_id == patient_id
    ]

    return {"history": history}


# Helper function to get consultation (used by other routers)
def get_consultation_by_id(consultation_id: str) -> SOAPConsultation | None:
    """Get consultation by ID (for use by other modules)."""
    return _consultations.get(consultation_id)


def save_consultation(consultation: SOAPConsultation):
    """Save consultation (for use by other modules)."""
    _consultations[consultation.id] = consultation
