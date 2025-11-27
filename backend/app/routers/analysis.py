"""
Analysis Router - Image analysis endpoints using MedGemma + RAG.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.analysis import (
    ImageAnalysisRequest, ImageAnalysisResponse, BodyLocation
)
from ..models.soap import CapturedImage, ObjectiveData
from ..services.analysis_service import AnalysisService
from ..services.rag_service import RAGService
from .consultation import get_consultation_by_id, save_consultation

from datetime import datetime
import uuid


router = APIRouter(prefix="/analyze", tags=["analysis"])

# Service instances
_rag_service = RAGService()
_analysis_service = AnalysisService(rag_service=_rag_service)


class QuickAnalyzeRequest(BaseModel):
    """Simplified analysis request."""
    consultation_id: str
    image_base64: str
    body_location: str
    body_location_specific: str | None = None


@router.post("/image", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze a skin condition image using MedGemma.

    This endpoint:
    1. Validates image quality
    2. Extracts visual features
    3. Queries SCIN database for similar cases
    4. Generates possible conditions with ICD codes
    5. Determines urgency level
    """
    consultation = get_consultation_by_id(request.consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    try:
        # Perform analysis
        result = await _analysis_service.analyze_image(request)

        # Update consultation objective data
        captured_image = CapturedImage(
            id=result.analysis_id,
            timestamp=datetime.utcnow(),
            body_location=request.body_location.primary,
            image_url=f"/images/{result.analysis_id}.png",  # Would be actual storage URL
            consent_given=True,
            consent_timestamp=datetime.utcnow()
        )

        consultation.objective.images.append(captured_image)
        consultation.objective.primary_body_location = request.body_location.primary
        consultation.objective.visual_observations = [result.visual_description]

        # Update assessment with analysis results
        if result.predictions:
            consultation.assessment.possible_conditions = \
                _analysis_service.convert_to_differential_diagnoses(
                    result.predictions,
                    result.similar_cases
                )

            urgency, reasoning = _analysis_service.determine_urgency(result.predictions)
            consultation.assessment.urgency_level = urgency
            consultation.assessment.urgency_reasoning = reasoning

        consultation.assessment.confidence_overall = \
            result.predictions[0].confidence if result.predictions else 0.0

        # Save consultation
        save_consultation(consultation)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick", response_model=ImageAnalysisResponse)
async def quick_analyze(request: QuickAnalyzeRequest):
    """
    Quick analysis with simplified input.

    Convenience endpoint for frontends.
    """
    full_request = ImageAnalysisRequest(
        consultation_id=request.consultation_id,
        image_base64=request.image_base64,
        body_location=BodyLocation(
            primary=request.body_location,
            specific=request.body_location_specific
        )
    )

    return await analyze_image(full_request)


@router.get("/similar")
async def find_similar_cases(
    symptoms: str = "",
    body_location: str = "",
    top_k: int = 5
):
    """
    Find similar cases from the SCIN database.

    This is a text-only search without image.
    """
    symptom_list = [s.strip() for s in symptoms.split(",") if s.strip()]

    cases = await _rag_service.find_similar_cases(
        symptoms=symptom_list,
        body_location=body_location if body_location else None,
        top_k=top_k
    )

    return {
        "query": {
            "symptoms": symptom_list,
            "body_location": body_location
        },
        "results": cases
    }


@router.get("/stats")
async def get_rag_stats():
    """
    Get statistics about the RAG database.
    """
    return _rag_service.get_collection_stats()


@router.post("/ingest")
async def ingest_scin_data(data_dir: str):
    """
    Ingest SCIN database from directory.

    This is an admin endpoint for loading the dermatology database.
    """
    try:
        count = await _rag_service.ingest_scin_database(data_dir)
        return {
            "status": "success",
            "records_ingested": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
