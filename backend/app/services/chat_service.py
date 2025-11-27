"""
Chat Service - Handles conversational AI using Ollama (gpt-oss or similar).

This service manages the SOAP conversation flow, filtering medical information
from patient narratives and guiding the consultation process.
"""
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import ollama

from ..config import get_settings
from ..models.soap import (
    SOAPConsultation, SOAPStage, SubjectiveData, Symptom, UrgencyLevel
)
from ..models.chat import (
    ChatMessage, ChatRequest, ChatResponse, ConversationContext,
    MessageRole, MessageType, SuggestedAction,
    SOAP_SYSTEM_PROMPTS, COMMON_SENSE_CHECKS
)


class ChatService:
    """
    Conversational AI service using Ollama for SOAP-based consultations.

    Uses gpt-oss:20b (or configured model) for:
    - Conversation management
    - SOAP flow progression
    - Medical information extraction
    - Common sense de-escalation
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = ollama.AsyncClient(host=self.settings.ollama_base_url)
        self.model = self.settings.ollama_chat_model  # gpt-oss:20b

        # In-memory storage (replace with database in production)
        self._conversations: Dict[str, ConversationContext] = {}
        self._messages: Dict[str, List[ChatMessage]] = {}
        self._consultations: Dict[str, SOAPConsultation] = {}

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = False,
        temperature: float = 0.7
    ) -> str:
        """
        Call Ollama LLM with messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            json_mode: Whether to request JSON output
            temperature: Sampling temperature

        Returns:
            Response content string
        """
        response = await self.client.chat(
            model=self.model,
            messages=messages,
            format="json" if json_mode else None,
            options={"temperature": temperature}
        )
        return response['message']['content']

    async def process_message(
        self,
        request: ChatRequest,
        consultation: SOAPConsultation
    ) -> ChatResponse:
        """
        Process an incoming message and generate a response.

        Args:
            request: The chat request with user message
            consultation: Current SOAP consultation state

        Returns:
            ChatResponse with assistant message and conversation state
        """
        # Get or create conversation context
        context = self._get_or_create_context(consultation)

        # Store user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=request.message,
            message_type=request.message_type,
            original_language=request.language
        )
        self._add_message(consultation.id, user_message)

        # Check for common sense de-escalation
        deescalation = await self._check_common_sense(request.message, context)
        if deescalation:
            return deescalation

        # Build conversation history for LLM
        messages = self._build_llm_messages(consultation, context)

        # Add user message
        messages.append({
            "role": "user",
            "content": request.message
        })

        # Call Ollama LLM
        assistant_content = await self._call_llm(
            messages=messages,
            json_mode=False,
            temperature=0.7
        )

        # Parse structured response if in SUBJECTIVE stage
        if context.current_stage == SOAPStage.SUBJECTIVE:
            extraction = await self._extract_medical_info(
                request.message,
                assistant_content,
                context
            )
            if extraction:
                consultation.subjective = extraction

        # Store assistant message
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            message_type=MessageType.TEXT
        )
        self._add_message(consultation.id, assistant_message)

        # Determine stage transition
        new_stage, suggested_actions = await self._determine_next_stage(
            context, consultation, assistant_content
        )

        # Update context
        context.current_stage = new_stage
        consultation.current_stage = new_stage

        return ChatResponse(
            message=assistant_content,
            current_stage=new_stage,
            stage_progress=self._calculate_progress(context, consultation),
            suggested_actions=suggested_actions,
            requires_image=new_stage == SOAPStage.OBJECTIVE and not context.image_captured,
            consultation_complete=new_stage == SOAPStage.COMPLETED,
            detected_language=request.language
        )

    async def _extract_medical_info(
        self,
        user_message: str,
        assistant_response: str,
        context: ConversationContext
    ) -> Optional[SubjectiveData]:
        """
        Extract structured medical information from the conversation.
        Uses Ollama to parse and filter medically relevant content.
        """
        extraction_prompt = f"""
Based on this patient message, extract medical information.

Patient said: "{user_message}"

