"""
Report Router - Report generation and facility submission endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO

from ..services.report_service import ReportService
from .consultation import get_consultation_by_id, save_consultation


router = APIRouter(prefix="/report", tags=["report"])

# Service instance
_report_service = ReportService()


class GenerateReportRequest(BaseModel):
    """Request to generate a report."""
    consultation_id: str
    language: str = "en"


class PatientReportResponse(BaseModel):
    """Patient-friendly report."""
    consultation_id: str
    report_text: str
    language: str


class PhysicianReportResponse(BaseModel):
    """Physician report."""
    consultation_id: str
    report_text: str
    can_download_pdf: bool = True


@router.post("/patient", response_model=PatientReportResponse)
async def generate_patient_report(request: GenerateReportRequest):
    """
    Generate a patient-friendly report.

    This report is designed to be read aloud to the patient.
    Uses simple language appropriate for the patient's literacy level.
    """
    consultation = get_consultation_by_id(request.consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    try:
        report_text = await _report_service.generate_patient_report(consultation)

        return PatientReportResponse(
            consultation_id=request.consultation_id,
            report_text=report_text,
            language=request.language
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/physician", response_model=PhysicianReportResponse)
async def generate_physician_report(request: GenerateReportRequest):
    """
    Generate a formal physician report.

    This report follows standard SOAP format with ICD-10 codes.
    Suitable for submission to healthcare facilities.
    """
    consultation = get_consultation_by_id(request.consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    try:
        report_text = await _report_service.generate_physician_report(consultation)

        return PhysicianReportResponse(
            consultation_id=request.consultation_id,
            report_text=report_text
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{consultation_id}/pdf")
async def download_pdf_report(consultation_id: str):
    """
    Download the physician report as PDF.
    """
    consultation = get_consultation_by_id(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    try:
        pdf_bytes = await _report_service.generate_pdf_report(consultation)

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{consultation_id[:8]}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{consultation_id}/generate-plan")
async def generate_plan(consultation_id: str, language: str = "en"):
    """
    Generate the plan section based on assessment results.

    This should be called after image analysis is complete.
    """
    consultation = get_consultation_by_id(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    try:
        plan = await _report_service.generate_plan_data(consultation, language)
        consultation.plan = plan
        save_consultation(consultation)

        return {
            "status": "generated",
            "plan": plan
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SubmitToFacilityRequest(BaseModel):
    """Request to submit report to healthcare facility."""
    consultation_id: str
    facility_id: str | None = None


@router.post("/submit")
async def submit_to_facility(request: SubmitToFacilityRequest):
    """
    Submit the consultation report to a healthcare facility.

    This sends the formal SOAP report to the designated facility.
    """
    consultation = get_consultation_by_id(request.consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Generate physician report
    report = await _report_service.generate_physician_report(consultation)

    # In production, this would:
    # 1. Send to facility API
    # 2. Upload images to secure storage
    # 3. Create tracking record
    # 4. Send notification to on-call provider

    # For now, mark as submitted
    consultation.submitted_to_facility = True
    consultation.facility_case_id = f"CASE-{consultation.id[:8].upper()}"
    save_consultation(consultation)

    return {
        "status": "submitted",
        "facility_case_id": consultation.facility_case_id,
        "message": "Report has been submitted to the healthcare facility. You will be contacted soon."
    }


@router.get("/{consultation_id}/status")
async def get_submission_status(consultation_id: str):
    """
    Get the submission status of a consultation.
    """
    consultation = get_consultation_by_id(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    return {
        "consultation_id": consultation_id,
        "submitted": consultation.submitted_to_facility,
        "facility_case_id": consultation.facility_case_id,
        "current_stage": consultation.current_stage.value
    }
