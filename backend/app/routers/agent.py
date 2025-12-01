"""
Agent Router

FastAPI endpoints for SOAP Orchestrator Agent.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
# Use Google Gemini ADK agent with MedGemma
from agent.soap_agent import create_soap_agent, SOAPAgent

router = APIRouter(prefix="/agent", tags=["agent"])

# In-memory agent instances (keyed by consultation_id)
_agents: Dict[str, SOAPAgent] = {}


class AgentMessageRequest(BaseModel):
    """Request model for agent message."""
    message: str
    image_base64: Optional[str] = None
    consultation_id: Optional[str] = None
    patient_id: Optional[str] = None
    language: str = "en"


class AgentMessageResponse(BaseModel):
    """Response model for agent message."""
    success: bool
    message: str
    current_stage: str
    consultation_id: str
    language: str
    analysis: Optional[Dict[str, Any]] = None
    similar_cases: Optional[list] = None
    plan: Optional[Dict[str, Any]] = None
    requires_image: bool = False
    safety_triggered: bool = False
    consultation_complete: bool = False


@router.post("/message", response_model=AgentMessageResponse)
async def process_agent_message(request: AgentMessageRequest):
    """
    Process message through SOAP Orchestrator Agent.

    Creates new agent instance if needed, or retrieves existing one.
    """
    try:
        # Get or create agent
        if request.consultation_id and request.consultation_id in _agents:
            agent = _agents[request.consultation_id]
        else:
            # Use Gemini 2.0 Flash Exp for fast medical reasoning with MedGemma
            # Note: Gemini 3.0 not yet available, using latest working model
            # Pass consultation_id if provided to maintain session continuity
            agent = create_soap_agent(
                model="gemini-2.0-flash-exp",
                consultation_id=request.consultation_id
            )
            _agents[agent.state.consultation_id] = agent

        # Process message
        result = await agent.process_message(
            message=request.message,
            image_base64=request.image_base64,
            consultation_id=request.consultation_id,
            patient_id=request.patient_id,
            language=request.language
        )

        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Agent processing failed"))

        return AgentMessageResponse(
            success=True,
            message=result.get("message", ""),
            current_stage=agent.state.current_stage,
            consultation_id=agent.state.consultation_id,
            language=agent.state.language,
            analysis=result.get("analysis"),
            similar_cases=result.get("similar_cases"),
            plan=result.get("plan"),
            requires_image=result.get("requires_image", False),
            safety_triggered=result.get("safety_triggered", False),
            consultation_complete=result.get("consultation_complete", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consultation/{consultation_id}")
async def get_consultation_state(consultation_id: str):
    """Get current state of consultation."""
    if consultation_id not in _agents:
        raise HTTPException(status_code=404, detail="Consultation not found")

    agent = _agents[consultation_id]

    return {
        "consultation_id": agent.state.consultation_id,
        "patient_id": agent.state.patient_id,
        "language": agent.state.language,
        "current_stage": agent.state.current_stage,
        "consent_given": agent.state.consent_given,
        "extracted_symptoms": agent.state.extracted_symptoms,
        "image_captured": agent.state.image_captured,
        "message_history_count": len(agent.state.message_history),
        "created_at": agent.state.created_at.isoformat()
    }


@router.delete("/consultation/{consultation_id}")
async def end_consultation(consultation_id: str):
    """End consultation and cleanup agent."""
    if consultation_id in _agents:
        del _agents[consultation_id]
        return {"success": True, "message": "Consultation ended"}

    raise HTTPException(status_code=404, detail="Consultation not found")


@router.get("/health")
async def agent_health_check():
    """Health check for agent system."""
    return {
        "status": "healthy",
        "agent_type": "SOAP Orchestrator",
        "model": "gemini-2.5-flash-001",
        "active_consultations": len(_agents),
        "tools_count": 7
    }
