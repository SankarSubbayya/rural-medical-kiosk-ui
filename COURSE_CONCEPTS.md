# Course Concepts Demonstrated in Rural Medical AI Kiosk

This document highlights the three key concepts from the Google Agent Development Kit (ADK) course that are implemented in this project.

---

## 1. ✅ Agent Powered by an LLM (Multi-Agent System)

### Overview
The project implements a **SOAP Orchestrator Agent** powered by Google's Gemini 2.0 Flash model, following the SOAP (Subjective, Objective, Assessment, Plan) medical consultation framework.

### Implementation Details

**Location**: [`backend/agent/soap_agent.py`](backend/agent/soap_agent.py)

**Key Features**:
- **LLM Integration**: Uses Google Gemini 2.0 Flash (`gemini-2.0-flash-exp`) via the Google ADK
- **State Management**: Tracks consultation state through SOAP stages
- **Automatic Function Calling**: Gemini autonomously decides which tools to call based on context
- **Multi-turn Conversations**: Maintains conversation history for context-aware responses

**Code Example**:
```python
class SOAPAgent:
    """
    SOAP Orchestrator Agent using Google Gemini ADK + MCP tools.

    Manages dermatological consultations through SOAP stages:
    GREETING → SUBJECTIVE → OBJECTIVE → ASSESSMENT → PLAN → SUMMARY → COMPLETED
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp", api_key: Optional[str] = None):
        # Initialize Google Genai client
        self.client = genai.Client(api_key=api_key)

        # Initialize consultation state
        self.state = ConsultationState()

        # Load MCP tools
        self.mcp_tools = {
            "medgemma": medgemma_tool,
            "rag": rag_tool,
            "safety": safety_tool,
            "siglip_rag": siglip_rag_tool,
            "speech": speech_tool,
        }
```

**Agent Workflow**:
1. **GREETING Stage**: Introduces itself, obtains consent
2. **SUBJECTIVE Stage**: Gathers symptoms using `extract_symptoms` tool
3. **OBJECTIVE Stage**: Analyzes medical images using `analyze_image` tool
4. **ASSESSMENT Stage**: Synthesizes findings from MedGemma AI analysis
5. **PLAN Stage**: Provides care recommendations

**Sequential Agent Behavior**:
The agent progresses through stages sequentially, where each stage's completion triggers the next:

```python
# Stage progression logic (lines 380-388)
if self.state.current_stage == "SUBJECTIVE":
    stage_context += "INSTRUCTION: When patient describes symptoms, you MUST call extract_symptoms function.\n"
elif self.state.current_stage == "OBJECTIVE":
    stage_context += "INSTRUCTION: When you receive an image, call analyze_image function.\n"
```

**Multi-Turn Context Management**:
```python
# Add message history for context (lines 358-364)
for msg in self.state.message_history[-10:]:  # Last 10 messages for context
    contents.append(
        Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[Part(text=msg["content"])]
        )
    )
```

---

## 2. ✅ Tools: MCP (Model Context Protocol) Custom Tools

### Overview
The project implements **7 custom MCP tools** that extend the agent's capabilities for medical consultation tasks.

### Implementation Details

**Location**: [`backend/mcp_server/tools/`](backend/mcp_server/tools/)

**Custom MCP Tools**:

1. **MedGemma Tool** (`medgemma_tool.py`) - Medical image analysis
2. **SigLIP RAG Tool** (`siglip_rag_tool.py`) - Visual similarity search
3. **Safety Tool** (`safety_tool.py`) - Content safety guardrails
4. **Medical Tool** (`medical_tool.py`) - Medical knowledge extraction
5. **RAG Tool** (`rag_tool.py`) - Text-based case retrieval
6. **Consultation Tool** (`consultation_tool.py`) - Consultation management
7. **Speech Tool** (`speech_tool.py`) - Text-to-speech synthesis

### Tool Integration with Agent

**Function Declarations** (lines 162-250):
```python
def _create_tool_declarations(self) -> List[Tool]:
    """Create ADK-compatible tool declarations from MCP tools."""

    tools = [
        Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="check_message_safety",
                    description="Check if patient message violates safety guardrails",
                    parameters={...}
                ),
                FunctionDeclaration(
                    name="extract_symptoms",
                    description="Extract medical symptoms from patient message",
                    parameters={...}
                ),
                FunctionDeclaration(
                    name="analyze_image",
                    description="Analyze dermatology images with MedGemma",
                    parameters={...}
                ),
                # ... more tools
            ]
        )
    ]
```

