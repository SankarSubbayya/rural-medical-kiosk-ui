"""
Test Data Router - Generate sample consultations for testing.
"""
from fastapi import APIRouter
from datetime import datetime
from uuid import uuid4

from ..models.soap import (
    SOAPConsultation,
    SubjectiveData,
    ObjectiveData,
    AssessmentData,
    PlanData,
    Symptom,
    CapturedImage,
    DifferentialDiagnosis,
    UrgencyLevel,
    SOAPStage
)
from .consultation import save_consultation


router = APIRouter(prefix="/test", tags=["test"])


@router.post("/create-sample-consultation")
async def create_sample_consultation():
    """
    Create a sample consultation with complete SOAP data for testing reports.
    """
    consultation_id = str(uuid4())

    # Create sample consultation
    consultation = SOAPConsultation(
        id=consultation_id,
        patient_id="test-patient-001",
        kiosk_id="test-kiosk-01",
        language="en",
        current_stage=SOAPStage.COMPLETED,
        created_at=datetime.utcnow(),

        # SUBJECTIVE
        subjective=SubjectiveData(
            chief_complaint="Red, itchy rash on back",
            symptoms=[
                Symptom(
                    name="Rash",
                    duration="3 weeks",
                    severity="moderate",
                    location="back"
                ),
                Symptom(
                    name="Itching",
                    duration="3 weeks",
                    severity="moderate",
                    location="back"
                )
            ],
            onset="3 weeks ago",
            duration="3 weeks",
            aggravating_factors=["heat", "sweating"],
            relieving_factors=["cool showers"],
            previous_treatments=["over-the-counter cream"],
            medical_history="No significant medical history",
            allergies=[]
        ),

        # OBJECTIVE
        objective=ObjectiveData(
            primary_body_location="back",
            images=[
                CapturedImage(
                    id=str(uuid4()),
                    body_location="upper back",
                    timestamp=datetime.utcnow(),
                    image_url="data:image/jpeg;base64,test"
                )
            ],
            visual_observations=[
                "Red, flat patches",
                "Slightly raised borders",
                "No blistering"
            ],
            lesion_characteristics={
                "color": "red",
                "pattern": "scattered patches",
                "size": "2-5 cm diameter",
                "texture": "slightly raised"
            },
            distribution_pattern="scattered on upper back"
        ),

        # ASSESSMENT
        assessment=AssessmentData(
            differential_diagnoses=[
                DifferentialDiagnosis(
                    condition="Contact Dermatitis",
                    icd_code="L25.9",
                    confidence=0.75,
                    is_critical=False,
                    supporting_evidence=[
                        "Red, itchy rash",
                        "Flat patches with raised borders",
                        "Recent onset",
                        "Improves with cool showers"
                    ],
                    contraindications=[]
                ),
                DifferentialDiagnosis(
                    condition="Eczema (Atopic Dermatitis)",
                    icd_code="L20.9",
                    confidence=0.60,
                    is_critical=False,
                    supporting_evidence=[
                        "Itchy rash",
                        "Chronic symptoms"
                    ],
                    contraindications=["No family history mentioned"]
                ),
                DifferentialDiagnosis(
                    condition="Fungal Infection (Tinea)",
                    icd_code="B35.9",
                    confidence=0.45,
                    is_critical=False,
                    supporting_evidence=[
                        "Raised borders",
                        "Persistent symptoms"
                    ],
                    contraindications=["No scaling mentioned"]
                )
            ],
            urgency_level=UrgencyLevel.ROUTINE,
            urgency_reasoning="Non-emergency skin condition that can be evaluated by a dermatologist at routine appointment",
            confidence_overall=0.70,
            requires_professional=True,
            rag_sources=[],
            disclaimer="This AI-generated assessment is for informational purposes only and does not constitute medical advice. Please consult with a licensed healthcare professional for proper diagnosis and treatment."
        ),

        # PLAN
        plan=PlanData(
            patient_guidance="You should see a dermatologist for proper evaluation. This appears to be a skin condition that requires professional assessment.",
            patient_next_steps=[
                "Schedule an appointment with a dermatologist within 1-2 weeks",
                "Bring this report to your appointment",
                "Take photos if the rash changes"
            ],
            self_care_instructions=[
                "Keep the affected area clean and dry",
                "Avoid scratching or picking at the rash",
                "Use fragrance-free moisturizer",
                "Wear loose, breathable clothing",
                "Avoid hot showers - use lukewarm water",
                "Identify and avoid potential irritants (new soaps, detergents, fabrics)"
            ],
            physician_summary="Patient presents with 3-week history of red, itchy rash on back. AI assessment suggests contact dermatitis (L25.9) with 75% confidence. Routine urgency.",
            recommended_tests=[
                "Visual examination by dermatologist",
                "Patch testing if contact dermatitis suspected",
                "KOH preparation if fungal infection suspected"
            ],
            recommended_referrals=[],
            follow_up="Follow up as recommended by dermatologist",
            what_to_expect="The dermatologist will examine the rash and may perform tests to determine the exact cause. Treatment may include topical medications."
        )
    )

    # Save to in-memory storage
    save_consultation(consultation)

    return {
        "status": "created",
        "consultation_id": consultation_id,
        "message": f"Sample consultation created. You can now test reports with ID: {consultation_id}"
    }