Extract and return JSON with:
{{
    "chief_complaint": "main concern in one sentence",
    "symptoms": [
        {{"name": "symptom", "duration": "how long", "severity": "mild/moderate/severe", "location": "body part"}}
    ],
    "onset": "when it started",
    "duration": "how long present",
    "aggravating_factors": ["what makes worse"],
    "relieving_factors": ["what makes better"],
    "previous_treatments": ["treatments tried"],
    "is_medically_relevant": true,
    "irrelevant_info_filtered": ["list of filtered irrelevant info"]
}}

Filter out irrelevant information like weather complaints, family issues, etc.
Only include medically relevant details.
Return valid JSON only.
"""

        try:
            response = await self._call_llm(
                messages=[
                    {"role": "system", "content": "You extract structured medical information from patient narratives. Return valid JSON only."},
                    {"role": "user", "content": extraction_prompt}
                ],
                json_mode=True,
                temperature=0.3
            )

            data = json.loads(response)

            # Update context with extracted info
            if data.get("symptoms"):
                context.extracted_symptoms.extend(
                    [s["name"] for s in data["symptoms"] if isinstance(s, dict)]
                )
            if data.get("duration"):
                context.extracted_duration = data["duration"]
            if data.get("symptoms") and data["symptoms"]:
                first_symptom = data["symptoms"][0]
                if isinstance(first_symptom, dict) and first_symptom.get("location"):
                    context.extracted_location = first_symptom["location"]

            # Build SubjectiveData
            symptoms = [
                Symptom(
                    name=s.get("name", ""),
                    duration=s.get("duration"),
                    severity=s.get("severity"),
                    location=s.get("location")
                )
                for s in data.get("symptoms", [])
                if isinstance(s, dict)
            ]

            return SubjectiveData(
                raw_transcript=[user_message],
                filtered_narrative=data.get("chief_complaint", ""),
                chief_complaint=data.get("chief_complaint", ""),
                symptoms=symptoms,
                onset=data.get("onset"),
                duration=data.get("duration"),
                aggravating_factors=data.get("aggravating_factors", []),
                relieving_factors=data.get("relieving_factors", []),
                previous_treatments=data.get("previous_treatments", [])
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error extracting medical info: {e}")
            return None

    async def _check_common_sense(
        self,
        message: str,
        context: ConversationContext
    ) -> Optional[ChatResponse]:
        """
        Check for common sense de-escalation scenarios.
        E.g., paint on skin, tattoos, mild acne, insect bites.
        """
        message_lower = message.lower()

        for check in COMMON_SENSE_CHECKS:
            # Check if already asked this question
            if check["question"] in context.common_sense_questions_asked:
                continue

            # Check if any pattern matches
            patterns = check["patterns"]
            if any(pattern in message_lower for pattern in patterns):
                context.common_sense_questions_asked.append(check["question"])
                context.non_medical_flags.append(check["patterns"][0])

                return ChatResponse(
                    message=check["question"],
                    current_stage=context.current_stage,
                    stage_progress=0.5,
                    suggested_actions=[
                        SuggestedAction(type="confirm", label="Yes"),
                        SuggestedAction(type="deny", label="No")
                    ],
                    requires_confirmation=True
                )

        return None

    async def _determine_next_stage(
        self,
        context: ConversationContext,
        consultation: SOAPConsultation,
        response: str
    ) -> tuple[SOAPStage, List[SuggestedAction]]:
        """
        Determine if the conversation should move to the next SOAP stage.
        """
        current = context.current_stage
        actions = []

        if current == SOAPStage.GREETING:
            # Move to subjective once greeting is done
            return SOAPStage.SUBJECTIVE, []

        elif current == SOAPStage.SUBJECTIVE:
            # Check if we have enough information
            if self._has_sufficient_subjective_info(consultation):
                actions = [
                    SuggestedAction(
                        type="take_photo",
                        label="Take a photo of the affected area"
                    )
                ]
                return SOAPStage.OBJECTIVE, actions

        elif current == SOAPStage.OBJECTIVE:
            if context.image_captured:
                return SOAPStage.ASSESSMENT, []

        elif current == SOAPStage.ASSESSMENT:
            if context.analysis_complete:
                return SOAPStage.PLAN, []

        elif current == SOAPStage.PLAN:
            # Check if plan has been communicated
            return SOAPStage.SUMMARY, [
                SuggestedAction(
                    type="send_report",
                    label="Send report to healthcare facility"
                )
            ]

        elif current == SOAPStage.SUMMARY:
            return SOAPStage.COMPLETED, []

        return current, actions

    def _has_sufficient_subjective_info(self, consultation: SOAPConsultation) -> bool:
        """Check if we have gathered enough subjective information."""
        subj = consultation.subjective
        return bool(
            subj.chief_complaint and
            subj.symptoms and
            len(subj.symptoms) > 0
        )

    def _build_llm_messages(
        self,
        consultation: SOAPConsultation,
        context: ConversationContext
    ) -> List[Dict[str, str]]:
        """Build the message history for Ollama."""
        messages = []

        # System prompt based on current stage
        system_prompt = SOAP_SYSTEM_PROMPTS.get(
            context.current_stage,
            SOAP_SYSTEM_PROMPTS[SOAPStage.GREETING]
        )

        # Add language instruction if not English
        if consultation.language != "en":
            system_prompt += f"\n\nIMPORTANT: Respond in {consultation.language}. The patient speaks this language."

        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        history = self._messages.get(consultation.id, [])
        for msg in history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        return messages

    def _calculate_progress(
        self,
        context: ConversationContext,
        consultation: SOAPConsultation
    ) -> float:
        """Calculate progress within the current stage."""
        stage = context.current_stage

        if stage == SOAPStage.GREETING:
            return 1.0 if consultation.consent_given else 0.5

        elif stage == SOAPStage.SUBJECTIVE:
            subj = consultation.subjective
            score = 0.0
            if subj.chief_complaint:
                score += 0.4
            if subj.symptoms:
                score += 0.3
            if subj.duration or subj.onset:
                score += 0.3
            return min(score, 1.0)

        elif stage == SOAPStage.OBJECTIVE:
            return 1.0 if context.image_captured else 0.0

        elif stage == SOAPStage.ASSESSMENT:
            return 1.0 if context.analysis_complete else 0.5

        elif stage == SOAPStage.PLAN:
            return 1.0 if consultation.plan.patient_guidance else 0.5

        return 0.0

    def _get_or_create_context(
        self,
        consultation: SOAPConsultation
    ) -> ConversationContext:
        """Get or create conversation context."""
        if consultation.id not in self._conversations:
            self._conversations[consultation.id] = ConversationContext(
                consultation_id=consultation.id,
                patient_id=consultation.patient_id,
                language=consultation.language,
                current_stage=consultation.current_stage
            )
        return self._conversations[consultation.id]

    def _add_message(self, consultation_id: str, message: ChatMessage):
        """Add a message to the conversation history."""
        if consultation_id not in self._messages:
            self._messages[consultation_id] = []
        self._messages[consultation_id].append(message)

    async def generate_stage_prompt(
        self,
        stage: SOAPStage,
        consultation: SOAPConsultation
    ) -> str:
        """Generate an appropriate prompt for entering a new stage."""
        prompts = {
            SOAPStage.GREETING: "Hello! I'm here to help you with your skin concern. What brings you in today?",
            SOAPStage.SUBJECTIVE: "Can you tell me more about what you're experiencing? When did you first notice this?",
            SOAPStage.OBJECTIVE: "Thank you for sharing that. To better understand your condition, I'd like to take a photo of the affected area. Do I have your permission?",
            SOAPStage.ASSESSMENT: "I'm analyzing the information you've provided and the image. Please give me a moment...",
            SOAPStage.PLAN: "Based on my analysis, here's what I recommend...",
            SOAPStage.SUMMARY: "Let me summarize what we discussed today..."
        }
        return prompts.get(stage, "How can I help you?")