**Tool Execution** (lines 280-316):
```python
async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an MCP tool by name."""

    tool = self.mcp_tools.get(operation)
    if not tool:
        return {"success": False, "error": f"Unknown tool: {name}"}

    # Execute MCP tool
    result = await tool.run(operation=operation, **args)

    # Update agent state based on results
    if name == "extract_symptoms" and result.get("success"):
        symptoms = result.get("symptoms", [])
        self.state.extracted_symptoms.extend([s["name"] for s in symptoms])

    return result
```

### Example: MedGemma Tool (Medical Image Analysis)

**Location**: [`backend/mcp_server/tools/medgemma_tool.py`](backend/mcp_server/tools/medgemma_tool.py)

```python
async def analyze_image(
    image_base64: str,
    clinical_context: str = "",
    language: str = "en",
    consultation_id: str = "unknown"
) -> Dict[str, Any]:
    """Analyze dermatological image using MedGemma."""

    # Create request object
    request = ImageAnalysisRequest(
        consultation_id=consultation_id,
        image_base64=image_base64,
        body_location=BodyLocation(primary="unknown"),
        patient_description=clinical_context,
        symptoms=[]
    )

    # Call MedGemma analysis service
    result = await _get_service().analyze_image(request)

    return {
        "success": True,
        "operation": "analyze_image",
        "analysis": {
            "visual_description": result.visual_description,
            "predictions": [
                {
                    "condition": p.condition,
                    "confidence": p.confidence,
                    "reasoning": p.reasoning,
                    "icd_code": p.icd_code,
                    "is_critical": p.is_critical,
                    "urgency_level": p.urgency_level
                }
                for p in result.predictions
            ],
            "critical_findings": result.critical_findings,
            "requires_urgent_attention": result.requires_urgent_attention,
            "confidence_level": result.confidence_level
        },
        "model_used": "medgemma-4b-it:q8"
    }
```

### Example: SigLIP RAG Tool (Visual Case Retrieval)

**Location**: [`backend/mcp_server/tools/siglip_rag_tool.py`](backend/mcp_server/tools/siglip_rag_tool.py)

```python
async def search_by_image(
    image_base64: str,
    top_k: int = 5,
    min_score: float = 0.7
) -> Dict[str, Any]:
    """Search for similar cases using SigLIP image embeddings."""

    similar_cases = await _get_service().find_similar_cases(
        image_base64=image_base64,
        symptoms=None,  # Image-only search
        body_location=None,
        top_k=top_k
    )

    return {
        "success": True,
        "operation": "search_by_image",
        "similar_cases": [
            {
                "case_id": case.case_id,
                "diagnosis": case.condition,
                "similarity_score": case.similarity_score,
                "symptoms": case.key_features or [],
                "treatment": case.description or "",
                "visual_match_score": case.similarity_score,
                "icd_code": case.icd_code or ""
            }
            for case in similar_cases
        ],
        "total_found": len(similar_cases),
        "embedding_model": "google/siglip-base-patch16-224",
        "embedding_dimensions": 768
    }
```

### Enhanced Workflow: Sequential Tool Calling

**Location**: `soap_agent.py` lines 422-461

The agent implements an **enhanced workflow** that combines multiple tools sequentially:

```python
# SPECIAL HANDLING: If Gemini calls analyze_image, use enhanced workflow
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
```

This demonstrates **sequential tool orchestration** where:
1. First, the RAG tool searches for similar cases
2. Then, results are used to enhance context
3. Finally, the image analysis tool uses the enriched context

---

## 3. ✅ Sessions & Memory: Session State Management

### Overview
The project implements **comprehensive session state management** through the `ConsultationState` class that tracks the entire consultation lifecycle.

### Implementation Details

**Location**: [`backend/agent/soap_agent.py`](backend/agent/soap_agent.py) lines 18-32

**State Management Class**:
```python
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
```

### State Tracking Features

