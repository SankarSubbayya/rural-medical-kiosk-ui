"""
Chat and conversation models for the GPT-based conversational interface.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

from .soap import SOAPStage


class MessageRole(str, Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Type of message content."""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    ACTION = "action"


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    id: str
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # For voice messages
    audio_url: Optional[str] = None
    original_language: Optional[str] = None
    translated_content: Optional[str] = None  # If translated from another language

    # For image messages
    image_url: Optional[str] = None
    image_analysis: Optional[str] = None

    # For action messages (e.g., "Take a photo", "Confirm consent")
    action_type: Optional[str] = None
    action_data: Optional[dict] = None


class ConversationContext(BaseModel):
    """
    Context maintained throughout the conversation.
    Used to track SOAP progress and extracted information.
    """
    consultation_id: str
    patient_id: str
    language: str = "en"
    current_stage: SOAPStage = SOAPStage.GREETING

    # Extracted information (updated as conversation progresses)
    extracted_symptoms: List[str] = Field(default_factory=list)
    extracted_duration: Optional[str] = None
    extracted_location: Optional[str] = None
    extracted_severity: Optional[str] = None

    # Conversation flags
    consent_obtained: bool = False
    image_captured: bool = False
    analysis_complete: bool = False

    # For de-escalation checks
    non_medical_flags: List[str] = Field(default_factory=list)
    common_sense_questions_asked: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Request to the chat endpoint."""
    consultation_id: str
    message: str
    message_type: MessageType = MessageType.TEXT
    language: Optional[str] = None  # Auto-detect if not provided
    image_base64: Optional[str] = None  # For image messages
    audio_base64: Optional[str] = None  # For voice messages


class SuggestedAction(BaseModel):
    """An action suggested by the assistant."""
    type: str  # "take_photo", "confirm", "select_location", etc.
    label: str  # Display text
    data: Optional[dict] = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    message: str
    message_type: MessageType = MessageType.TEXT

    # For voice output
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None

    # Conversation state
    current_stage: SOAPStage
    stage_progress: float = Field(
        ge=0.0, le=1.0,
        description="Progress within current stage (0-1)"
    )

    # Suggested actions for the UI
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)

    # Flags
    requires_image: bool = False
    requires_confirmation: bool = False
    consultation_complete: bool = False

    # Detected language
    detected_language: Optional[str] = None


class ConversationHistory(BaseModel):
    """Complete conversation history for a consultation."""
    consultation_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    context: ConversationContext


# System prompts for different stages
SOAP_SYSTEM_PROMPTS = {
    SOAPStage.GREETING: """You are a friendly medical assistant at a rural health kiosk.
Your role is to help gather information about skin conditions and connect patients with healthcare providers.

IMPORTANT RULES:
- You are NOT a doctor and cannot diagnose or prescribe
- You are a patient advocate helping gather case history
- Speak simply and clearly for low-literacy users
- Be warm, reassuring, and patient

Start by:
1. Greeting the patient warmly
2. Asking how you can help today
3. Confirming their preferred language if needed""",

    SOAPStage.SUBJECTIVE: """You are gathering the patient's story about their skin condition.

EXTRACT:
- What is the main concern? (chief complaint)
- How long has it been present? (duration)
- Where on the body? (location)
- What does it feel like? (itching, burning, pain)
- What makes it better or worse?
- Any treatments tried?

FILTER OUT irrelevant information like:
- Weather complaints
- Family drama
- Unrelated stories

Ask follow-up questions to get complete information.
When you have enough details, summarize what you heard and ask to take a photo.""",

    SOAPStage.OBJECTIVE: """You are helping capture an image of the skin condition.

STEPS:
1. Explain why a photo is needed
2. Ask for EXPLICIT permission: "Do I have your permission to take a photo?"
3. Wait for clear "yes" confirmation
4. Guide them to position the affected area
5. Ensure good lighting
6. Capture and confirm the image quality

NEVER proceed without explicit verbal consent.""",

    SOAPStage.ASSESSMENT: """You are explaining the analysis results to the patient.

RULES:
- Present findings as POSSIBILITIES, not diagnoses
- Use simple, non-scary language
- Explain what the similar cases from our database suggest
- If critical condition suspected, stay calm but emphasize urgency
- Always recommend seeing a healthcare provider

Example: "Based on what you've told me and the image, this looks similar to cases of [condition] we have in our records. This is not a diagnosis - only a doctor can confirm that.""",

    SOAPStage.PLAN: """You are providing guidance and next steps.

INCLUDE:
- Clear explanation of urgency level
- Specific next steps (where to go, what to do)
- Transportation guidance if needed
- What to tell the doctor
- Self-care tips if appropriate (non-prescription only)
- Follow-up recommendations

PROVIDE:
- Simple patient summary (spoken)
- Offer to send formal report to healthcare facility

Be encouraging and supportive.""",

    SOAPStage.SUMMARY: """Summarize the consultation:
- Recap the main concern
- What was observed
- What the next steps are
- Remind them this is guidance, not diagnosis
- Wish them well and offer to help again"""
}


# Common sense checks for de-escalation
COMMON_SENSE_CHECKS = [
    {
        "patterns": ["blue", "paint", "ink", "marker", "dye"],
        "question": "That color looks unusual. Did you recently handle paint, ink, or dye? Have you tried washing the area?",
        "if_yes": "dismiss",
        "response": "It sounds like this might just be from paint or dye. Try washing thoroughly with soap and water. If it doesn't come off or if you notice any irritation, let me know."
    },
    {
        "patterns": ["tattoo", "henna", "mehndi", "mehendi"],
        "question": "Is that a tattoo or henna design?",
        "if_yes": "dismiss",
        "response": "I see! Tattoos and henna aren't skin conditions. Is there something else I can help you with?"
    },
    {
        "patterns": ["pimple", "acne", "teenager", "puberty", "adolescent"],
        "question": "This looks like it could be common acne. Are you a teenager, or did this start during puberty?",
        "if_yes": "educate",
        "response": "This looks like normal acne, which is very common during adolescence. Keep the area clean, avoid touching or picking at it, and it usually improves over time. Using a gentle soap can help. If it's severe or painful, a doctor can suggest treatments."
    },
    {
        "patterns": ["mosquito", "bug bite", "insect"],
        "question": "Does this look like it could be from a mosquito or insect bite?",
        "if_yes": "educate",
        "response": "This looks like an insect bite. Keep it clean, try not to scratch, and it should heal in a few days. If it becomes very swollen, painful, or shows signs of infection (increasing redness, pus), please see a doctor."
    },
    {
        "patterns": ["sunburn", "sun", "beach", "outside"],
        "question": "Have you been in the sun recently without protection?",
        "if_yes": "educate",
        "response": "This looks like sunburn. Stay out of the sun, keep the area moisturized, and drink plenty of water. Aloe vera can help soothe the skin. If you have blisters or fever, please see a doctor."
    }
]
