"""
SOAP Orchestrator Agent using Google Gemini ADK

Orchestrates medical consultations through SOAP workflow stages using MCP tools
and Google's Agent Development Kit (ADK) for intelligent function calling.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os

from google import genai
from google.genai.types import Tool, FunctionDeclaration, Part, Content


@dataclass
class ConsultationState:
    """Tracks state of active consultation."""
    consultation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""
    language: str = "en"
    current_stage: str = "GREETING"
    consent_given: bool = False
    extracted_symptoms: List[str] = field(default_factory=list)
    image_captured: bool = False
    image_base64: Optional[str] = None
    analysis_results: Optional[Dict] = None
    similar_cases: List[Dict] = field(default_factory=list)
    message_history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class SOAPAgent:
    """
    SOAP Orchestrator Agent using Google Gemini ADK + MCP tools.

    Manages dermatological consultations through SOAP stages:
    GREETING → SUBJECTIVE → OBJECTIVE → ASSESSMENT → PLAN → SUMMARY → COMPLETED

    Uses Google's Agent Development Kit for:
    - Automatic function calling
    - Multi-turn conversations
    - Context management
    - Safety guardrails
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None,
        ollama_host: str = "http://localhost:11434"
    ):
        """
        Initialize SOAP Agent with Google ADK.

        Args:
            model: Gemini model name (default: gemini-2.0-flash-exp)
            api_key: Google API key (reads from GOOGLE_API_KEY env if not provided)
            ollama_host: Ollama server URL (for fallback/hybrid use)
        """
        self.model_name = model
        self.ollama_host = ollama_host
        self.state = ConsultationState()

        # Initialize Google Genai client
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Get one at https://aistudio.google.com/apikey"
            )

        self.client = genai.Client(api_key=api_key)

        # Load MCP tools
        from mcp_server.tools import (
            consultation_tool,
            medical_tool,
            medgemma_tool,
            rag_tool,
            safety_tool,
            siglip_rag_tool,
            speech_tool,
        )

        self.mcp_tools = {
            "consultation": consultation_tool,
            "medical": medical_tool,
            "medgemma": medgemma_tool,
            "rag": rag_tool,
            "safety": safety_tool,
            "siglip_rag": siglip_rag_tool,
            "speech": speech_tool,
        }

        # Define ADK-compatible tool declarations
        self.tools = self._create_tool_declarations()

        # System instruction for medical context
        self.system_instruction = """You are a compassionate AI medical assistant specializing in dermatology consultations.

You follow the SOAP (Subjective, Objective, Assessment, Plan) framework:
- GREETING: Greet warmly, get consent
- SUBJECTIVE: Gather symptoms, history, concerns
- OBJECTIVE: Request and analyze images
- ASSESSMENT: Synthesize findings
- PLAN: Provide care recommendations

CRITICAL SAFETY RULES:
1. You are NOT a doctor - always clarify you provide information, not diagnosis
2. For urgent/severe conditions, recommend immediate professional care
3. Never promise cures or definitive diagnoses
4. Respect patient privacy and consent
5. Use simple, empathetic language

Available tools:
- check_message_safety: Verify message safety before processing
- extract_symptoms: Extract medical information from patient messages
- analyze_image: Analyze dermatology images with MedGemma
- find_similar_cases: Search for similar cases using RAG
- create_consultation: Create new consultation record
- finalize_consultation: Generate final care plan

Always check message safety first. Progress through SOAP stages systematically."""

    def _create_tool_declarations(self) -> List[Tool]:
        """Create ADK-compatible tool declarations from MCP tools."""

        tools = [
            Tool(
                function_declarations=[
                    FunctionDeclaration(
                        name="check_message_safety",
                        description="Check if patient message violates safety guardrails (diagnosis demands, harmful requests). Call this FIRST before processing any message.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Patient message to check"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Language code (en, hi, ta, etc.)"
                                }
                            },
                            "required": ["message"]
                        }
                    ),
                    FunctionDeclaration(
                        name="extract_symptoms",
                        description="Extract medical symptoms and information from patient message",
                        parameters={
                            "type": "object",
                            "properties": {
                                "patient_message": {
                                    "type": "string",
                                    "description": "Patient's description of their condition"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Language code"
                                }
                            },
                            "required": ["patient_message"]
                        }
                    ),
                    FunctionDeclaration(
                        name="analyze_image",
                        description="Analyze dermatology image using MedGemma vision model",
                        parameters={
                            "type": "object",
                            "properties": {
                                "image_base64": {
                                    "type": "string",
                                    "description": "Base64-encoded image data"
                                },
                                "clinical_context": {
                                    "type": "string",
                                    "description": "Patient symptoms and context"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Language code"
                                }
                            },
                            "required": ["image_base64"]
                        }
                    ),
                    FunctionDeclaration(
                        name="find_similar_cases",
                        description="Search for similar dermatology cases using image embeddings (SigLIP RAG)",
                        parameters={
                            "type": "object",
                            "properties": {
                                "image_base64": {
                                    "type": "string",
                                    "description": "Base64-encoded image for similarity search"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "Number of similar cases to return"
                                }
                            },
                            "required": ["image_base64"]
                        }
                    ),
                    FunctionDeclaration(
                        name="create_consultation",
                        description="Create a new consultation record",
                        parameters={
                            "type": "object",
                            "properties": {
                                "patient_id": {
                                    "type": "string",
                                    "description": "Patient identifier"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Consultation language"
                                }
                            },
                            "required": ["patient_id"]
                        }
                    ),
                    FunctionDeclaration(
                        name="finalize_consultation",
                        description="Generate final care plan and recommendations",
                        parameters={
                            "type": "object",
                            "properties": {
                                "consultation_id": {
                                    "type": "string",
                                    "description": "Consultation ID to finalize"
                                }
                            },
                            "required": ["consultation_id"]
                        }
                    )
                ]
            )
        ]

        return tools

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool based on function call from ADK."""

        # Map ADK function names to MCP tools
        tool_mapping = {
            "check_message_safety": ("safety", "check_message"),
            "extract_symptoms": ("medical", "extract_symptoms"),
            "analyze_image": ("medgemma", "analyze_image"),
            "find_similar_cases": ("siglip_rag", "search_by_image"),
            "create_consultation": ("consultation", "create"),
            "finalize_consultation": ("consultation", "finalize"),
        }

        if name not in tool_mapping:
            return {"success": False, "error": f"Unknown tool: {name}"}

        tool_name, operation = tool_mapping[name]
        tool = self.mcp_tools[tool_name]

        # Execute MCP tool
        result = await tool.run(operation=operation, **args)

        # Update agent state based on results
        if name == "extract_symptoms" and result.get("success"):
            symptoms = result.get("symptoms", [])
            self.state.extracted_symptoms.extend([s["name"] for s in symptoms])

        elif name == "analyze_image" and result.get("success"):
            self.state.analysis_results = result.get("analysis")
            self.state.image_captured = True

        elif name == "find_similar_cases" and result.get("success"):
            self.state.similar_cases = result.get("similar_cases", [])

        return result

    async def process_message(
        self,
        message: str,
        image_base64: Optional[str] = None,
        consultation_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process user message using Google ADK with automatic function calling.

        Args:
            message: User's message
            image_base64: Optional base64-encoded image
            consultation_id: Optional existing consultation ID
            patient_id: Optional patient ID
            language: Language code

        Returns:
            Dict with agent response and state
        """
        # Update state
        if consultation_id:
            self.state.consultation_id = consultation_id
        if patient_id:
            self.state.patient_id = patient_id
        if language:
            self.state.language = language
        if image_base64:
            self.state.image_base64 = image_base64

        # Build conversation context
        contents = []

        # Add message history
        for msg in self.state.message_history[-10:]:  # Last 10 messages for context
            contents.append(
                Content(
                    role="user" if msg["role"] == "user" else "model",
                    parts=[Part(text=msg["content"])]
                )
            )

        # Add current message
        current_parts = [Part(text=message)]

        # Add image if provided
        if image_base64:
            # Remove data URL prefix if present
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]
            current_parts.append(Part(inline_data={"mime_type": "image/jpeg", "data": image_base64}))

        contents.append(Content(role="user", parts=current_parts))

        # Add SOAP stage context
        stage_context = f"\n\nCurrent SOAP stage: {self.state.current_stage}\n"
        if self.state.extracted_symptoms:
            stage_context += f"Extracted symptoms: {', '.join(self.state.extracted_symptoms)}\n"

        # Generate response with automatic function calling
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config={
                    "system_instruction": self.system_instruction + stage_context,
                    "tools": self.tools,
                    "temperature": 0.7,
                }
            )

            # Process function calls if any
            function_calls = []
            final_text = ""

            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.function_call:
                        # Execute the function
                        fc = part.function_call
                        result = await self._execute_tool(fc.name, dict(fc.args))
                        function_calls.append({
                            "name": fc.name,
                            "args": dict(fc.args),
                            "result": result
                        })

                        # If safety check failed, return immediately
                        if fc.name == "check_message_safety" and not result.get("is_safe", True):
                            return {
                                "success": True,
                                "message": result.get("redirect_response", "I cannot assist with that request."),
                                "stage": self.state.current_stage,
                                "safety_triggered": True
                            }

                    elif part.text:
                        final_text += part.text

            # If no text in first response (only function calls), generate follow-up
            if not final_text and function_calls:
                # Add function results to context
                function_results = []
                for fc in function_calls:
                    function_results.append(
                        Content(
                            role="model",
                            parts=[Part(function_call=fc)]
                        )
                    )
                    function_results.append(
                        Content(
                            role="function",
                            parts=[Part(function_response={"name": fc["name"], "response": fc["result"]})]
                        )
                    )

                # Generate final response with function results
                followup_response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents + function_results,
                    config={
                        "system_instruction": self.system_instruction + stage_context,
                        "temperature": 0.7,
                    }
                )

                final_text = followup_response.text

            # Update message history
            self.state.message_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.state.message_history.append({
                "role": "assistant",
                "content": final_text,
                "timestamp": datetime.utcnow().isoformat(),
                "function_calls": function_calls if function_calls else None
            })

            # Determine stage progression
            self._update_stage()

            return {
                "success": True,
                "message": final_text,
                "stage": self.state.current_stage,
                "function_calls": function_calls if function_calls else [],
                "extracted_symptoms": self.state.extracted_symptoms,
                "requires_image": self.state.current_stage == "OBJECTIVE" and not self.state.image_captured,
                "analysis": self.state.analysis_results,
                "similar_cases": self.state.similar_cases if self.state.similar_cases else None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stage": self.state.current_stage
            }

    def _update_stage(self):
        """Update SOAP stage based on consultation state."""

        if self.state.current_stage == "GREETING" and self.state.consent_given:
            self.state.current_stage = "SUBJECTIVE"

        elif self.state.current_stage == "SUBJECTIVE":
            # Move to OBJECTIVE when we have symptoms
            if len(self.state.extracted_symptoms) >= 2:
                self.state.current_stage = "OBJECTIVE"

        elif self.state.current_stage == "OBJECTIVE":
            # Move to ASSESSMENT when image is analyzed
            if self.state.image_captured and self.state.analysis_results:
                self.state.current_stage = "ASSESSMENT"

        elif self.state.current_stage == "ASSESSMENT":
            # Move to PLAN automatically
            self.state.current_stage = "PLAN"

        elif self.state.current_stage == "PLAN":
            # Stay in PLAN until finalized
            pass


def create_soap_agent(**kwargs) -> SOAPAgent:
    """Factory function to create SOAP Agent instance."""
    return SOAPAgent(**kwargs)