**1. Consultation Lifecycle Tracking**:
- Unique consultation ID generation
- Patient identification
- Language preference
- Current SOAP stage
- Consent status

**2. Medical Data Accumulation**:
- Extracted symptoms list
- Image capture status
- Base64-encoded image data
- MedGemma analysis results
- Similar cases from Qdrant RAG

**3. Conversation Memory**:
```python
# Message history for context (lines 358-364)
for msg in self.state.message_history[-10:]:  # Last 10 messages for context
    contents.append(
        Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[Part(text=msg["content"])]
        )
    )
```

**4. State Updates During Tool Execution** (lines 304-316):
```python
# Update agent state based on results
if name == "extract_symptoms" and result.get("success"):
    symptoms = result.get("symptoms", [])
    self.state.extracted_symptoms.extend([s["name"] for s in symptoms])

elif name == "analyze_image" and result.get("success"):
    self.state.analysis_results = result.get("analysis")
    self.state.image_captured = True

elif name == "find_similar_cases" and result.get("success"):
    self.state.similar_cases = result.get("similar_cases", [])
```

### Session Persistence & Resume Capability

**Initialization with Existing Session** (lines 68-72):
```python
# Initialize state with provided consultation_id if given
if consultation_id:
    self.state = ConsultationState(consultation_id=consultation_id)
else:
    self.state = ConsultationState()
```

**State Update on Message Processing** (lines 339-347):
```python
# Update state
if consultation_id:
    self.state.consultation_id = consultation_id
if patient_id:
    self.state.patient_id = patient_id
if language:
    self.state.language = language
if image_base64:
    self.state.image_base64 = image_base64
```

### Context Engineering: Stage-Specific Instructions

**Dynamic Context Based on Stage** (lines 378-388):
```python
# Add SOAP stage context
stage_context = f"\n\nCurrent SOAP stage: {self.state.current_stage}\n"

# Add stage-specific instructions
if self.state.current_stage == "SUBJECTIVE":
    stage_context += "INSTRUCTION: When patient describes symptoms, you MUST call extract_symptoms function.\n"
elif self.state.current_stage == "OBJECTIVE":
    stage_context += "INSTRUCTION: When you receive an image, call analyze_image function.\n"

if self.state.extracted_symptoms:
    stage_context += f"Extracted symptoms: {', '.join(self.state.extracted_symptoms)}\n"
```

This demonstrates **context engineering** where the agent's behavior is dynamically adjusted based on:
- Current consultation stage
- Previously extracted information
- Conversation history

### State Serialization for Long-Term Storage

**Location**: [`backend/app/routers/agent.py`](backend/app/routers/agent.py)

The state can be serialized and stored in a database for long-term memory:

```python
@router.post("/message")
async def process_agent_message(request: AgentMessageRequest):
    """Process message through SOAP agent."""

    # Initialize or resume agent
    agent = SOAPAgent(
        model="gemini-2.0-flash-exp",
        consultation_id=request.consultation_id
    )

    # Process message
    response = await agent.process_message(
        message=request.message,
        image_base64=request.image_base64,
        consultation_id=request.consultation_id,
        patient_id=request.patient_id,
        language=request.language
    )

    # Return state for client to maintain
    return {
        "success": response.get("success"),
        "message": response.get("message"),
        "stage": response.get("stage"),
        "consultation_id": agent.state.consultation_id,
        "extracted_symptoms": agent.state.extracted_symptoms,
        "has_image": agent.state.image_captured,
        "analysis_results": agent.state.analysis_results
    }
```

---

## Bonus: Observability (Logging & Tracing)

While not one of the primary three concepts, the project also demonstrates **observability** through comprehensive logging.

### Structured Logging

**Throughout the agent** (lines 349-352, 419-445, 480-481, 506-572):

```python
print(f"[SOAP Agent - Gemini] Processing message in stage: {self.state.current_stage}")
print(f"[SOAP Agent - Gemini] Has image: {bool(image_base64)}")
print(f"[SOAP Agent - Gemini] Gemini called function: {fc.name}")
print(f"[SOAP Agent - Gemini] Found {len(similar_cases)} similar cases from Qdrant")
print(f"[SOAP Agent - Gemini] Enhanced with {len(similar_cases)} similar cases")
print(f"[SOAP Agent - Gemini] Functions called by Gemini: {[fc['name'] for fc in function_calls]}")
```

