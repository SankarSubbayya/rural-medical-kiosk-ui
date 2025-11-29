"""
MCP Tool: Speech Services

Handles speech-to-text (Whisper) and text-to-speech (gTTS).
"""

from typing import Optional, Any, Dict
from app.services.speech_service import SpeechService

# Lazy-initialized service instance
_speech_service: Optional[SpeechService] = None


def _get_service() -> SpeechService:
    """Get or create service instance (lazy initialization)."""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    return _speech_service


async def transcribe_audio(audio_base64: str, language: str = "auto") -> Dict[str, Any]:
    """Transcribe audio to text using Whisper."""
    try:
        # SpeechService.transcribe returns: (transcript, language, confidence)
        transcript, detected_language, confidence = await _get_service().transcribe(
            audio_base64=audio_base64,
            language=language if language != "auto" else None
        )

        return {
            "success": True,
            "operation": "transcribe",
            "transcript": transcript,
            "detected_language": detected_language,
            "confidence": confidence
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def synthesize_speech(text: str, language: str = "en") -> Dict[str, Any]:
    """Synthesize speech from text using gTTS."""
    try:
        # SpeechService.synthesize returns: base64 audio string
        audio_base64_result = await _get_service().synthesize(
            text=text,
            language=language
        )

        return {
            "success": True,
            "operation": "synthesize",
            "audio_base64": audio_base64_result,
            "audio_url": None,
            "duration_seconds": None
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point for speech services.

    Args:
        operation: One of "transcribe", "synthesize"
        **kwargs: Operation-specific parameters

    Returns:
        Dict with operation result
    """
    try:
        if operation == "transcribe":
            return await transcribe_audio(
                audio_base64=kwargs["audio_base64"],
                language=kwargs.get("language", "auto")
            )

        elif operation == "synthesize":
            return await synthesize_speech(
                text=kwargs["text"],
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
