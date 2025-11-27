"""
Dermatology Kiosk Backend - FastAPI Application

Main entry point for the backend API server.

Architecture:
- GPT-4o for conversational AI and SOAP flow management
- MedGemma for dermatological image analysis
- SCIN database with ChromaDB for RAG retrieval
- Whisper for speech-to-text, gTTS for text-to-speech
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import (
    chat_router,
    analysis_router,
    speech_router,
    report_router,
    consultation_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup: Initialize services, load models
    Shutdown: Clean up resources
    """
    # Startup
    settings = get_settings()
    print(f"Starting Dermatology Kiosk Backend...")
    print(f"Debug mode: {settings.debug}")
    print(f"Supported languages: {settings.languages}")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Dermatology Kiosk API",
    description="""
    Backend API for the Rural Medical AI Kiosk.

    ## Overview

    This API provides:
    - **SOAP Consultation Flow**: Structured medical consultation management
    - **Conversational AI**: GPT-4o powered chat for patient interaction
    - **Image Analysis**: MedGemma for dermatological analysis
    - **RAG Retrieval**: SCIN database for similar case finding
    - **Speech Services**: Multi-language voice support

    ## Important Notes

    ⚠️ **This system is NOT a diagnostic tool**. It provides guidance and case
    history preparation only. All findings are suggestions that require
    professional medical verification.

    ## SOAP Framework

    The consultation follows the medical SOAP framework:
    - **S**ubjective: Patient's narrative and symptoms
    - **O**bjective: Images and observable findings
    - **A**ssessment: Possible conditions with ICD codes
    - **P**lan: Guidance and next steps
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",
        "https://*.vercel.app",   # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(consultation_router)
app.include_router(chat_router)
app.include_router(analysis_router)
app.include_router(speech_router)
app.include_router(report_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Dermatology Kiosk API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "consultation": "/consultation - SOAP consultation management",
            "chat": "/chat - Conversational AI (GPT-4o)",
            "analyze": "/analyze - Image analysis (MedGemma)",
            "speech": "/speech - Voice services (Whisper/TTS)",
            "report": "/report - Report generation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
