# Agent Features Documentation

## Three Key Course Concepts Implemented

This document provides a technical overview of the three key concepts from the Google Agent Development Kit (ADK) course that are implemented in this project, with direct code references.

---

## Feature 1: Agent Powered by LLM (Multi-Agent System)

### Overview
The SOAP Orchestrator Agent is an LLM-powered agent using Google Gemini 2.0 Flash that autonomously manages medical consultations through the SOAP (Subjective, Objective, Assessment, Plan) clinical framework.

### Code Location
**Primary File**: [`backend/agent/soap_agent.py`](backend/agent/soap_agent.py)

### Key Implementation Details

#### 1.1 LLM Client Initialization (Lines 163-174)
```python
# =======================================================================
# LLM CLIENT INITIALIZATION (Course Concept #1: Agent Powered by LLM)
# The Gemini client is the reasoning engine for this agent
# =======================================================================
api_key = api_key or os.getenv("GOOGLE_API_KEY")
self.client = genai.Client(api_key=api_key)
```

#### 1.2 Automatic Function Calling (Lines 399-408)
The agent uses Gemini's automatic function calling to decide which tools to invoke:
```python
response = self.client.models.generate_content(
    model=self.model_name,
    contents=contents,
    config={
        "system_instruction": self.system_instruction + stage_context,
        "tools": self.tools,  # 7 MCP tools available for autonomous selection
        "tool_config": tool_config,
        "temperature": 0.7,
    }
)
```

#### 1.3 Sequential Agent Behavior - SOAP Stages (Lines 109-110)
```python
# SOAP Stage Progression (Sequential Agent Behavior):
#     GREETING → SUBJECTIVE → OBJECTIVE → ASSESSMENT → PLAN → SUMMARY → COMPLETED
```

#### 1.4 Context-Aware Processing (Lines 358-376)
```python
# Add message history for context retention
for msg in self.state.message_history[-10:]:  # Last 10 messages
    contents.append(
        Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[Part(text=msg["content"])]
        )
    )
```

### Agent Capabilities Demonstrated
- **Autonomous Tool Selection**: Gemini decides when to call `extract_symptoms`, `analyze_image`, etc.
- **Multi-turn Conversations**: Maintains conversation history for context-aware responses
- **Stage-driven Behavior**: Different instructions and actions per SOAP stage
- **Safety Guardrails**: Built-in safety checks via `check_message_safety` tool

---

## Feature 2: Custom MCP Tools

### Overview
The project implements 7 custom MCP (Model Context Protocol) tools that extend the agent's capabilities for medical consultation tasks.

### Code Location
**Tool Directory**: [`backend/mcp_server/tools/`](backend/mcp_server/tools/)

### Tool Registry (Lines 190-200 in soap_agent.py)
```python
# Registry of MCP tools available to the agent
self.mcp_tools = {
    "consultation": consultation_tool,  # Session management
    "medical": medical_tool,            # Medical NER
    "medgemma": medgemma_tool,          # Image analysis
    "rag": rag_tool,                    # Text retrieval
    "safety": safety_tool,              # Safety guardrails
    "siglip_rag": siglip_rag_tool,      # Visual RAG
    "speech": speech_tool,              # TTS
}
```

### Key Tool Implementations

#### 2.1 MedGemma Tool (Medical Image Analysis)
**File**: [`backend/mcp_server/tools/medgemma_tool.py`](backend/mcp_server/tools/medgemma_tool.py)

```python
async def analyze_image(
    image_base64: str,
    clinical_context: str = "",
    language: str = "en",
    consultation_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Analyze dermatological image using MedGemma vision model.

    Returns structured predictions with:
    - visual_description: What the model sees
    - predictions: Conditions with confidence scores
    - critical_findings: Urgent findings
    - requires_urgent_attention: Triage flag
    """
```

#### 2.2 SigLIP RAG Tool (Visual Case Retrieval)
**File**: [`backend/mcp_server/tools/siglip_rag_tool.py`](backend/mcp_server/tools/siglip_rag_tool.py)

