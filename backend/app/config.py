"""
Configuration settings for the Dermatology Kiosk Backend.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Ollama Configuration (Local LLM)
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_chat_model: str = Field(default="gpt-oss:20b", env="OLLAMA_CHAT_MODEL")
    ollama_medgemma_model: str = Field(default="amsaravi/medgemma-4b-it:q8", env="OLLAMA_MEDGEMMA_MODEL")
    ollama_vision_model: str = Field(default="llava:latest", env="OLLAMA_VISION_MODEL")

    # HuggingFace Configuration (for SigLIP-2 embeddings)
    huggingface_token: str = Field(default="", env="HUGGINGFACE_TOKEN")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./kiosk.db",
        env="DATABASE_URL"
    )

    # Qdrant Vector Store Configuration
    qdrant_embedded: bool = Field(default=True, env="QDRANT_EMBEDDED")
    qdrant_path: str = Field(default="./qdrant_data", env="QDRANT_PATH")
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_collection_name: str = Field(default="scin_dermatology", env="QDRANT_COLLECTION")

    # SCIN Data Directory
    scin_data_dir: str = Field(default="./scin_data", env="SCIN_DATA_DIR")

    # Speech Configuration
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")

    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")

    # Healthcare Facility
    facility_api_url: str = Field(default="", env="FACILITY_API_URL")
    facility_api_key: str = Field(default="", env="FACILITY_API_KEY")

    # Supported Languages
    supported_languages: str = Field(default="en,hi,ta,te,bn", env="SUPPORTED_LANGUAGES")

    @property
    def languages(self) -> List[str]:
        """Get list of supported language codes."""
        return self.supported_languages.split(",")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Language display names
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "bn": "Bengali (বাংলা)",
    "mr": "Marathi (मराठी)",
    "gu": "Gujarati (ગુજરાતી)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
}

# ICD-10 codes for common dermatological conditions
ICD_CODES = {
    "eczema": "L30.9",
    "psoriasis": "L40.9",
    "acne": "L70.9",
    "contact_dermatitis": "L25.9",
    "urticaria": "L50.9",
    "fungal_infection": "B35.9",
    "bacterial_infection": "L08.9",
    "viral_rash": "B09",
    "melanoma": "C43.9",
    "basal_cell_carcinoma": "C44.91",
    "squamous_cell_carcinoma": "C44.92",
    "vitiligo": "L80",
    "rosacea": "L71.9",
    "seborrheic_dermatitis": "L21.9",
    "impetigo": "L01.0",
    "cellulitis": "L03.90",
    "herpes_simplex": "B00.9",
    "herpes_zoster": "B02.9",
    "scabies": "B86",
    "tinea": "B35.9",
}

# Critical conditions requiring immediate escalation
CRITICAL_CONDITIONS = [
    "melanoma",
    "squamous_cell_carcinoma",
    "basal_cell_carcinoma",
    "cellulitis",
    "necrotizing_fasciitis",
    "stevens_johnson_syndrome",
    "toxic_epidermal_necrolysis",
    "meningococcal_rash",
    "anaphylaxis",
    "severe_burns",
    "pemphigus",
    "drug_reaction",
]