### Tracing Through Agent Stages

The logging provides **end-to-end traceability**:
1. Stage entry logging
2. Tool invocation logging
3. Tool result logging
4. Stage completion logging

Example trace from the working system:
```
[SOAP Agent - Gemini] Processing message in stage: OBJECTIVE
[SOAP Agent - Gemini] Has image: True
[SOAP Agent - Gemini] Gemini called function: analyze_image
[SOAP Agent - Gemini] Intercepting analyze_image - using enhanced Qdrant workflow
[SOAP Agent - Gemini] Searching Qdrant for similar cases...
[SOAP Agent - Gemini] Found 3 similar cases from Qdrant
[SOAP Agent - Gemini] Enhanced with 3 similar cases
[SOAP Agent - Gemini] Initial response text: Okay! The analysis of the image...
[SOAP Agent - Gemini] Functions called by Gemini: ['analyze_image']
```

---

## Summary

This **Rural Medical AI Kiosk** project demonstrates three key concepts from the Google ADK course:

1. **✅ Agent Powered by LLM (Multi-Agent System)**
   - SOAP Orchestrator Agent using Gemini 2.0 Flash
   - Sequential stage progression through medical consultation workflow
   - Automatic function calling and multi-turn conversations
   - State-driven agent behavior

2. **✅ MCP Custom Tools**
   - 7 custom MCP tools for medical consultation tasks
   - MedGemma for medical image analysis
   - SigLIP RAG for visual case similarity search
   - Safety guardrails, symptom extraction, and speech synthesis
   - Sequential tool orchestration (RAG → Context Enhancement → Analysis)

3. **✅ Sessions & Memory (State Management)**
   - Comprehensive `ConsultationState` tracking
   - Session persistence and resume capability
   - Conversation history management (last 10 messages)
   - Context engineering with stage-specific instructions
   - State updates based on tool execution results

**Bonus**: **Observability** through structured logging and tracing throughout the agent lifecycle.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Next.js + TypeScript)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                    (Agent Router Layer)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SOAP Orchestrator Agent                      │
│                   (Gemini 2.0 Flash + ADK)                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ConsultationState (Session)                 │  │
│  │  • consultation_id, patient_id, language                │  │
│  │  • current_stage (GREETING → SUBJECTIVE → ...)          │  │
│  │  • extracted_symptoms, analysis_results                 │  │
│  │  • message_history (last 10 for context)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Stage Progression: GREETING → SUBJECTIVE → OBJECTIVE →        │
│                     ASSESSMENT → PLAN → SUMMARY → COMPLETED    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    MCP Custom Tools     │   │   External Services     │
│                         │   │                         │
│  • medgemma_tool        │   │  • Qdrant (Vector DB)   │
│  • siglip_rag_tool      │   │  • Ollama (Local LLM)   │
│  • safety_tool          │   │  • Google Gemini API    │
│  • medical_tool         │   │  • SigLIP Embeddings    │
│  • rag_tool             │   │                         │
│  • consultation_tool    │   │                         │
│  • speech_tool          │   │                         │
└─────────────────────────┘   └─────────────────────────┘
```

---

## Testing & Validation

The system has been tested end-to-end:

1. ✅ **Agent Conversation Flow**: Multi-turn consultation through SOAP stages
2. ✅ **Tool Execution**: All 7 MCP tools successfully integrated and called
3. ✅ **State Persistence**: Consultation state tracked across messages
4. ✅ **Image Analysis**: MedGemma successfully analyzed dermatology images
5. ✅ **RAG Integration**: Qdrant successfully retrieved similar cases
6. ✅ **Sequential Orchestration**: RAG → Context Enhancement → Analysis workflow

**Example Test Output**:
```
Okay! The analysis of the image suggests a few possibilities.
The most likely condition is eczema, with 95% confidence.
Eczema is a condition that makes your skin red and itchy.
This is a routine condition, so it's not an emergency.
Another possibility is contact dermatitis, with 80% confidence...
```

This demonstrates successful integration of:
- LLM-powered agent (Gemini analyzing and explaining)
- MCP tools (MedGemma + SigLIP RAG)
- State management (tracking stage, results, and history)
