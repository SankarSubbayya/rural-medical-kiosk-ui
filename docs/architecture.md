# Rural Medical AI Kiosk - Architecture Documentation

## System Architecture

### High-Level Overview

```mermaid
graph TB
    subgraph "Frontend - Next.js 16"
        UI[User Interface]
        CS[consultation-screen.tsx]
        CC[camera-capture.tsx]
        KS[kiosk-services.ts]
        API[backend-api.ts]
    end

    subgraph "Backend - FastAPI"
        Router[API Routers]
        AgentRouter[/agent]
        ChatRouter[/chat]
        SpeechRouter[/speech]
        AnalyzeRouter[/analyze]
    end

    subgraph "Google ADK SOAP Agent"
        ADK[Gemini 2.0 Flash Exp]
        State[Consultation State]

        subgraph "SOAP Workflow"
            S1[GREETING]
            S2[SUBJECTIVE]
            S3[OBJECTIVE]
            S4[ASSESSMENT]
            S5[PLAN]
            S6[COMPLETED]
            S1 --> S2 --> S3 --> S4 --> S5 --> S6
        end
    end

    subgraph "MCP Tools - 7 Tools"
        T1[check_message_safety]
        T2[extract_symptoms]
        T3[analyze_image]
        T4[find_similar_cases]
        T5[create_consultation]
        T6[finalize_consultation]
        T7[speech_synthesis]
    end

    subgraph "Backend Services"
        Safety[SafetyService]
        Chat[ChatService]
        MedGemma[MedGemmaService]
        RAG[RAGService]
        Consult[ConsultationService]
        Speech[SpeechService]
    end

    subgraph "External Systems"
        Ollama[Ollama Server<br/>gpt-oss:20b<br/>MedGemma]
        Qdrant[Qdrant Vector DB<br/>SigLIP Embeddings<br/>6,500+ Cases]
        Whisper[Whisper STT]
        gTTS[Google TTS]
    end

    UI --> KS
    KS --> API
    API -->|HTTP/REST| Router
    Router --> AgentRouter
    Router --> ChatRouter
    Router --> SpeechRouter
    Router --> AnalyzeRouter

    AgentRouter --> ADK
    ADK --> State
    ADK -->|Function Calling| T1 & T2 & T3 & T4 & T5 & T6 & T7

    T1 --> Safety
    T2 --> Chat
    T3 --> MedGemma
    T4 --> RAG
    T5 --> Consult
    T6 --> Consult
    T7 --> Speech

    Chat --> Ollama
    MedGemma --> Ollama
    RAG --> Qdrant
    Speech --> Whisper
    Speech --> gTTS

    style ADK fill:#e1f5ff
    style T1 fill:#fff3cd
    style T2 fill:#fff3cd
    style T3 fill:#fff3cd
    style T4 fill:#fff3cd
    style T5 fill:#fff3cd
    style T6 fill:#fff3cd
    style T7 fill:#fff3cd
```

## Component Details

### 1. Frontend (Next.js 16)

**Purpose**: Voice-first UI optimized for low-tech literacy users

**Key Components**:
- **consultation-screen.tsx**: Main chat interface with voice/text input
- **camera-capture.tsx**: Dermatology image capture modal
- **kiosk-services.ts**: Service layer abstracting backend calls
- **backend-api.ts**: TypeScript API client for FastAPI

**Tech Stack**:
- Next.js 16 (App Router)
- TypeScript (strict mode)
- Tailwind CSS 4
- Framer Motion
- Radix UI

### 2. Backend API (FastAPI)

**Purpose**: RESTful API gateway to AI services

**Endpoints**:
- `POST /agent/message` - SOAP Agent conversation
- `GET /agent/consultation/{id}` - Get consultation state
- `POST /chat/message` - Direct chat (legacy)
- `POST /speech/transcribe` - Audio to text (Whisper)
- `POST /speech/synthesize` - Text to audio (gTTS)
- `POST /analyze/image` - Image analysis (MedGemma)
- `POST /analyze/similar` - Find similar cases (RAG)

### 3. Google ADK SOAP Agent

**Purpose**: Intelligent orchestrator for medical consultations

**Key Features**:
- **Automatic Function Calling**: Gemini 2.0 decides when to use MCP tools
- **Multi-turn Context**: Maintains conversation history (10 messages)
- **SOAP Workflow**: Guides consultation through medical stages
- **State Management**: Tracks symptoms, images, analysis results

**Model**: `gemini-2.0-flash-exp`

**System Instruction**:
```
You are a compassionate AI medical assistant specializing in dermatology consultations.

SOAP Framework:
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
```

### 4. MCP Tools (Model Context Protocol)

**Purpose**: Expose backend functionality as callable tools for ADK

