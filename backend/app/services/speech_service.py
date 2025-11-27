"""
Speech Service - Handles speech-to-text and text-to-speech.

Supports multiple languages for the voice-first interface.
Uses Whisper for STT and gTTS for TTS.
Translation uses Ollama for local processing.
"""
import base64
import tempfile
import os
from typing import Optional, Tuple
from pathlib import Path
import io
import ollama

from ..config import get_settings, LANGUAGE_NAMES


class SpeechService:
    """
    Speech processing service for voice-first interface.

    Features:
    - Speech-to-text using local OpenAI Whisper
    - Text-to-speech using gTTS
    - Language detection
    - Multi-language support (5+ languages)
    """

    def __init__(self):
        self.settings = get_settings()
        self._whisper_model = None

    def _load_whisper(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            try:
                import whisper
                self._whisper_model = whisper.load_model(self.settings.whisper_model)
            except ImportError:
                raise RuntimeError(
                    "Whisper not installed. Install with: pip install openai-whisper"
                )

    async def transcribe(
        self,
        audio_base64: str,
        language: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """
        Transcribe audio to text.

        Args:
            audio_base64: Base64 encoded audio (WAV, MP3, etc.)
            language: Optional language code (auto-detect if not provided)

        Returns:
            Tuple of (transcript, detected_language, confidence)
        """
        self._load_whisper()

        # Decode audio
        audio_data = base64.b64decode(audio_base64)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            return await self._transcribe_local(temp_path, language)
        finally:
            # Clean up temp file
            os.unlink(temp_path)

    async def _transcribe_local(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Transcribe using local Whisper model."""
        options = {}
        if language:
            options["language"] = language

        result = self._whisper_model.transcribe(audio_path, **options)

        return (
            result["text"].strip(),
            result.get("language", language or "en"),
            0.9  # Whisper doesn't provide confidence scores directly
        )

    async def detect_language(self, audio_base64: str) -> str:
        """
        Detect the language of spoken audio.

        Args:
            audio_base64: Base64 encoded audio

        Returns:
            Detected language code
        """
        self._load_whisper()

        # Decode audio
        audio_data = base64.b64decode(audio_base64)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            import whisper
            audio = whisper.load_audio(temp_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self._whisper_model.device)
            _, probs = self._whisper_model.detect_language(mel)
            return max(probs, key=probs.get)
        finally:
            os.unlink(temp_path)

    async def synthesize(
        self,
        text: str,
        language: str = "en"
    ) -> str:
        """
        Convert text to speech.

        Args:
            text: Text to synthesize
            language: Language code

        Returns:
            Base64 encoded audio (MP3)
        """
        try:
            # Use gTTS (free, supports many languages)
            return await self._synthesize_gtts(text, language)
        except Exception as e:
            print(f"gTTS failed: {e}, trying fallback...")
            # Fallback to basic TTS
            return await self._synthesize_fallback(text, language)

    async def _synthesize_gtts(self, text: str, language: str) -> str:
        """Synthesize using gTTS (Google Text-to-Speech)."""
        from gtts import gTTS

        # Map language codes to gTTS codes
        lang_map = {
            "en": "en",
            "hi": "hi",
            "ta": "ta",
            "te": "te",
            "bn": "bn",
            "mr": "mr",
            "gu": "gu",
            "kn": "kn",
            "ml": "ml",
            "pa": "pa",
        }
        gtts_lang = lang_map.get(language, "en")

        # Generate speech
        tts = gTTS(text=text, lang=gtts_lang, slow=False)

        # Save to bytes
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        # Encode to base64
        return base64.b64encode(audio_buffer.read()).decode()

    async def _synthesize_fallback(self, text: str, language: str) -> str:
        """Fallback TTS using pyttsx3 or similar."""
        # This is a placeholder - in production, use a robust TTS service
        # For now, return empty audio
        print(f"TTS fallback called for language: {language}")
        return ""

    async def synthesize_to_file(
        self,
        text: str,
        language: str,
        output_path: str
    ) -> str:
        """
        Synthesize text to an audio file.

        Args:
            text: Text to synthesize
            language: Language code
            output_path: Path to save the audio file

        Returns:
            Path to the saved file
        """
        audio_base64 = await self.synthesize(text, language)
        audio_data = base64.b64decode(audio_base64)

        with open(output_path, "wb") as f:
            f.write(audio_data)

        return output_path

    def get_supported_languages(self) -> dict:
        """Get dictionary of supported languages."""
        return {
            code: LANGUAGE_NAMES.get(code, code)
            for code in self.settings.languages
        }

    async def validate_language(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in self.settings.languages


class LanguageService:
    """
    Language detection and translation support.
    Uses Ollama for translation.
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = ollama.AsyncClient(host=self.settings.ollama_base_url)
        self.model = self.settings.ollama_chat_model

    async def detect_text_language(self, text: str) -> str:
        """
        Detect the language of text.

        Uses simple heuristics and/or ML model.
        """
        try:
            from langdetect import detect
            return detect(text)
        except ImportError:
            # Fallback to simple heuristics
            return self._detect_by_script(text)

    def _detect_by_script(self, text: str) -> str:
        """Detect language by Unicode script."""
        # Count characters in different scripts
        scripts = {
            "devanagari": 0,  # Hindi, Marathi
            "tamil": 0,
            "telugu": 0,
            "bengali": 0,
            "gujarati": 0,
            "kannada": 0,
            "malayalam": 0,
            "gurmukhi": 0,  # Punjabi
            "latin": 0,
        }

        for char in text:
            code = ord(char)
            if 0x0900 <= code <= 0x097F:
                scripts["devanagari"] += 1
            elif 0x0B80 <= code <= 0x0BFF:
                scripts["tamil"] += 1
            elif 0x0C00 <= code <= 0x0C7F:
                scripts["telugu"] += 1
            elif 0x0980 <= code <= 0x09FF:
                scripts["bengali"] += 1
            elif 0x0A80 <= code <= 0x0AFF:
                scripts["gujarati"] += 1
            elif 0x0C80 <= code <= 0x0CFF:
                scripts["kannada"] += 1
            elif 0x0D00 <= code <= 0x0D7F:
                scripts["malayalam"] += 1
            elif 0x0A00 <= code <= 0x0A7F:
                scripts["gurmukhi"] += 1
            elif (0x0041 <= code <= 0x007A) or (0x00C0 <= code <= 0x00FF):
                scripts["latin"] += 1

        # Map script to language
        script_to_lang = {
            "devanagari": "hi",
            "tamil": "ta",
            "telugu": "te",
            "bengali": "bn",
            "gujarati": "gu",
            "kannada": "kn",
            "malayalam": "ml",
            "gurmukhi": "pa",
            "latin": "en",
        }

        # Return language with most characters
        max_script = max(scripts, key=scripts.get)
        if scripts[max_script] > 0:
            return script_to_lang.get(max_script, "en")

        return "en"

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text between languages using Ollama.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text
        """
        if source_lang == target_lang:
            return text

        source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)

        prompt = f"""Translate the following text from {source_name} to {target_name}.
Maintain the meaning and tone. Only output the translation, nothing else.

Text to translate:
{text}"""

        try:
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate accurately and naturally."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={"temperature": 0.3}
            )
            return response['message']['content'].strip()

        except Exception as e:
            print(f"Translation error: {e}")
            # Return original text if translation fails
            return text
