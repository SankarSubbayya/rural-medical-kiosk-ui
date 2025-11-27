"""
SOAP (Subjective, Objective, Assessment, Plan) data models.

The SOAP framework structures medical consultations:
- Subjective: Patient's narrative and reported symptoms
- Objective: Observable findings (images, measurements)
- Assessment: Analysis and possible conditions
- Plan: Recommended actions and guidance
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SOAPStage(str, Enum):
    """Current stage in the SOAP consultation flow."""
    GREETING = "greeting"
    SUBJECTIVE = "subjective"
    OBJECTIVE = "objective"
    ASSESSMENT = "assessment"
    PLAN = "plan"
    SUMMARY = "summary"
    COMPLETED = "completed"


class UrgencyLevel(str, Enum):
    """Urgency classification for the condition."""
    EMERGENCY = "emergency"      # Immediate medical attention required
    URGENT = "urgent"            # See doctor within 24-48 hours
    ROUTINE = "routine"          # Schedule appointment when convenient
    SELF_CARE = "self_care"      # Can manage at home with guidance


class Symptom(BaseModel):
    """A single symptom reported by the patient."""
    name: str
    duration: Optional[str] = None
    severity: Optional[str] = None  # mild, moderate, severe
    location: Optional[str] = None
    characteristics: List[str] = Field(default_factory=list)


class SubjectiveData(BaseModel):
    """
    Subjective: The patient's narrative.
    Filtered to extract medically relevant information.
    """
    raw_transcript: List[str] = Field(
        default_factory=list,
        description="Complete voice transcripts from patient"
    )
    filtered_narrative: str = Field(
        default="",
        description="Medically relevant information extracted"
    )
    chief_complaint: str = Field(
        default="",
        description="Primary reason for consultation"
    )
    symptoms: List[Symptom] = Field(
        default_factory=list,
        description="List of reported symptoms"
    )
    onset: Optional[str] = Field(
        default=None,
        description="When the condition started"
    )
    duration: Optional[str] = Field(
        default=None,
        description="How long the condition has persisted"
    )
    aggravating_factors: List[str] = Field(
        default_factory=list,
        description="What makes it worse"
    )
    relieving_factors: List[str] = Field(
        default_factory=list,
        description="What makes it better"
    )
    previous_treatments: List[str] = Field(
        default_factory=list,
        description="Treatments already tried"
    )
    medical_history: Optional[str] = Field(
        default=None,
        description="Relevant medical history"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="Known allergies"
    )


class CapturedImage(BaseModel):
    """An image captured during the consultation."""
    id: str
    timestamp: datetime
    body_location: str
    image_url: str  # Local path or cloud URL
    thumbnail_url: Optional[str] = None
    consent_given: bool = True
    consent_timestamp: Optional[datetime] = None


class ObjectiveData(BaseModel):
    """
    Objective: Observable and measurable findings.
    Includes images and AI-generated observations.
    """
    images: List[CapturedImage] = Field(
        default_factory=list,
        description="Captured images of the condition"
    )
    primary_body_location: Optional[str] = Field(
        default=None,
        description="Main affected area"
    )
    visual_observations: List[str] = Field(
        default_factory=list,
        description="AI-generated visual findings"
    )
    lesion_characteristics: Optional[dict] = Field(
        default=None,
        description="Size, shape, color, borders, etc."
    )
    distribution_pattern: Optional[str] = Field(
        default=None,
        description="How the condition is distributed"
    )


class DifferentialDiagnosis(BaseModel):
    """A possible condition with supporting evidence."""
    condition: str = Field(description="Name of the condition")
    icd_code: str = Field(description="ICD-10 code")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score (0-1)"
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence supporting this diagnosis"
    )
    contraindications: List[str] = Field(
        default_factory=list,
        description="Evidence against this diagnosis"
    )
    is_critical: bool = Field(
        default=False,
        description="Whether this is a critical condition"
    )


class RAGSource(BaseModel):
    """A source from the SCIN database used in assessment."""
    source_id: str
    condition: str
    similarity_score: float
    image_url: Optional[str] = None
    description: Optional[str] = None


class AssessmentData(BaseModel):
    """
    Assessment: Analysis of the condition.
    Provides possible diagnoses with ICD codes, NOT definitive diagnoses.
    """
    possible_conditions: List[DifferentialDiagnosis] = Field(
        default_factory=list,
        description="Ranked list of possible conditions"
    )
    urgency_level: UrgencyLevel = Field(
        default=UrgencyLevel.ROUTINE,
        description="How urgently medical attention is needed"
    )
    urgency_reasoning: str = Field(
        default="",
        description="Explanation for urgency classification"
    )
    rag_sources: List[RAGSource] = Field(
        default_factory=list,
        description="Similar cases from SCIN database"
    )
    confidence_overall: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="Overall confidence in assessment"
    )
    requires_professional: bool = Field(
        default=True,
        description="Whether professional consultation is recommended"
    )
    disclaimer: str = Field(
        default="This is not a medical diagnosis. Please consult a healthcare professional.",
        description="Medical disclaimer"
    )


class TransportationInfo(BaseModel):
    """Transportation guidance for the patient."""
    nearest_facility: Optional[str] = None
    distance: Optional[str] = None
    directions: Optional[str] = None
    estimated_travel_time: Optional[str] = None
    transportation_options: List[str] = Field(default_factory=list)
    what_to_bring: List[str] = Field(default_factory=list)


class PlanData(BaseModel):
    """
    Plan: Recommended actions and guidance.
    Separate outputs for patient (simple) and physician (formal).
    """
    # For the patient (spoken in their language)
    patient_guidance: str = Field(
        default="",
        description="Simple explanation for the patient"
    )
    patient_next_steps: List[str] = Field(
        default_factory=list,
        description="Clear action items for the patient"
    )
    self_care_instructions: List[str] = Field(
        default_factory=list,
        description="Home care recommendations if applicable"
    )

    # For the physician (formal medical report)
    physician_summary: str = Field(
        default="",
        description="Formal medical summary"
    )
    recommended_tests: List[str] = Field(
        default_factory=list,
        description="Suggested diagnostic tests"
    )
    recommended_referrals: List[str] = Field(
        default_factory=list,
        description="Specialist referrals if needed"
    )

    # Logistics
    transportation: Optional[TransportationInfo] = None
    follow_up: Optional[str] = Field(
        default=None,
        description="Follow-up recommendations"
    )
    what_to_expect: Optional[str] = Field(
        default=None,
        description="What patient should expect at the facility"
    )


class SOAPConsultation(BaseModel):
    """
    Complete SOAP consultation record.
    This is the main data structure for a consultation session.
    """
    id: str = Field(description="Unique consultation ID")
    patient_id: str = Field(description="Patient identifier")
    kiosk_id: Optional[str] = Field(default=None, description="Kiosk location ID")
    language: str = Field(default="en", description="Consultation language")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    current_stage: SOAPStage = Field(default=SOAPStage.GREETING)

    subjective: SubjectiveData = Field(default_factory=SubjectiveData)
    objective: ObjectiveData = Field(default_factory=ObjectiveData)
    assessment: AssessmentData = Field(default_factory=AssessmentData)
    plan: PlanData = Field(default_factory=PlanData)

    # Metadata
    consent_given: bool = Field(default=False)
    consent_timestamp: Optional[datetime] = None
    submitted_to_facility: bool = Field(default=False)
    facility_case_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConsultationSummary(BaseModel):
    """Brief summary of a consultation for listing."""
    id: str
    patient_id: str
    created_at: datetime
    chief_complaint: str
    urgency_level: UrgencyLevel
    current_stage: SOAPStage
    top_condition: Optional[str] = None
