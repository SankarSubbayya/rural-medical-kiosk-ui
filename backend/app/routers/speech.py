"""
Speech Router - Speech-to-text and text-to-speech endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.speech_service import SpeechService, LanguageService


router = APIRouter(prefix="/speech", tags=["speech"])

# Service instances
_speech_service = SpeechService()
_language_service = LanguageService()


class TranscribeRequest(BaseModel):
    """Request to transcribe audio."""
    audio_base64: str
    language: str | None = None  # Auto-detect if not provided


class TranscribeResponse(BaseModel):
    """Transcription result."""
    text: str
    language: str
    confidence: float


class SynthesizeRequest(BaseModel):
    """Request to synthesize speech."""
    text: str
    language: str = "en"


class SynthesizeResponse(BaseModel):
    """Speech synthesis result."""
    audio_base64: str
    language: str
    duration_estimate: float | None = None


class DetectLanguageRequest(BaseModel):
    """Request to detect language."""
    audio_base64: str | None = None
    text: str | None = None


class TranslateRequest(BaseModel):
    """Request to translate text."""
    text: str
    source_language: str
    target_language: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """
    Transcribe audio to text using Whisper.

    Supports multiple languages with auto-detection.
    """
    try:
        text, language, confidence = await _speech_service.transcribe(
            request.audio_base64,
            request.language
        )

        return TranscribeResponse(
            text=text,
            language=language,
            confidence=confidence
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(request: SynthesizeRequest):
    """
    Convert text to speech.

    Supports multiple languages.
    """
    # Validate language
    if not await _speech_service.validate_language(request.language):
        raise HTTPException(
            status_code=400,
            detail=f"Language '{request.language}' is not supported"
        )

    try:
        audio_base64 = await _speech_service.synthesize(
            request.text,
            request.language
        )

        # Estimate duration (rough: ~150 words per minute)
        word_count = len(request.text.split())
        duration_estimate = word_count / 2.5  # seconds

        return SynthesizeResponse(
            audio_base64=audio_base64,
            language=request.language,
            duration_estimate=duration_estimate
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-language")
async def detect_language(request: DetectLanguageRequest):
    """
    Detect the language of audio or text.
    """
    if request.audio_base64:
        try:
            language = await _speech_service.detect_language(request.audio_base64)
            return {"language": language, "source": "audio"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif request.text:
        try:
            language = await _language_service.detect_text_language(request.text)
            return {"language": language, "source": "text"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(
            status_code=400,
            detail="Either audio_base64 or text must be provided"
        )


@router.post("/translate")
async def translate_text(request: TranslateRequest):
    """
    Translate text between languages.
    """
    try:
        translated = await _language_service.translate(
            request.text,
            request.source_language,
            request.target_language
        )

        return {
            "original": request.text,
            "translated": translated,
            "source_language": request.source_language,
            "target_language": request.target_language
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages.
    """
    return {
        "languages": _speech_service.get_supported_languages()
    }