| Tool | Purpose | Backend Service |
|------|---------|-----------------|
| `check_message_safety` | Verify message safety, detect diagnosis demands | SafetyService |
| `extract_symptoms` | Extract medical info from patient messages | ChatService (Ollama) |
| `analyze_image` | Analyze dermatology images | MedGemmaService (Ollama) |
| `find_similar_cases` | Search for similar cases using image embeddings | RAGService (Qdrant) |
| `create_consultation` | Create consultation record | ConsultationService |
| `finalize_consultation` | Generate care plan and recommendations | ConsultationService |
| `speech_synthesis` | Text-to-speech for responses | SpeechService (gTTS) |

**Implementation**: Each tool has a `run(operation, **kwargs)` async function that:
1. Validates parameters
2. Calls backend service
3. Returns structured response
4. Updates agent state

### 5. Backend Services

**SafetyService**:
- Medical guardrails
- "Do Not Play Doctor" enforcement
- Critical condition detection
- Language-specific safety rules

**ChatService**:
- Ollama gpt-oss:20b integration
- Symptom extraction
- Medical NLP
- Common sense checks

**MedGemmaService**:
- Ollama MedGemma 4B integration
- Dermatology image analysis
- Visual description generation
- Condition predictions with confidence

**RAGService**:
- Qdrant vector database
- SigLIP embeddings (768-dim)
- Similarity search (cosine distance)
- 6,500+ SCIN dermatology cases

**ConsultationService**:
- In-memory consultation tracking
- SOAP stage management
- Care plan generation

**SpeechService**:
- Whisper STT (multi-language)
- gTTS TTS (5+ languages)
- Audio format conversion

### 6. External Systems

**Ollama** (localhost:11434):
- Local LLM inference
- `gpt-oss:20b` - Chat model
- `medgemma-4b-it:q8` - Medical vision model
- Privacy-preserving (no data leaves device)

**Qdrant** (localhost:6333):
- Vector database
- SigLIP embeddings (google/siglip-base-patch16-224)
- HNSW index for fast similarity search
- 6,500+ SCIN dataset cases

**Whisper**:
- OpenAI Whisper base model
- Multi-language STT (en, hi, ta, te, bn)
- FFmpeg audio processing

**gTTS**:
- Google Text-to-Speech
- Multi-language support
- Streaming audio generation

## Data Flow

### User Message Flow (Text)

```
1. User types message in consultation-screen.tsx
2. kiosk-services.ts calls sendMessageToAI()
3. backend-api.ts sends POST to /agent/message
4. FastAPI agent router receives request
5. SOAP Agent (Gemini 2.0) processes message
6. Agent decides to call MCP tools:
   - check_message_safety (always first)
   - extract_symptoms (if SUBJECTIVE stage)
7. MCP tools execute backend services
8. Agent synthesizes response with context
9. Response flows back to frontend
10. UI displays message + plays TTS audio
```

### Image Analysis Flow

```
1. User captures image in camera-capture.tsx
2. Image converted to base64 JPEG
3. backend-api.ts sends POST to /agent/message with image_base64
4. SOAP Agent receives message + image
5. Agent calls analyze_image MCP tool
6. MedGemmaService sends to Ollama MedGemma
7. Ollama analyzes image (local inference)
8. Agent calls find_similar_cases MCP tool
9. RAGService generates SigLIP embedding
10. Qdrant searches for similar cases
11. Agent synthesizes findings
12. Frontend displays analysis + similar cases
```

### Voice Input Flow

```
1. User presses microphone button
2. Browser MediaRecorder captures audio
3. kiosk-services.ts stops recording
4. Audio blob sent to backend-api.transcribeSpeech()
5. SpeechService processes with Whisper
6. Transcript returned to frontend
7. Transcript sent as text message to agent
8. Agent processes as normal text message
```

## SOAP Workflow Stages

### GREETING
- **Purpose**: Greet patient, obtain consent
- **Agent Behavior**: Warm greeting, explain process
- **User Input**: "Yes", "OK", "Sure" (consent keywords)
- **Transition**: Moves to SUBJECTIVE when consent given

### SUBJECTIVE
- **Purpose**: Gather patient symptoms and history
- **Agent Behavior**:
  - Calls `extract_symptoms` MCP tool
  - Asks follow-up questions
  - Tracks extracted symptoms in state
- **Transition**: Moves to OBJECTIVE when 2+ symptoms collected

### OBJECTIVE
- **Purpose**: Analyze dermatology image
- **Agent Behavior**:
  - Requests image if not provided
  - Calls `analyze_image` MCP tool
  - Calls `find_similar_cases` MCP tool
  - Stores analysis results in state
- **Transition**: Moves to ASSESSMENT when image analyzed

### ASSESSMENT
- **Purpose**: Synthesize findings
- **Agent Behavior**:
  - Reviews symptoms + image analysis + similar cases
  - Generates assessment summary
  - Checks for critical conditions
- **Transition**: Automatically moves to PLAN