```python
async def search_by_image(
    image_base64: str,
    top_k: int = 5,
    min_score: float = 0.7
) -> Dict[str, Any]:
    """
    Search for similar cases using SigLIP image embeddings.

    Pipeline:
    Input Image → SigLIP Embedding (768-dim) → Qdrant Search → Similar Cases
    """
```

### MCP Tool Pattern
All tools follow the MCP standard interface:
```python
async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point.

    Args:
        operation: Operation name (e.g., "analyze_image", "search_by_image")
        **kwargs: Operation-specific parameters

    Returns:
        Dict with 'success' boolean and operation results
    """
```

### Sequential Tool Orchestration (Lines 422-461 in soap_agent.py)
The agent implements multi-step tool orchestration:
```python
# STEP 1: Search Qdrant for similar cases
similar_cases_result = await self._execute_tool("find_similar_cases", {
    "image_base64": image_base64,
    "top_k": 3,
    "min_score": 0.7
})

# STEP 2: Build enhanced clinical context from similar cases
if similar_cases:
    clinical_context += "\n\nSimilar Historical Cases:\n"
    for i, case in enumerate(similar_cases[:3], 1):
        clinical_context += f"{i}. {case.get('diagnosis')} ({case.get('similarity_score'):.0%})\n"

# STEP 3: Call analyze_image with enhanced context
result = await self._execute_tool("analyze_image", {
    "image_base64": image_base64,
    "clinical_context": clinical_context,
    "language": self.state.language
})
```

---

## Feature 3: Sessions & Memory (State Management)

### Overview
The project implements comprehensive session state management through the `ConsultationState` class, enabling persistent consultations with accumulated context.

### Code Location
**Primary File**: [`backend/agent/soap_agent.py`](backend/agent/soap_agent.py) (Lines 49-90)

### ConsultationState Class
```python
@dataclass
class ConsultationState:
    """
    Tracks state of active consultation session.

    Implements SESSION STATE MANAGEMENT with:
    1. Session Identity: consultation_id, patient_id
    2. Workflow State: current_stage (SOAP progression)
    3. Accumulated Data: symptoms, analysis_results
    4. Conversation Memory: message_history
    """
    consultation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""
    language: str = "en"
    current_stage: str = "GREETING"  # SOAP stage progression
    consent_given: bool = False
    extracted_symptoms: List[str] = field(default_factory=list)
    image_captured: bool = False
    image_base64: Optional[str] = None
    analysis_results: Optional[Dict] = None
    similar_cases: List[Dict] = field(default_factory=list)
    message_history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### State Management Features

#### 3.1 Session Persistence (Lines 152-161)
```python
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
```

#### 3.2 State Updates After Tool Execution (Lines 304-316)
```python
# Update agent state based on tool results
if name == "extract_symptoms" and result.get("success"):
    symptoms = result.get("symptoms", [])
    self.state.extracted_symptoms.extend([s["name"] for s in symptoms])

elif name == "analyze_image" and result.get("success"):
    self.state.analysis_results = result.get("analysis")
    self.state.image_captured = True

elif name == "find_similar_cases" and result.get("success"):
    self.state.similar_cases = result.get("similar_cases", [])
```

#### 3.3 Context Engineering (Lines 378-388)
Dynamic context injection based on current state:
```python
# Add SOAP stage context
stage_context = f"\n\nCurrent SOAP stage: {self.state.current_stage}\n"

# Stage-specific instructions
if self.state.current_stage == "SUBJECTIVE":
    stage_context += "INSTRUCTION: Call extract_symptoms when patient describes symptoms.\n"
elif self.state.current_stage == "OBJECTIVE":
    stage_context += "INSTRUCTION: Call analyze_image when you receive an image.\n"

# Include accumulated symptoms for context
if self.state.extracted_symptoms:
    stage_context += f"Extracted symptoms: {', '.join(self.state.extracted_symptoms)}\n"
