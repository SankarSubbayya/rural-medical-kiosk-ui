"""
Models for image analysis and MedGemma responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BodyLocation(BaseModel):
    """Body location for the skin condition."""
    primary: str  # e.g., "arm", "face", "back"
    specific: Optional[str] = None  # e.g., "left forearm", "right cheek"
    laterality: Optional[str] = None  # "left", "right", "bilateral"


class LesionCharacteristics(BaseModel):
    """Visual characteristics of the skin lesion."""
    # ABCDE criteria for melanoma screening
    asymmetry: Optional[str] = None
    border: Optional[str] = None  # regular, irregular, notched
    color: List[str] = Field(default_factory=list)  # colors present
    diameter: Optional[str] = None  # estimated size
    evolution: Optional[str] = None  # changing?

    # Additional characteristics
    texture: Optional[str] = None  # smooth, scaly, rough, raised
    shape: Optional[str] = None  # round, oval, irregular
    distribution: Optional[str] = None  # single, clustered, scattered
    surface: Optional[str] = None  # dry, moist, crusted


class ImageAnalysisRequest(BaseModel):
    """Request to analyze a skin image."""
    consultation_id: str
    image_base64: str
    body_location: BodyLocation
    patient_description: Optional[str] = None  # What patient said about it
    symptoms: List[str] = Field(default_factory=list)


class SimilarCase(BaseModel):
    """A similar case from the SCIN database."""
    case_id: str
    condition: str
    icd_code: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    image_url: Optional[str] = None
    description: Optional[str] = None
    key_features: List[str] = Field(default_factory=list)


class ConditionPrediction(BaseModel):
    """A predicted condition from MedGemma."""
    condition: str
    icd_code: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    key_findings: List[str] = Field(default_factory=list)
    is_critical: bool = False
    urgency_level: str = "routine"  # emergency, urgent, routine, self_care


class ImageAnalysisResponse(BaseModel):
    """Response from the image analysis service."""
    consultation_id: str
    analysis_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Visual analysis
    lesion_characteristics: LesionCharacteristics
    visual_description: str
    quality_assessment: str  # good, acceptable, poor

    # Predictions from MedGemma
    predictions: List[ConditionPrediction] = Field(default_factory=list)
    top_prediction: Optional[ConditionPrediction] = None

    # RAG results from SCIN database
    similar_cases: List[SimilarCase] = Field(default_factory=list)

    # Safety flags
    critical_findings: List[str] = Field(default_factory=list)
    requires_urgent_attention: bool = False
    confidence_level: str = "moderate"  # low, moderate, high

    # Disclaimer
    disclaimer: str = Field(
        default="This analysis is for informational purposes only and is not a medical diagnosis. Please consult a healthcare professional for proper evaluation."
    )


class RAGQuery(BaseModel):
    """Query for the SCIN RAG system."""
    image_embedding: Optional[List[float]] = None
    text_query: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    body_location: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class RAGResult(BaseModel):
    """Result from RAG retrieval."""
    id: str
    condition: str
    icd_code: str
    description: str
    image_path: Optional[str] = None
    similarity_score: float
    metadata: dict = Field(default_factory=dict)


class SCINRecord(BaseModel):
    """A record from the SCIN database."""
    id: str
    condition: str
    icd_code: str
    description: str
    image_path: str
    body_location: Optional[str] = None
    age_group: Optional[str] = None
    skin_type: Optional[str] = None  # Fitzpatrick scale
    characteristics: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None


# MedGemma prompt templates
MEDGEMMA_SYSTEM_PROMPT = """You are a medical image analysis assistant specializing in dermatology.
Your role is to analyze skin condition images and provide structured observations.

IMPORTANT RULES:
1. You are NOT providing diagnoses - only observations and possibilities
2. Always recommend professional medical consultation
3. Flag any concerning features (ABCDE criteria for melanoma)
4. Be thorough but use accessible language
5. If image quality is poor, say so

Provide your analysis in the following structure:
1. Visual Description: What you observe
2. Key Features: Notable characteristics
3. Possible Conditions: What this could be (with reasoning)
4. Urgency Assessment: How soon medical attention is needed
5. Recommendations: Next steps"""

MEDGEMMA_ANALYSIS_PROMPT = """Analyze this skin condition image.

Patient Information:
- Body Location: {body_location}
- Patient Description: {patient_description}
- Reported Symptoms: {symptoms}

Please provide:
1. Detailed visual description of the lesion/condition
2. Key characteristics (size, shape, color, texture, borders)
3. Top 3 possible conditions with confidence levels and reasoning
4. ABCDE assessment if relevant (Asymmetry, Border, Color, Diameter, Evolution)
5. Urgency level (emergency/urgent/routine/self-care)
6. Whether this requires immediate professional attention

Remember: You are assisting with information gathering, not diagnosing."""
