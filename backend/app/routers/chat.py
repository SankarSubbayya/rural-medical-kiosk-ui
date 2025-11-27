"""
Chat Router - Conversational AI endpoints using GPT-4o.
"""
from fastapi import APIRouter, HTTPException

from ..models.chat import ChatRequest, ChatResponse
from ..services.chat_service import ChatService
from .consultation import get_consultation_by_id, save_consultation


router = APIRouter(prefix="/chat", tags=["chat"])

# Service instance
_chat_service = ChatService()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message in the SOAP conversation.

    This endpoint:
    1. Processes the user message
    2. Extracts medical information
    3. Advances the SOAP workflow
    4. Returns AI response with guidance
    """
    consultation = get_consultation_by_id(request.consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    try:
        response = await _chat_service.process_message(request, consultation)

        # Save updated consultation
        save_consultation(consultation)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{consultation_id}/history")
async def get_chat_history(consultation_id: str):
    """
    Get the chat history for a consultation.
    """
    consultation = get_consultation_by_id(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    messages = _chat_service._messages.get(consultation_id, [])

    return {
        "consultation_id": consultation_id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.message_type.value
            }
            for msg in messages
        ]
    }


@router.post("/{consultation_id}/start")
async def start_conversation(consultation_id: str):
    """
    Start the conversation with a greeting.

    Returns the initial AI greeting message.
    """
    consultation = get_consultation_by_id(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    greeting = await _chat_service.generate_stage_prompt(
        consultation.current_stage,
        consultation
    )

    return {
        "message": greeting,
        "current_stage": consultation.current_stage.value,
        "language": consultation.language
    }
