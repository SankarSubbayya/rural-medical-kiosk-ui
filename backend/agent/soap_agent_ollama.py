"""
SOAP Orchestrator Agent using Ollama (Local LLM)

Orchestrates medical consultations through SOAP workflow stages using MCP tools
and Ollama's function calling capabilities.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
import httpx


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
    SOAP Orchestrator Agent using Ollama + MCP tools.

    Manages dermatological consultations through SOAP stages:
    GREETING → SUBJECTIVE → OBJECTIVE → ASSESSMENT → PLAN → SUMMARY → COMPLETED

    Uses Ollama's function calling for:
    - Automatic tool selection
    - Multi-turn conversations
    - Context management
    """

    def __init__(
        self,
        model: str = "gpt-oss:20b",
        ollama_host: str = "http://localhost:11434"
    ):
        """
        Initialize SOAP Agent with Ollama.

        Args:
            model: Ollama model name (default: gpt-oss:20b)
            ollama_host: Ollama server URL
        """
        self.model_name = model
        self.ollama_host = ollama_host
        self.state = ConsultationState()

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

        # Define Ollama-compatible tool declarations
        self.tools = self._create_tool_declarations()

        # System instruction for medical context
        self.system_instruction = """You are a compassionate AI medical assistant specializing in dermatology consultations.

You follow the SOAP (Subjective, Objective, Assessment, Plan) framework:
- GREETING: Greet warmly, get consent
- SUBJECTIVE: Gather symptoms, history, concerns ONE QUESTION AT A TIME
- OBJECTIVE: Request and analyze images
- ASSESSMENT: Synthesize findings
- PLAN: Provide care recommendations

CRITICAL SAFETY RULES:
1. You are NOT a doctor - always clarify you provide information, not diagnosis
2. For urgent/severe conditions, recommend immediate professional care
3. Never promise cures or definitive diagnoses
4. Respect patient privacy and consent
5. Use simple, empathetic language

CONVERSATION STYLE - VERY IMPORTANT:
- Ask ONE question at a time, never multiple questions in a single response
- Keep responses SHORT and conversational (2-3 sentences max)
- After patient answers, ask the NEXT relevant question
- Gradually build understanding through natural dialogue
- Don't overwhelm with long lists of questions

EXAMPLES OF GOOD vs BAD:
❌ BAD: "Can you tell me: 1. How long have you had it? 2. Does it itch? 3. Any pain? 4. Recent changes? 5. Other symptoms?"
✅ GOOD: "How long have you had this white spot?"
(Then after patient responds, ask the next question)

TOOL USAGE GUIDELINES (Use when needed):
- In SUBJECTIVE stage: If patient describes symptoms in detail, call extract_symptoms
- In OBJECTIVE stage: If image is provided, call analyze_image
- After image analysis: Call find_similar_cases for similar dermatology cases
- In PLAN stage: Call finalize_consultation to generate final care plan

Start by warmly greeting the patient and asking about their main concern. Always keep it conversational and simple."""

    def _create_tool_declarations(self) -> List[Dict]:
        """Create Ollama-compatible tool declarations from MCP tools."""

        return [
            {
                "type": "function",
                "function": {
                    "name": "check_message_safety",
                    "description": "Check if patient message violates safety guardrails (diagnosis demands, harmful requests). Call this FIRST before processing any message.",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_symptoms",
                    "description": "Extract medical symptoms and information from patient message. ALWAYS call this in SUBJECTIVE stage when patient describes their condition.",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_image",
                    "description": "Analyze dermatology image using MedGemma vision model",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_similar_cases",
                    "description": "Search for similar dermatology cases using image embeddings (SigLIP RAG)",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_consultation",
                    "description": "Create a new consultation record",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finalize_consultation",
                    "description": "Generate final care plan and recommendations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "consultation_id": {
                                "type": "string",
                                "description": "Consultation ID to finalize"
                            }
                        },
                        "required": ["consultation_id"]
                    }
                }
            }
        ]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MCP tool function call.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            # Map function names to MCP tools
            tool_map = {
                "check_message_safety": ("safety", "check_message_safety"),
                "extract_symptoms": ("medical", "extract_symptoms"),
                "analyze_image": ("medgemma", "analyze_image"),
                "find_similar_cases": ("rag", "find_similar_cases"),
                "create_consultation": ("consultation", "create_consultation"),
                "finalize_consultation": ("consultation", "finalize_consultation"),
            }

            if tool_name not in tool_map:
                return {"error": f"Unknown tool: {tool_name}"}

            mcp_name, func_name = tool_map[tool_name]
            tool_module = self.mcp_tools[mcp_name]

            # Execute tool via the module's run() function
            print(f"[SOAP Agent] Calling MCP tool: {mcp_name}.{func_name} with args: {list(arguments.keys())}")
            result = await tool_module.run(operation=func_name, **arguments)
            if result:
                success = result.get('success')
                error = result.get('error', '')
                print(f"[SOAP Agent] Tool result - success: {success}, error: {error[:200] if error else 'None'}")
            else:
                print(f"[SOAP Agent] Tool result: None")

            # Update state based on tool results
            if tool_name == "extract_symptoms" and result.get("symptoms"):
                self.state.extracted_symptoms = result["symptoms"]

            if tool_name == "analyze_image" and result.get("analysis"):
                self.state.image_captured = True
                self.state.analysis_results = result["analysis"]

            if tool_name == "find_similar_cases" and result.get("similar_cases"):
                self.state.similar_cases = result["similar_cases"]

            return result

        except Exception as e:
            return {"error": str(e)}

    async def _call_ollama(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Call Ollama chat API with function calling support.

        Args:
            messages: Conversation messages
            tools: Available tools for function calling

        Returns:
            Ollama response
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            }

            if tools:
                payload["tools"] = tools

            response = await client.post(
                f"{self.ollama_host}/api/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()

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
            if any(keyword in message.lower() for keyword in consent_keywords):
                self.state.consent_given = True
                self.state.current_stage = "SUBJECTIVE"

        elif self.state.current_stage == "SUBJECTIVE":
            # Move to OBJECTIVE when symptoms are extracted and we need image
            if self.state.extracted_symptoms and not self.state.image_captured:
                self.state.current_stage = "OBJECTIVE"

        elif self.state.current_stage == "OBJECTIVE":
            # Move to ASSESSMENT after image analysis
            if self.state.image_captured and self.state.analysis_results:
                self.state.current_stage = "ASSESSMENT"

        elif self.state.current_stage == "ASSESSMENT":
            # Move to PLAN after assessment
            if self.state.analysis_results:
                self.state.current_stage = "PLAN"

        elif self.state.current_stage == "PLAN":
            # Can move to COMPLETED
            self.state.current_stage = "COMPLETED"

    async def process_message(
        self,
        message: str,
        image_base64: Optional[str] = None,
        consultation_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process user message through SOAP agent.

        Args:
            message: User message
            image_base64: Optional base64-encoded image
            consultation_id: Existing consultation ID (or None for new)
            patient_id: Patient identifier
            language: Language code (en, hi, ta, etc.)

        Returns:
            Agent response with message, stage, and any analysis/recommendations
        """
        try:
            # Update state
            if patient_id:
                self.state.patient_id = patient_id
            if language:
                self.state.language = language
            if image_base64:
                self.state.image_base64 = image_base64

            # Build conversation history
            messages = [
                {"role": "system", "content": self.system_instruction}
            ]

            # Add message history
            for msg in self.state.message_history:
                messages.append(msg)

            # Add current stage context
            stage_context = f"\nCurrent SOAP stage: {self.state.current_stage}"
            if self.state.extracted_symptoms:
                # Handle both list of strings and list of dicts
                if isinstance(self.state.extracted_symptoms[0], dict):
                    symptom_names = [s.get('name', str(s)) for s in self.state.extracted_symptoms]
                else:
                    symptom_names = self.state.extracted_symptoms
                stage_context += f"\nExtracted symptoms: {', '.join(symptom_names)}"
            if self.state.consent_given:
                stage_context += "\nConsent: Given"

            # Add user message
            user_message = f"{stage_context}\n\nPatient: {message}"
            if image_base64:
                user_message += "\n[Image provided]"
                print(f"[SOAP Agent] Image received: {len(image_base64)} chars")

            messages.append({"role": "user", "content": user_message})

            # Initialize final_response
            final_response = None

            # If image provided, analyze it directly to avoid tool-calling issues with large base64
            if image_base64 and not self.state.image_captured:
                print(f"[SOAP Agent] Direct image analysis with RAG (bypassing Ollama tools)")

                # Strip data URL prefix if present
                clean_base64 = image_base64
                if image_base64.startswith('data:image'):
                    clean_base64 = image_base64.split(',', 1)[1]
                    print(f"[SOAP Agent] Stripped data URL prefix, clean base64 length: {len(clean_base64)}")

                # Step 1: Analyze image with MedGemma
                analysis_args = {
                    "image_base64": clean_base64,
                    "consultation_id": self.state.consultation_id
                }

                # Extract symptom names for context
                symptom_names = []
                if self.state.extracted_symptoms:
                    if isinstance(self.state.extracted_symptoms[0], dict):
                        symptom_names = [s.get('name', '') for s in self.state.extracted_symptoms if s.get('name')]
                    else:
                        symptom_names = self.state.extracted_symptoms

                    if symptom_names:
                        analysis_args["clinical_context"] = ", ".join(symptom_names)

                analysis_result = await self._call_tool("analyze_image", analysis_args)

                # Step 2: Find similar cases using RAG + SigLIP
                rag_args = {
                    "symptoms": symptom_names,
                    "image_base64": clean_base64,
                    "top_k": 3
                }
                similar_cases_result = await self._call_tool("find_similar_cases", rag_args)

                self.state.image_captured = True
                print(f"[SOAP Agent] MedGemma: {analysis_result.get('success')}, RAG: {similar_cases_result.get('success')}")

                # DEBUG: Print what MedGemma returned
                if analysis_result.get("success"):
                    print(f"[DEBUG] MedGemma analysis data keys: {analysis_result.get('analysis', {}).keys()}")
                    print(f"[DEBUG] Predictions count: {len(analysis_result.get('analysis', {}).get('predictions', []))}")

                # Format analysis in a human-readable way for the model
                if analysis_result.get("success"):
                    analysis_data = analysis_result.get("analysis", {})
                    visual_desc = analysis_data.get("visual_description", "")
                    predictions = analysis_data.get("predictions", [])
                    critical_findings = analysis_data.get("critical_findings", [])
                    requires_urgent = analysis_data.get("requires_urgent_attention", False)
                    confidence_level = analysis_data.get("confidence_level", "moderate")

                    analysis_summary = f"Image Analysis Results (MedGemma):\n\n"
                    analysis_summary += f"Visual Description: {visual_desc}\n\n"

                    if predictions:
                        analysis_summary += "Possible Conditions:\n"
                        for pred in predictions[:3]:  # Top 3
                            condition = pred.get('condition', 'Unknown')
                            confidence = int(pred.get('confidence', 0) * 100)
                            reasoning = pred.get('reasoning', '')
                            urgency = pred.get('urgency_level', 'routine')
                            is_critical = pred.get('is_critical', False)

                            analysis_summary += f"- {condition} ({confidence}% confidence)\n"
                            if reasoning:
                                analysis_summary += f"  Reasoning: {reasoning}\n"
                            if is_critical:
                                analysis_summary += f"  ⚠️ CRITICAL FINDING - Urgency: {urgency}\n"

                    if critical_findings:
                        analysis_summary += f"\n⚠️ Critical Findings: {', '.join(critical_findings)}\n"

                    if requires_urgent:
                        analysis_summary += f"\n🚨 REQUIRES URGENT MEDICAL ATTENTION\n"

                    analysis_summary += f"\nAnalysis Confidence: {confidence_level}\n"

                    # Add similar cases from RAG
                    if similar_cases_result.get("success"):
                        similar_cases = similar_cases_result.get("similar_cases", [])
                        if similar_cases:
                            analysis_summary += f"\n\nSimilar Cases from Database (found {len(similar_cases)}):\n"
                            for i, case in enumerate(similar_cases, 1):
                                analysis_summary += f"{i}. {case.get('diagnosis')} (similarity: {int(case.get('similarity_score', 0)*100)}%)\n"
                                analysis_summary += f"   Treatment: {case.get('treatment', 'N/A')}\n"
                else:
                    analysis_summary = f"Image analysis failed: {analysis_result.get('error', 'Unknown error')}"

                # Add analysis to conversation
                analysis_prompt = f"Based on the image I uploaded, here's what the dermatology AI analysis found:\n\n{analysis_summary}\n\nPlease explain these findings to me in simple terms and tell me what I should do next."
                messages.append({
                    "role": "user",
                    "content": analysis_prompt
                })

                # DEBUG: Print what we're sending to gpt-oss
                print(f"[DEBUG] Analysis summary length: {len(analysis_summary)} chars")
                print(f"[DEBUG] Analysis summary preview: {analysis_summary[:200]}...")

                # Get final response without tools
                final_call = await self._call_ollama(messages, tools=None)
                final_response = final_call.get("message", {}).get("content", "")
                print(f"[SOAP Agent] Direct analysis complete (response: {len(final_response)} chars)")
                print(f"[DEBUG] gpt-oss response: {final_response}")

            # Call Ollama with tools (only if we don't have a final response from image analysis)
            max_iterations = 5

            if not final_response:
                for iteration in range(max_iterations):
                    print(f"[SOAP Agent] Iteration {iteration + 1}/{max_iterations}")
                    response = await self._call_ollama(messages, tools=self.tools)

                    # Check for tool calls
                    message_data = response.get("message", {})
                    tool_calls = message_data.get("tool_calls", [])

                    print(f"[SOAP Agent] Tool calls: {len(tool_calls)}")
                    if tool_calls:
                        for tc in tool_calls:
                            print(f"[SOAP Agent] - {tc.get('function', {}).get('name')}")

                    if not tool_calls:
                        # No tool calls, this is the final response
                        final_response = message_data.get("content", "")
                        print(f"[SOAP Agent] Final response received (length: {len(final_response)})")
                        break

                    # Execute tool calls
                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        tool_name = function.get("name")
                        arguments = function.get("arguments", {})

                        # Handle analyze_image specially to inject image
                        if tool_name == "analyze_image" and image_base64:
                            arguments["image_base64"] = image_base64
                            if self.state.extracted_symptoms:
                                # Extract symptom names from dicts
                                if isinstance(self.state.extracted_symptoms[0], dict):
                                    symptom_names = [s.get('name', str(s)) for s in self.state.extracted_symptoms if s.get('name')]
                                else:
                                    symptom_names = self.state.extracted_symptoms
                                if symptom_names:
                                    arguments["clinical_context"] = ", ".join(symptom_names)

                        # Call the tool
                        result = await self._call_tool(tool_name, arguments)

                        # Add assistant message with tool call
                        messages.append({
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [tool_call]
                        })

                        # Add tool result
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(result)
                        })

                    # After executing tools, get final response WITHOUT tools to avoid loops
                    # Add a prompt to encourage the model to respond
                    messages.append({
                        "role": "user",
                        "content": "Based on the tool results above, please provide your response to the patient."
                    })
                    print(f"[SOAP Agent] Getting final response after tool execution")
                    final_call = await self._call_ollama(messages, tools=None)
                    final_response = final_call.get("message", {}).get("content", "")
                    print(f"[SOAP Agent] Final response after tools (length: {len(final_response)})")
                    break

            # Update stage based on results
            self._update_stage(message)

            # Store in history
            self.state.message_history.append({"role": "user", "content": message})
            if final_response:
                self.state.message_history.append({"role": "assistant", "content": final_response})

            # Build response
            response_data = {
                "success": True,
                "message": final_response or "Processing...",
                "current_stage": self.state.current_stage,
                "consultation_id": self.state.consultation_id,
                "language": self.state.language,
                "extracted_symptoms": self.state.extracted_symptoms,
                "requires_image": self.state.current_stage == "OBJECTIVE" and not self.state.image_captured,
                "consultation_complete": self.state.current_stage == "COMPLETED"
            }

            # Add optional fields
            if self.state.analysis_results:
                response_data["analysis"] = self.state.analysis_results
            if self.state.similar_cases:
                response_data["similar_cases"] = self.state.similar_cases

            return response_data

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "message": "I encountered an error. Please try again.",
                "current_stage": self.state.current_stage,
                "consultation_id": self.state.consultation_id
            }


def create_soap_agent(
    model: str = "gpt-oss:20b",
    ollama_host: str = "http://localhost:11434"
) -> SOAPAgent:
    """
    Factory function to create SOAP agent.

    Args:
        model: Ollama model name
        ollama_host: Ollama server URL

    Returns:
        Initialized SOAPAgent
    """
    return SOAPAgent(model=model, ollama_host=ollama_host)
