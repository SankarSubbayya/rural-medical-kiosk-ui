"""
SOAP Orchestrator Agent using Google Gemini ADK

==============================================================================
COURSE CONCEPT #1: AGENT POWERED BY LLM (Multi-Agent System)
==============================================================================

This module implements the core AI agent for the Rural Medical Kiosk system.
The SOAP Orchestrator Agent demonstrates:

1. LLM-Powered Agent: Uses Google Gemini 2.0 Flash as the reasoning engine
2. Sequential Agent Behavior: Progresses through SOAP stages in order
3. Automatic Function Calling: Agent autonomously decides which tools to invoke
4. Multi-turn Conversation: Maintains context across multiple interactions

Architecture:
    User Message → Agent → Tool Selection → Tool Execution → Response Generation
                     ↑                            ↓
                     └────── State Update ────────┘

The agent follows the SOAP (Subjective, Objective, Assessment, Plan) clinical
framework, which is the gold standard for medical documentation.

Author: Agentic Health Team
Course: Google Agent Development Kit (ADK) Capstone
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os

from google import genai
from google.genai.types import Tool, FunctionDeclaration, Part, Content


# ==============================================================================
# COURSE CONCEPT #3: SESSIONS & MEMORY (State Management)
# ==============================================================================
# The ConsultationState class implements session state management, tracking
# the entire consultation lifecycle. This enables:
# - Session persistence across multiple API calls
# - Context retention for multi-turn conversations
# - State-driven agent behavior (different actions per stage)
# - Accumulated data (symptoms, analysis results, similar cases)
# ==============================================================================

@dataclass
class ConsultationState:
    """
    Tracks state of active consultation session.

    This dataclass implements SESSION STATE MANAGEMENT - one of the key
    course concepts. It maintains:

    1. Session Identity: consultation_id, patient_id for tracking
    2. Workflow State: current_stage tracks SOAP progression
    3. Accumulated Data: symptoms, analysis results collected over time
    4. Conversation Memory: message_history for context retention

    The state is updated after each tool execution and used to provide
    context-aware responses throughout the consultation.

    Attributes:
        consultation_id: Unique identifier for this consultation session
        patient_id: Patient identifier for record keeping
        language: User's preferred language (en, hi, ta, te, bn)
        current_stage: Current SOAP stage (GREETING, SUBJECTIVE, etc.)
        consent_given: Whether patient has consented to AI consultation
        extracted_symptoms: List of symptoms extracted during SUBJECTIVE stage
        image_captured: Whether a dermatology image has been provided
        image_base64: Base64-encoded image data for analysis
        analysis_results: MedGemma analysis predictions and findings
        similar_cases: Similar historical cases from Qdrant RAG
        message_history: Conversation history for context (last 10 messages)
        created_at: Timestamp when consultation started
    """
    consultation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""
    language: str = "en"
    current_stage: str = "GREETING"  # SOAP stage progression
    consent_given: bool = False
    extracted_symptoms: List[str] = field(default_factory=list)  # Accumulated symptoms
    image_captured: bool = False
    image_base64: Optional[str] = None
    analysis_results: Optional[Dict] = None  # MedGemma predictions
    similar_cases: List[Dict] = field(default_factory=list)  # RAG results
    message_history: List[Dict] = field(default_factory=list)  # Context memory
    created_at: datetime = field(default_factory=datetime.utcnow)


class SOAPAgent:
    """
    SOAP Orchestrator Agent using Google Gemini ADK + MCP tools.

    ===========================================================================
    COURSE CONCEPT #1: AGENT POWERED BY LLM
    ===========================================================================

    This class implements the core LLM-powered agent that orchestrates medical
    consultations. Key characteristics of this agent:

    1. REASONING ENGINE: Google Gemini 2.0 Flash provides intelligent reasoning
    2. AUTONOMOUS TOOL SELECTION: Agent decides which tools to call based on context
    3. SEQUENTIAL WORKFLOW: Progresses through SOAP stages in clinical order
    4. CONTEXT-AWARE: Uses conversation history and state for coherent responses

    SOAP Stage Progression (Sequential Agent Behavior):
        GREETING → SUBJECTIVE → OBJECTIVE → ASSESSMENT → PLAN → SUMMARY → COMPLETED

    The agent demonstrates AUTOMATIC FUNCTION CALLING where Gemini autonomously
    decides when to invoke tools like:
    - check_message_safety: Guardrails for patient safety
    - extract_symptoms: NLP-based symptom extraction
    - analyze_image: MedGemma vision analysis
    - find_similar_cases: RAG-based case retrieval

    Uses Google's Agent Development Kit (ADK) for:
    - Automatic function calling with tool declarations
    - Multi-turn conversations with context retention
    - State management across the consultation lifecycle
    - Built-in safety guardrails for medical applications
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None,
        ollama_host: str = "http://localhost:11434",
        consultation_id: Optional[str] = None
    ):
        """
        Initialize SOAP Agent with Google ADK.

        This constructor sets up:
        1. LLM Client: Connection to Gemini 2.0 Flash via Google ADK
        2. MCP Tools: 7 custom tools for medical consultation capabilities
        3. Session State: Either new or resumed consultation state
        4. Tool Declarations: ADK-compatible function definitions

        Args:
            model: Gemini model name (default: gemini-2.0-flash-exp)
            api_key: Google API key (reads from GOOGLE_API_KEY env if not provided)
            ollama_host: Ollama server URL (for fallback/hybrid use)
            consultation_id: Optional consultation ID to resume existing consultation
                           (demonstrates session persistence capability)
        """
        self.model_name = model
        self.ollama_host = ollama_host

        # =======================================================================
        # SESSION STATE INITIALIZATION
        # Demonstrates session persistence - can resume existing consultations
        # =======================================================================
        if consultation_id:
            # Resume existing consultation (long-running operation support)
            self.state = ConsultationState(consultation_id=consultation_id)
        else:
            # Create new consultation session
            self.state = ConsultationState()

        # =======================================================================
        # LLM CLIENT INITIALIZATION (Course Concept #1: Agent Powered by LLM)
        # The Gemini client is the reasoning engine for this agent
        # =======================================================================
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Get one at https://aistudio.google.com/apikey"
            )

        self.client = genai.Client(api_key=api_key)

        # =======================================================================
        # MCP TOOLS INITIALIZATION (Course Concept #2: Custom Tools)
        # Load all 7 MCP-compliant tools that extend agent capabilities
        # =======================================================================
        from mcp_server.tools import (
            consultation_tool,  # Session management operations
            medical_tool,       # Medical knowledge extraction
            medgemma_tool,      # Medical image analysis (MedGemma 4B)
            rag_tool,           # Text-based case retrieval
            safety_tool,        # Content safety guardrails
            siglip_rag_tool,    # Image-based case retrieval (SigLIP + Qdrant)
            speech_tool,        # Text-to-speech synthesis
        )

        # Registry of MCP tools available to the agent
        # The agent will autonomously decide which tools to invoke
        self.mcp_tools = {
            "consultation": consultation_tool,
            "medical": medical_tool,
            "medgemma": medgemma_tool,
            "rag": rag_tool,
            "safety": safety_tool,
            "siglip_rag": siglip_rag_tool,
            "speech": speech_tool,
        }

        # Create ADK-compatible tool declarations for Gemini's function calling
        self.tools = self._create_tool_declarations()

        # System instruction for medical context
        self.system_instruction = """You are a compassionate AI medical assistant specializing in dermatology consultations.

You follow the SOAP (Subjective, Objective, Assessment, Plan) framework:
- GREETING: Greet warmly, get consent
- SUBJECTIVE: Gather symptoms, history, concerns (ALWAYS call extract_symptoms when patient describes symptoms)
- OBJECTIVE: Request and analyze images
- ASSESSMENT: Synthesize findings
- PLAN: Provide care recommendations

CRITICAL INTERACTION RULES:
1. ASK ONLY ONE QUESTION AT A TIME - Never ask multiple questions in a single response
2. Wait for the patient's answer before asking the next question
3. Keep questions simple and conversational
4. This is a voice-first interface for low-literacy users - be clear and concise

CRITICAL SAFETY RULES:
1. You are NOT a doctor - always clarify you provide information, not diagnosis
2. For urgent/severe conditions, recommend immediate professional care
3. Never promise cures or definitive diagnoses
4. Respect patient privacy and consent
5. Use simple, empathetic language

TOOL USAGE RULES:
1. ALWAYS call check_message_safety first for every patient message
2. In SUBJECTIVE stage: ALWAYS call extract_symptoms when patient describes their condition
3. In OBJECTIVE stage: Call analyze_image when you receive an image
4. After image analysis: Call find_similar_cases to search for similar dermatology cases
5. In PLAN stage: Call finalize_consultation to generate care plan

EXPLAINING MEDGEMMA ANALYSIS:
When you receive MedGemma image analysis results, you MUST:
1. Explain the findings in SIMPLE, patient-friendly language
2. Mention the condition name and what it means
3. Explain the confidence level in plain terms (e.g., "fairly confident", "very confident")
4. State the urgency level clearly (routine, urgent, emergency)
5. If it's critical/emergency: Strongly urge immediate doctor visit
6. Never use medical jargon - use everyday words

Example patient explanation:
"Based on the image analysis, this looks like eczema with 85% confidence. This means the skin is inflamed
and irritated. This is a routine condition that can be managed with proper care. I recommend seeing a doctor
to get the right treatment."

Available tools:
- check_message_safety: Verify message safety before processing
- extract_symptoms: Extract medical information from patient messages (USE THIS IN SUBJECTIVE STAGE)
- analyze_image: Analyze dermatology images with MedGemma
- find_similar_cases: Search for similar cases using RAG
- create_consultation: Create new consultation record
- finalize_consultation: Generate final care plan

Progress through SOAP stages systematically. When in doubt, call the appropriate tool."""

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

        print(f"[SOAP Agent - Gemini] Processing message in stage: {self.state.current_stage}")
        print(f"[SOAP Agent - Gemini] Has image: {bool(image_base64)}")
        if image_base64:
            print(f"[SOAP Agent - Gemini] Image length: {len(image_base64)}")

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

        # Add stage-specific instructions
        if self.state.current_stage == "SUBJECTIVE":
            stage_context += "INSTRUCTION: When patient describes symptoms, you MUST call extract_symptoms function.\n"
        elif self.state.current_stage == "OBJECTIVE":
            stage_context += "INSTRUCTION: When you receive an image, call analyze_image function.\n"

        if self.state.extracted_symptoms:
            stage_context += f"Extracted symptoms: {', '.join(self.state.extracted_symptoms)}\n"

        # Generate response with automatic function calling
        try:
            # Configure tool calling mode based on stage
            tool_config = None
            symptom_keywords = ["symptom", "rash", "pain", "itch", "red", "fever", "cough", "sore"]
            if self.state.current_stage == "SUBJECTIVE" and any(keyword in message.lower() for keyword in symptom_keywords):
                # Force tool calling for symptom extraction
                tool_config = {"function_calling_config": {"mode": "ANY"}}

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config={
                    "system_instruction": self.system_instruction + stage_context,
                    "tools": self.tools,
                    "tool_config": tool_config,
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
                        print(f"[SOAP Agent - Gemini] Gemini called function: {fc.name}")

                        # SPECIAL HANDLING: If Gemini calls analyze_image, use our enhanced workflow
                        if fc.name == "analyze_image" and image_base64:
                            print(f"[SOAP Agent - Gemini] Intercepting analyze_image - using enhanced Qdrant workflow")

                            # STEP 1: Search Qdrant for similar cases
                            print(f"[SOAP Agent - Gemini] Searching Qdrant for similar cases...")
                            similar_cases_result = await self._execute_tool("find_similar_cases", {
                                "image_base64": image_base64,
                                "top_k": 3,
                                "min_score": 0.7
                            })

                            similar_cases = []
                            if similar_cases_result.get("success") and similar_cases_result.get("similar_cases"):
                                similar_cases = similar_cases_result["similar_cases"]
                                print(f"[SOAP Agent - Gemini] Found {len(similar_cases)} similar cases from Qdrant")

                            # STEP 2: Build enhanced clinical context
                            clinical_context = message
                            if similar_cases and len(similar_cases) > 0:
                                similar_cases_context = "\n\nSimilar Historical Cases:\n"
                                for i, case in enumerate(similar_cases[:3], 1):
                                    similar_cases_context += f"{i}. {case.get('diagnosis', 'Unknown')} ({case.get('similarity_score', 0):.0%})\n"
                                clinical_context += similar_cases_context
                                print(f"[SOAP Agent - Gemini] Enhanced with {len(similar_cases)} similar cases")

                            # STEP 3: Call analyze_image with enhanced context
                            result = await self._execute_tool("analyze_image", {
                                "image_base64": image_base64,
                                "clinical_context": clinical_context,
                                "language": self.state.language
                            })

                            # Store results in state
                            if result.get('success') and result.get('analysis'):
                                self.state.analysis_results = result['analysis']
                                self.state.similar_cases = similar_cases
                                self.state.image_captured = True
                        else:
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

            print(f"[SOAP Agent - Gemini] Initial response text: {final_text[:200] if final_text else 'NONE'}")
            print(f"[SOAP Agent - Gemini] Functions called by Gemini: {[fc['name'] for fc in function_calls]}")

            # Fallback: If in SUBJECTIVE stage and extract_symptoms wasn't called, call it manually
            symptom_keywords = ["symptom", "rash", "pain", "itch", "red", "fever", "cough", "sore", "hurt", "burn"]
            if (self.state.current_stage == "SUBJECTIVE" and
                any(keyword in message.lower() for keyword in symptom_keywords) and
                not any(fc["name"] == "extract_symptoms" for fc in function_calls)):

                # Manually extract symptoms
                symptom_result = await self._execute_tool("extract_symptoms", {
                    "patient_message": message,
                    "language": self.state.language
                })
                function_calls.append({
                    "name": "extract_symptoms",
                    "args": {"patient_message": message, "language": self.state.language},
                    "result": symptom_result
                })

            # Fallback: If image provided but analyze_image wasn't called, call it manually
            # (trigger regardless of stage to ensure image is always analyzed)
            if (image_base64 and
                not self.state.image_captured and
                not any(fc["name"] == "analyze_image" for fc in function_calls)):

                print(f"[SOAP Agent - Gemini] Auto-triggering image analysis in OBJECTIVE stage")
                print(f"[SOAP Agent - Gemini] Image base64 length: {len(image_base64)}")

                # STEP 1: First search Qdrant for similar cases using SigLIP embeddings
                print(f"[SOAP Agent - Gemini] Searching Qdrant for similar cases...")
                similar_cases_result = await self._execute_tool("find_similar_cases", {
                    "image_base64": image_base64,
                    "top_k": 3,
                    "min_score": 0.7
                })

                print(f"[SOAP Agent - Gemini] Qdrant search result: success={similar_cases_result.get('success')}, has_cases={bool(similar_cases_result.get('similar_cases'))}")

                similar_cases = []
                if similar_cases_result.get("success") and similar_cases_result.get("similar_cases"):
                    similar_cases = similar_cases_result["similar_cases"]
                    print(f"[SOAP Agent - Gemini] Found {len(similar_cases)} similar cases from Qdrant")
                    for i, case in enumerate(similar_cases[:3]):
                        print(f"  Case {i+1}: {case.get('diagnosis', 'N/A')} (score: {case.get('similarity_score', 0):.3f})")
                else:
                    print(f"[SOAP Agent - Gemini] No similar cases found. Result: {similar_cases_result}")

                function_calls.append({
                    "name": "find_similar_cases",
                    "args": {"image_base64": "...", "top_k": 3, "min_score": 0.7},
                    "result": similar_cases_result
                })

                # STEP 2: Build enhanced clinical context with similar cases
                clinical_context = ", ".join(self.state.extracted_symptoms) if self.state.extracted_symptoms else message
                print(f"[SOAP Agent - Gemini] Clinical context: {clinical_context}")

                # Add similar cases context for MedGemma
                if similar_cases and len(similar_cases) > 0:
                    similar_cases_context = "\n\nSimilar Historical Cases from Database:\n"
                    for i, case in enumerate(similar_cases[:3], 1):
                        diagnosis = case.get('diagnosis', 'Unknown')
                        score = case.get('similarity_score', 0)
                        similar_cases_context += f"{i}. {diagnosis} (similarity: {score:.0%})\n"

                        symptoms = case.get('symptoms', [])
                        if symptoms and len(symptoms) > 0:
                            # Handle if symptoms is a list
                            if isinstance(symptoms, list):
                                similar_cases_context += f"   Symptoms: {', '.join(str(s) for s in symptoms[:3])}\n"
                            else:
                                similar_cases_context += f"   Symptoms: {symptoms}\n"

                        treatment = case.get('treatment', '')
                        if treatment:
                            similar_cases_context += f"   Treatment: {treatment}\n"

                    clinical_context += similar_cases_context
                    print(f"[SOAP Agent - Gemini] Enhanced context with {len(similar_cases)} similar cases")

                # STEP 3: Analyze image with MedGemma (now enriched with similar cases)
                image_result = await self._execute_tool("analyze_image", {
                    "image_base64": image_base64,
                    "clinical_context": clinical_context,
                    "language": self.state.language
                })

                print(f"[SOAP Agent - Gemini] Image analysis result: {image_result.get('success', False)}")
                if image_result.get('success') and image_result.get('analysis'):
                    analysis_data = image_result['analysis']
                    print(f"[SOAP Agent - Gemini] Analysis predictions: {analysis_data.get('predictions', [])}")
                    print(f"[SOAP Agent - Gemini] Visual description: {analysis_data.get('visual_description', 'N/A')[:100]}")

                    # Store MedGemma analysis AND similar cases in state for SOAP note generation
                    self.state.analysis_results = analysis_data
                    self.state.similar_cases = similar_cases

                function_calls.append({
                    "name": "analyze_image",
                    "args": {"image_base64": "...", "clinical_context": clinical_context[:200] + "..."},
                    "result": image_result
                })

                # Mark image as captured
                self.state.image_captured = True

            # If no text in first response OR if we just did image analysis, generate follow-up
            # to ensure Gemini explains the MedGemma findings
            has_image_analysis = any(fc["name"] == "analyze_image" for fc in function_calls)
            if (not final_text and function_calls) or (has_image_analysis and function_calls):
                # Build follow-up messages manually with function results
                # Add model message with function call
                contents.append(
                    Content(
                        role="model",
                        parts=[Part(text="") for _ in function_calls]  # Empty text to indicate function call
                    )
                )

                # Add function responses
                for fc in function_calls:
                    contents.append(
                        Content(
                            role="function",
                            parts=[Part(
                                function_response={
                                    "name": fc["name"],
                                    "response": fc["result"]
                                }
                            )]
                        )
                    )

                # If we just analyzed an image, add explicit prompt for explanation
                if has_image_analysis:
                    contents.append(
                        Content(
                            role="user",
                            parts=[Part(text="Please explain the image analysis results to me in simple language.")]
                        )
                    )

                # Generate final response with function results
                followup_response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config={
                        "system_instruction": self.system_instruction + stage_context,
                        "temperature": 0.7,
                    }
                )

                final_text = followup_response.text
                print(f"[SOAP Agent - Gemini] Follow-up response after function calls: {final_text[:200]}")

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
            self._update_stage(message)

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

    def _update_stage(self, message: str = ""):
        """Update SOAP stage based on consultation state and user message."""

        if self.state.current_stage == "GREETING":
            # Check for consent keywords in multiple languages
            consent_keywords = [
                # English
                "yes", "agree", "ok", "okay", "sure", "proceed", "continue",
                # Hindi (हां, मैं सहमत हूं)
                "हां", "सहमत", "ठीक", "आगे",
                # Tamil (ஆம், நான் சம்மதிக்கிறேன்)
                "ஆம்", "சம்மதிக்கிறேன்", "சரி",
                # Telugu (అవును, నేను అంగీకరిస్తున్నాను)
                "అవును", "అంగీకరిస్తున్నాను", "సరే",
                # Bengali (হ্যাঁ, আমি সম্মত)
                "হ্যাঁ", "সম্মত", "ঠিক"
            ]
            if any(keyword in message for keyword in consent_keywords):
                self.state.consent_given = True

            # Transition to SUBJECTIVE after consent
            if self.state.consent_given:
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
