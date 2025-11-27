"""
Analysis Service - Handles medical image analysis using MedGemma via Ollama.

This service is specifically for dermatological image analysis and
condition suggestion. It does NOT diagnose - only provides possibilities.
"""
import base64
import uuid
from typing import Optional, List
from datetime import datetime
import ollama
from PIL import Image
import io

from ..config import get_settings, ICD_CODES, CRITICAL_CONDITIONS
from ..models.analysis import (
    ImageAnalysisRequest, ImageAnalysisResponse,
    ConditionPrediction, LesionCharacteristics, SimilarCase,
    MEDGEMMA_SYSTEM_PROMPT, MEDGEMMA_ANALYSIS_PROMPT
)
from ..models.soap import DifferentialDiagnosis, UrgencyLevel


class AnalysisService:
    """
    Medical image analysis service using MedGemma via Ollama.

    Uses amsaravi/medgemma-4b-it:q8 (or configured model) for:
    - Analyzing skin condition images
    - Extracting visual characteristics
    - Suggesting possible conditions (NOT diagnose)
    - Flagging critical conditions requiring urgent attention
    """

    def __init__(self, rag_service=None):
        self.settings = get_settings()
        self.client = ollama.AsyncClient(host=self.settings.ollama_base_url)
        self.medgemma_model = self.settings.ollama_medgemma_model  # amsaravi/medgemma-4b-it:q8
        self.vision_model = self.settings.ollama_vision_model  # llava (fallback)
        self.rag_service = rag_service

    async def analyze_image(
        self,
        request: ImageAnalysisRequest
    ) -> ImageAnalysisResponse:
        """
        Analyze a skin condition image.

        Args:
            request: Analysis request with image and context

        Returns:
            Structured analysis with possible conditions
        """
        analysis_id = str(uuid.uuid4())

        # Decode image
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data))

        # Check image quality
        quality = self._assess_image_quality(image)

        # Build analysis prompt
        prompt = MEDGEMMA_ANALYSIS_PROMPT.format(
            body_location=f"{request.body_location.primary} ({request.body_location.specific or 'unspecified'})",
            patient_description=request.patient_description or "Not provided",
            symptoms=", ".join(request.symptoms) if request.symptoms else "Not specified"
        )

        # Call MedGemma for analysis
        try:
            response = await self._call_medgemma(image, prompt)
            analysis_result = self._parse_analysis_response(response)
        except Exception as e:
            # Fallback analysis if model fails
            print(f"MedGemma analysis error: {e}")
            analysis_result = self._get_fallback_analysis(str(e))

        # Get similar cases from RAG if available
        similar_cases = []
        if self.rag_service:
            similar_cases = await self.rag_service.find_similar_cases(
                image_base64=request.image_base64,
                symptoms=request.symptoms,
                body_location=request.body_location.primary
            )

        # Build response
        return ImageAnalysisResponse(
            consultation_id=request.consultation_id,
            analysis_id=analysis_id,
            lesion_characteristics=analysis_result["characteristics"],
            visual_description=analysis_result["description"],
            quality_assessment=quality,
            predictions=analysis_result["predictions"],
            top_prediction=analysis_result["predictions"][0] if analysis_result["predictions"] else None,
            similar_cases=similar_cases,
            critical_findings=analysis_result.get("critical_findings", []),
            requires_urgent_attention=analysis_result.get("requires_urgent", False),
            confidence_level=analysis_result.get("confidence", "moderate")
        )

    async def _call_medgemma(self, image: Image.Image, prompt: str) -> str:
        """
        Call MedGemma model via Ollama with image and prompt.

        Uses amsaravi/medgemma-4b-it:q8 for medical image analysis.
        Falls back to llava if MedGemma fails.
        """
        # Convert PIL Image to base64
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()

        # Full prompt with system context
        full_prompt = f"{MEDGEMMA_SYSTEM_PROMPT}\n\n{prompt}"

        try:
            # Try MedGemma first
            response = await self.client.chat(
                model=self.medgemma_model,
                messages=[{
                    'role': 'user',
                    'content': full_prompt,
                    'images': [img_base64]
                }],
                options={"temperature": 0.3}
            )
            return response['message']['content']

        except Exception as e:
            print(f"MedGemma failed ({e}), falling back to {self.vision_model}")
            # Fallback to general vision model (llava)
            response = await self.client.chat(
                model=self.vision_model,
                messages=[{
                    'role': 'user',
                    'content': full_prompt,
                    'images': [img_base64]
                }],
                options={"temperature": 0.3}
            )
            return response['message']['content']

    def _parse_analysis_response(self, response: str) -> dict:
        """Parse the analysis response from MedGemma."""
        # Initialize result structure
        result = {
            "characteristics": LesionCharacteristics(),
            "description": "",
            "predictions": [],
            "critical_findings": [],
            "requires_urgent": False,
            "confidence": "moderate"
        }

        # Parse the response text
        lines = response.strip().split("\n")
        current_section = None
        description_lines = []
        predictions_text = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if "visual description" in line.lower() or "description:" in line.lower():
                current_section = "description"
                continue
            elif "key features" in line.lower() or "characteristics" in line.lower():
                current_section = "characteristics"
                continue
            elif "possible conditions" in line.lower() or "conditions:" in line.lower():
                current_section = "predictions"
                continue
            elif "urgency" in line.lower():
                current_section = "urgency"
                continue
            elif "abcde" in line.lower():
                current_section = "abcde"
                continue

            # Collect content based on section
            if current_section == "description":
                description_lines.append(line)
            elif current_section == "predictions":
                predictions_text.append(line)
            elif current_section == "urgency":
                if "emergency" in line.lower():
                    result["requires_urgent"] = True
                    result["confidence"] = "high"
                elif "urgent" in line.lower():
                    result["confidence"] = "high"

        result["description"] = " ".join(description_lines)

        # Parse predictions
        result["predictions"] = self._parse_predictions(predictions_text, response)

        # Check for critical conditions
        for pred in result["predictions"]:
            if pred.is_critical:
                result["critical_findings"].append(f"Possible {pred.condition} detected")
                result["requires_urgent"] = True

        return result

    def _parse_predictions(
        self,
        predictions_text: List[str],
        full_response: str
    ) -> List[ConditionPrediction]:
        """Parse condition predictions from the response."""
        predictions = []

        # Common dermatological conditions to look for
        condition_keywords = {
            "eczema": ("eczema", "L30.9"),
            "psoriasis": ("psoriasis", "L40.9"),
            "acne": ("acne", "L70.9"),
            "dermatitis": ("contact dermatitis", "L25.9"),
            "fungal": ("fungal infection", "B35.9"),
            "ringworm": ("tinea", "B35.9"),
            "hives": ("urticaria", "L50.9"),
            "melanoma": ("melanoma", "C43.9"),
            "basal cell": ("basal cell carcinoma", "C44.91"),
            "squamous": ("squamous cell carcinoma", "C44.92"),
            "rosacea": ("rosacea", "L71.9"),
            "vitiligo": ("vitiligo", "L80"),
            "impetigo": ("impetigo", "L01.0"),
            "cellulitis": ("cellulitis", "L03.90"),
            "herpes": ("herpes simplex", "B00.9"),
            "shingles": ("herpes zoster", "B02.9"),
            "scabies": ("scabies", "B86"),
        }

        response_lower = full_response.lower()

        # Find mentioned conditions
        found_conditions = []
        for keyword, (condition, icd) in condition_keywords.items():
            if keyword in response_lower:
                found_conditions.append((condition, icd, keyword))

        # Create predictions with estimated confidence
        for i, (condition, icd, keyword) in enumerate(found_conditions[:5]):
            # Estimate confidence based on position and mention frequency
            base_confidence = 0.8 - (i * 0.15)
            mention_count = response_lower.count(keyword)
            confidence = min(base_confidence + (mention_count * 0.05), 0.95)

            is_critical = condition.lower().replace(" ", "_") in CRITICAL_CONDITIONS

            # Determine urgency
            urgency = "routine"
            if is_critical:
                urgency = "urgent"
            if "melanoma" in condition.lower() or "carcinoma" in condition.lower():
                urgency = "emergency"

            predictions.append(ConditionPrediction(
                condition=condition,
                icd_code=icd,
                confidence=round(confidence, 2),
                reasoning=f"Visual features consistent with {condition}",
                key_findings=[],
                is_critical=is_critical,
                urgency_level=urgency
            ))

        # If no specific conditions found, add generic response
        if not predictions:
            predictions.append(ConditionPrediction(
                condition="Unspecified skin condition",
                icd_code="L98.9",
                confidence=0.3,
                reasoning="Unable to determine specific condition. Professional evaluation recommended.",
                is_critical=False,
                urgency_level="routine"
            ))

        return predictions

    def _assess_image_quality(self, image: Image.Image) -> str:
        """Assess the quality of the captured image."""
        width, height = image.size

        # Check resolution
        if width < 200 or height < 200:
            return "poor"

        # Check if image is too dark or too bright
        if image.mode == "RGB":
            pixels = list(image.getdata())
            avg_brightness = sum(sum(p) for p in pixels) / (len(pixels) * 3)

            if avg_brightness < 30:
                return "poor"  # Too dark
            if avg_brightness > 240:
                return "poor"  # Too bright

        if width >= 500 and height >= 500:
            return "good"

        return "acceptable"

    def _get_fallback_analysis(self, error: str) -> dict:
        """Return fallback analysis when model fails."""
        return {
            "characteristics": LesionCharacteristics(),
            "description": "Unable to perform detailed analysis. Please consult a healthcare professional for proper evaluation.",
            "predictions": [
                ConditionPrediction(
                    condition="Analysis unavailable",
                    icd_code="R21",
                    confidence=0.0,
                    reasoning=f"Technical error occurred: {error}",
                    is_critical=False,
                    urgency_level="routine"
                )
            ],
            "critical_findings": [],
            "requires_urgent": False,
            "confidence": "low"
        }

    def convert_to_differential_diagnoses(
        self,
        predictions: List[ConditionPrediction],
        similar_cases: List[SimilarCase]
    ) -> List[DifferentialDiagnosis]:
        """Convert analysis predictions to SOAP differential diagnoses."""
        diagnoses = []

        for pred in predictions:
            # Find supporting evidence from similar cases
            supporting = []
            for case in similar_cases:
                if case.condition.lower() == pred.condition.lower():
                    supporting.extend(case.key_features)

            diagnoses.append(DifferentialDiagnosis(
                condition=pred.condition,
                icd_code=pred.icd_code,
                confidence=pred.confidence,
                supporting_evidence=pred.key_findings + supporting,
                is_critical=pred.is_critical
            ))

        return diagnoses

    def determine_urgency(
        self,
        predictions: List[ConditionPrediction]
    ) -> tuple[UrgencyLevel, str]:
        """Determine overall urgency level from predictions."""
        if not predictions:
            return UrgencyLevel.ROUTINE, "No specific concerns identified."

        # Check for critical conditions
        for pred in predictions:
            if pred.is_critical:
                return UrgencyLevel.EMERGENCY, f"Possible {pred.condition} requires immediate professional evaluation."

            if pred.urgency_level == "emergency":
                return UrgencyLevel.EMERGENCY, f"{pred.condition} suspected - seek immediate medical attention."

            if pred.urgency_level == "urgent":
                return UrgencyLevel.URGENT, f"{pred.condition} suspected - please see a doctor within 24-48 hours."

        # Check confidence levels
        top_pred = predictions[0]
        if top_pred.confidence > 0.7:
            return UrgencyLevel.ROUTINE, f"Likely {top_pred.condition}. Schedule an appointment for professional confirmation."

        return UrgencyLevel.ROUTINE, "Professional evaluation recommended for accurate diagnosis."
