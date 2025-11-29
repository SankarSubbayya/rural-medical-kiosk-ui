"""
MCP Server for Rural Medical AI Kiosk.

Provides 7 MCP tools for the SOAP Orchestrator Agent:
1. consultation_tool - Consultation management
2. medical_tool - Symptom extraction & common sense checks
3. medgemma_tool - Medical image analysis
4. rag_tool - Case-based reasoning
5. safety_tool - Medical guardrails
6. siglip_rag_tool - SigLIP embedding-based RAG
7. speech_tool - Speech-to-text and text-to-speech
"""

from .tools import (
    consultation_tool,
    medical_tool,
    medgemma_tool,
    rag_tool,
    safety_tool,
    siglip_rag_tool,
    speech_tool,
)

__all__ = [
    "consultation_tool",
    "medical_tool",
    "medgemma_tool",
    "rag_tool",
    "safety_tool",
    "siglip_rag_tool",
    "speech_tool",
]