```

#### 3.4 Conversation Memory (Lines 358-364)
```python
# Add message history for multi-turn context (last 10 messages)
for msg in self.state.message_history[-10:]:
    contents.append(
        Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[Part(text=msg["content"])]
        )
    )
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FEATURE 1: LLM-POWERED AGENT                   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    SOAP Orchestrator Agent                      │  │
│   │                  (Google Gemini 2.0 Flash)                      │  │
│   │                                                                 │  │
│   │  • Autonomous tool selection via function calling               │  │
│   │  • Sequential stage progression (SOAP workflow)                 │  │
│   │  • Context-aware response generation                            │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FEATURE 2: CUSTOM MCP TOOLS                        │
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ medgemma_    │ │ siglip_rag_  │ │ safety_      │ │ medical_     │   │
│  │ tool         │ │ tool         │ │ tool         │ │ tool         │   │
│  │              │ │              │ │              │ │              │   │
│  │ Image        │ │ Visual RAG   │ │ Content      │ │ Symptom      │   │
│  │ Analysis     │ │ (Qdrant)     │ │ Safety       │ │ Extraction   │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │ consultation_│ │ rag_         │ │ speech_      │                    │
│  │ tool         │ │ tool         │ │ tool         │                    │
│  │              │ │              │ │              │                    │
│  │ Session      │ │ Text RAG     │ │ TTS          │                    │
│  │ Management   │ │              │ │ Synthesis    │                    │
│  └──────────────┘ └──────────────┘ └──────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   FEATURE 3: SESSIONS & MEMORY                          │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    ConsultationState                            │  │
│   │                                                                 │  │
│   │  Session Identity    │ Workflow State  │ Accumulated Data      │  │
│   │  ─────────────────   │ ──────────────  │ ─────────────────     │  │
│   │  • consultation_id   │ • current_stage │ • extracted_symptoms  │  │
│   │  • patient_id        │ • consent_given │ • analysis_results    │  │
│   │  • language          │                 │ • similar_cases       │  │
│   │                      │                 │ • message_history     │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Code Quality Highlights

### Comments and Documentation
All key files include:
- **Module-level docstrings** explaining course concepts
- **Function docstrings** with Args/Returns documentation
- **Inline comments** for complex logic
- **Section separators** for code organization

### Example from soap_agent.py
```python
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
```

### Example from medgemma_tool.py
```python
"""
MCP Tool: Medical Image Analysis (MedGemma)

==============================================================================
COURSE CONCEPT #2: CUSTOM TOOLS (MCP - Model Context Protocol)
==============================================================================

This module implements a CUSTOM MCP TOOL for medical image analysis using the
MedGemma 4B vision model. It demonstrates:

1. MCP Tool Pattern: Standard interface with `run(operation, **kwargs)` entry point
2. Lazy Service Initialization: Efficient resource management
3. Structured Output: Consistent response format for agent consumption
4. Multi-Modal Processing: Handles image data (base64) for vision analysis
"""
```

---

## Testing the Features

### Running the Backend
```bash
cd backend
uv pip install -r requirements.txt
uv run python main.py
```

### Testing Agent Conversation
```bash
curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a red rash on my arm", "language": "en"}'
```

### Expected Output Demonstrating All Features
```
[SOAP Agent - Gemini] Processing message in stage: SUBJECTIVE
[SOAP Agent - Gemini] Has image: False
[SOAP Agent - Gemini] Gemini called function: check_message_safety
[SOAP Agent - Gemini] Gemini called function: extract_symptoms
[SOAP Agent - Gemini] Functions called by Gemini: ['check_message_safety', 'extract_symptoms']
```

This demonstrates:
- **Feature 1**: Agent processing message and calling functions autonomously
- **Feature 2**: MCP tools (safety, symptoms) being invoked
- **Feature 3**: State tracking via `current_stage` and accumulated symptoms

---

## Summary

| Feature | Concept | Implementation |
|---------|---------|----------------|
| **1** | Agent Powered by LLM | SOAPAgent class with Gemini 2.0 Flash |
| **2** | Custom MCP Tools | 7 tools in `mcp_server/tools/` |
| **3** | Sessions & Memory | ConsultationState dataclass |

All three features work together to create a coherent, intelligent medical consultation agent that can:
1. **Reason** about patient symptoms using Gemini (Feature 1)
2. **Analyze** images and retrieve similar cases using custom tools (Feature 2)
3. **Remember** conversation history and accumulated data (Feature 3)