### PLAN
- **Purpose**: Generate care recommendations
- **Agent Behavior**:
  - Calls `finalize_consultation` MCP tool
  - Generates patient next steps
  - Recommends tests if needed
  - Sets follow-up timeline
  - Flags urgent cases
- **Transition**: Marks consultation as COMPLETED

### COMPLETED
- **Purpose**: Consultation finished
- **Agent Behavior**: Provides summary and next steps

## Safety Guardrails

### Medical Safety Rules

1. **No Diagnosis**: Agent never provides definitive diagnoses
2. **No Treatment**: Agent doesn't prescribe medications
3. **Professional Referral**: Always recommends doctor for urgent cases
4. **Information Only**: Clarifies it provides information, not medical advice
5. **Consent Required**: Must get explicit consent before proceeding

### Critical Condition Detection

SafetyService flags urgent conditions:
- Melanoma
- Severe burns
- Infected wounds
- Systemic symptoms (fever + rash)
- Rapidly changing lesions

### Message Safety Checks

Detects and redirects:
- Diagnosis demands ("What disease do I have?")
- Treatment requests ("Give me medicine")
- Non-medical queries
- Harmful requests

## Configuration

### Environment Variables

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Backend (.env)**:
```env
# Google ADK (REQUIRED)
GOOGLE_API_KEY=your_api_key_here

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gpt-oss:20b
OLLAMA_MEDGEMMA_MODEL=amsaravi/medgemma-4b-it:q8

# Qdrant
QDRANT_EMBEDDED=true
QDRANT_PATH=./qdrant_data
QDRANT_COLLECTION=scin_dermatology

# Speech
WHISPER_MODEL=base

# Languages
SUPPORTED_LANGUAGES=en,hi,ta,te,bn
```

## Performance Characteristics

### Response Times (Approximate)

- **Text Message (no tools)**: 1-2s (Gemini 2.0)
- **Symptom Extraction**: 2-4s (Ollama gpt-oss:20b)
- **Image Analysis**: 5-8s (Ollama MedGemma)
- **Similar Cases Search**: 0.5-1s (Qdrant)
- **Speech Transcription**: 2-3s (Whisper base)
- **TTS Generation**: 1-2s (gTTS)

### Resource Requirements

**Frontend**:
- Browser with MediaRecorder API
- Camera access for image capture
- Microphone access for voice input

**Backend**:
- 8GB RAM minimum (16GB recommended)
- Ollama models: ~12GB disk space
- Qdrant embeddings: ~2GB disk space
- NVIDIA GPU recommended (optional for Ollama)

## Security Considerations

1. **API Key Security**: GOOGLE_API_KEY in environment variables only
2. **Data Privacy**: Patient data never sent to Google (only agent prompts)
3. **Local Inference**: Ollama keeps medical images local
4. **HTTPS Required**: Production deployment must use HTTPS
5. **CORS**: Configured for frontend origin only
6. **Rate Limiting**: TODO - implement rate limits
7. **Input Validation**: All inputs validated by Pydantic models

## Monitoring & Logging

### Frontend Logging
- `console.log` with `[BackendAPI]` prefix
- Network requests logged to browser console

### Backend Logging
- FastAPI automatic request logging
- Ollama logs in separate terminal
- Qdrant logs to `qdrant_data/` directory

### Agent Logging
- Function calls logged with args/results
- SOAP stage transitions tracked
- Error stack traces in response

## Testing

### Unit Tests
- `backend/tests/mcp/test_mcp_tools.py` - MCP tool tests (19/20 passing)
- `backend/tests/agent/test_soap_agent.py` - Agent tests (1/1 passing)

### Integration Tests
- `backend/tests/integration/test_agent_endpoints.py` - API tests (6/6 passing)

### Manual Testing
1. Start backend with `uvicorn main:app --reload`
2. Visit http://localhost:8000/docs
3. Test `/agent/message` endpoint with sample messages
4. Verify SOAP stage progression

## Deployment

### Development
```bash
# Backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
pnpm dev
```

### Production (TODO)
- Deploy backend to cloud VM (AWS EC2, GCP Compute)
- Deploy frontend to Vercel
- Configure Tailscale for secure backend access
- Set up proper DNS and SSL certificates
- Implement rate limiting and authentication
- Add monitoring (Sentry, DataDog)

## Future Enhancements

1. **Persistent Storage**: Replace in-memory with PostgreSQL
2. **Authentication**: Add user authentication and health records
3. **Multi-modal RAG**: Combine text + image embeddings
4. **Streaming Responses**: Stream agent responses for faster UX
5. **Offline Mode**: PWA with IndexedDB caching
6. **Admin Dashboard**: Monitor consultations and usage metrics
7. **A/B Testing**: Compare Gemini vs Ollama for orchestration
8. **Fine-tuning**: Fine-tune Gemini on medical conversations
