# Agentic Health - Rural Medical AI Kiosk

A highly intuitive, empathetic UI for a rural medical AI kiosk designed to bridge the gap between advanced technology and low-tech literacy users.

## Features

- **Handshake (Login)**: QR code scanning or phone number entry with large dial pad
- **Consultation (Chat)**: Voice-first AI interaction with **Google ADK SOAP Agent** for intelligent medical conversations
- **Camera Capture**: Dermatology image capture for AI analysis using MedGemma
- **Health Passport**: Visual timeline of health records and next steps
- **RAG Similarity Search**: Find similar cases from 6,500+ dermatology images using SigLIP embeddings
- **Intelligent Agent**: Google's Agent Development Kit with automatic function calling for SOAP workflow
- **Report Generation**: Patient-friendly summaries and physician SOAP reports with PDF export

---

## Files to Customize

### Core Services (✅ Fully Integrated with Backend)

| File | Purpose | Status |
|------|---------|--------|
| [lib/backend-api.ts](lib/backend-api.ts) | **Backend API client** | ✅ Complete - FastAPI integration |
| [lib/kiosk-services.ts](lib/kiosk-services.ts) | **Service layer** | ✅ Integrated - Uses backend for AI/medical services |

**Integration Status:**

✅ **Completed Integrations:**
- `sendMessageToAI()` - Uses **Google ADK SOAP Agent** with Gemini 2.0 + MCP tools
- `analyzeDermatologyImage()` - Uses MedGemma + SigLIP RAG via MCP tools
- `startVoiceRecognition()` - Uses Whisper for transcription
- `textToSpeech()` - Uses gTTS for voice output
- `generateAndDownloadPDF()` - Generates and downloads PDF reports (patient/physician)
- `getTextReport()` - Fetches formatted text reports for viewing

⚠️ **Still Placeholder (Customize as needed):**
- `authenticateWithQR()` - QR code authentication
- `authenticateWithPhone()` - Phone number + OTP authentication
- `fetchHealthHistory()` - Patient health records retrieval

---

### UI Components

#### Login Flow

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/welcome-screen.tsx` | Landing page with login options | Modify welcome text, add/remove login methods |
| `components/kiosk/dial-pad.tsx` | Phone number input | Change button sizes, colors, validation rules |
| `components/kiosk/diagnostic-flow.tsx` | 4-step visual guide | Update step descriptions, illustrations |

#### Consultation Flow

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/consultation-screen.tsx` | Main chat interface | Modify AI prompts, button labels, layout |
| `components/kiosk/ai-avatar.tsx` | Animated AI persona header | Change avatar appearance, status messages |
| `components/kiosk/camera-capture.tsx` | Photo capture modal | Adjust camera settings, upload limits |
| `components/kiosk/report-viewer.tsx` | Report display modal | Customize formatting, styling, download behavior |

#### Health Records

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/health-passport-screen.tsx` | Health timeline view | Customize event types, icons, colors |

#### Branding

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/agentic-health-logo.tsx` | Logo component | Replace with your brand logo |
| `components/kiosk/kiosk-navigation.tsx` | Bottom navigation bar | Add/remove tabs, change icons |

---

### Styling & Configuration

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `app/globals.css` | Global styles & theme | Colors, fonts, design tokens |
| `app/layout.tsx` | Root layout & fonts | Change font family, metadata |
| `app/page.tsx` | Main app container | Modify screen flow, add new screens |

---

## Environment Variables

Add these to your `.env.local` file:

\`\`\`env
# Backend API URL (required)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Optional: Authentication (Supabase example)
# NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
\`\`\`

**Important**: The frontend now connects to the FastAPI backend for all AI/medical services (chat, image analysis, voice). The backend uses Google ADK with Gemini 2.0 for intelligent agent orchestration.

---

## Quick Start Integration Guide

### Step 1: Configure Backend Environment

First, set up your environment variables:

\`\`\`bash
cd backend
cp .env.example .env
\`\`\`

Edit `backend/.env` and add your Google API key:

\`\`\`env
# Required for Google ADK SOAP Agent
GOOGLE_API_KEY=your_google_api_key_here
\`\`\`

Get your Google API key at: https://aistudio.google.com/apikey

### Step 2: Start Backend Server

\`\`\`bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Start Ollama server (in separate terminal) - for MedGemma vision model
ollama serve

# Start FastAPI backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

Verify backend is running: http://localhost:8000/docs

### Step 3: Configure Frontend

Create `.env.local` file:

\`\`\`bash
cp .env.local.example .env.local
\`\`\`

Edit `.env.local`:

\`\`\`env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
\`\`\`

### Step 4: Start Frontend

\`\`\`bash
pnpm install
pnpm dev
\`\`\`

Open http://localhost:3000

### Step 5: Test Integration

The frontend is now fully integrated with the backend:

- **AI Chat**: Uses **Google ADK SOAP Agent** (Gemini 2.0) via `/agent/message`
- **Image Analysis**: Uses MedGemma + SigLIP RAG via MCP tools
- **Voice Input**: Uses Whisper via `/speech/transcribe`
- **Voice Output**: Uses gTTS via `/speech/synthesize`
- **Similar Cases**: Uses Qdrant vector search via SigLIP embeddings
- **Reports**: Patient/physician SOAP reports via `/report/patient` and `/report/physician`
- **PDF Export**: PDF generation via `/report/{consultation_id}/pdf`

All integration code is in:
- [lib/backend-api.ts](lib/backend-api.ts) - API client
- [lib/kiosk-services.ts](lib/kiosk-services.ts) - Service layer
- [backend/agent/soap_agent.py](backend/agent/soap_agent.py) - Google ADK SOAP Agent
- [backend/mcp_server/tools/](backend/mcp_server/tools/) - MCP tools (7 tools)

### Step 6: Test Report Generation

For testing report functionality without completing a full consultation:

```bash
# Create a sample consultation with complete SOAP data
curl -X POST http://localhost:8000/test/create-sample-consultation

# Returns: {"consultation_id": "uuid-here", ...}
```

Use the returned consultation ID to test:
- **View Report**: Click the report button (top-right) in the consultation screen
- **Download PDF**: Choose Patient Summary or Physician Report and click Download
- **View Formatted Report**: Click View to see the report in a modal

The test endpoint creates a complete dermatology consultation with:
- Patient symptoms (red, itchy rash)
- Captured images
- Differential diagnoses with ICD-10 codes
- Treatment plan and self-care instructions

---

## Database Schema (Suggested)

If using Supabase or PostgreSQL:

\`\`\`sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_number TEXT UNIQUE,
  qr_code_id TEXT UNIQUE,
  name TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Health records table
CREATE TABLE health_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  type TEXT, -- 'checkup', 'medication', 'test', 'vaccination'
  title TEXT,
  description TEXT,
  date DATE,
  status TEXT, -- 'completed', 'pending', 'upcoming'
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Consultation history
CREATE TABLE consultations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  messages JSONB,
  images TEXT[],
  ai_diagnosis TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

---

## Folder Structure

\`\`\`
├── app/                     # Next.js 16 frontend
│   ├── globals.css          # Theme & styling
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Main app entry
├── components/
│   └── kiosk/
│       ├── welcome-screen.tsx
│       ├── dial-pad.tsx
│       ├── diagnostic-flow.tsx
│       ├── consultation-screen.tsx
│       ├── ai-avatar.tsx
│       ├── camera-capture.tsx
│       ├── report-viewer.tsx
│       ├── health-passport-screen.tsx
│       ├── agentic-health-logo.tsx
│       └── kiosk-navigation.tsx
├── lib/
│   └── kiosk-services.ts    # ** MAIN INTEGRATION FILE **
├── backend/                 # FastAPI Python backend
│   ├── main.py              # Backend server
│   ├── app/                 # Services, models, routers
│   └── scripts/             # SigLIP embedding & SCIN ingestion
└── README.md
\`\`\`

## Backend Architecture

> 📊 **Detailed Documentation**: See [docs/architecture.md](docs/architecture.md) for comprehensive architecture documentation with Mermaid diagrams, data flows, and component details.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Next.js Frontend (UI)                      │
│  • consultation-screen.tsx  • camera-capture.tsx                │
│  • kiosk-services.ts  • backend-api.ts                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST API
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Server                        │
│  Routers: /agent, /chat, /speech, /analyze, /report, /test    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│         Google ADK SOAP Orchestrator Agent (NEW!)              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Gemini 2.0 Flash Exp (Google ADK)                        │ │
│  │ • Automatic function calling                             │ │
│  │ • Multi-turn conversation context                        │ │
│  │ • SOAP workflow: GREETING → SUBJECTIVE → OBJECTIVE →     │ │
│  │                  ASSESSMENT → PLAN → COMPLETED            │ │
│  └───────────────────────┬──────────────────────────────────┘ │
│                          │                                     │
│                          │ Calls MCP Tools                     │
│                          ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              MCP Tools (7 Tools)                         │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ 1. check_message_safety   → SafetyService               │ │
│  │ 2. extract_symptoms        → ChatService (Ollama)       │ │
│  │ 3. analyze_image           → MedGemma (Ollama)          │ │
│  │ 4. find_similar_cases      → SigLIP + Qdrant            │ │
│  │ 5. create_consultation     → ConsultationService        │ │
│  │ 6. finalize_consultation   → PlanService                │ │
│  │ 7. speech_synthesis        → SpeechService (gTTS)       │ │
│  └───────────────────────┬──────────────────────────────────┘ │
└──────────────────────────┼──────────────────────────────────────┘
                           │
           ┌───────────────┴─────────────────┐
           ▼                                 ▼
┌─────────────────────────┐    ┌────────────────────────────┐
│   Ollama (Local LLM)    │    │  Qdrant Vector Database    │
│  • gpt-oss:20b (chat)   │    │  • SigLIP embeddings       │
│  • MedGemma (vision)    │    │  • 6,500+ SCIN cases       │
│  • Local inference      │    │  • Similarity search       │
└─────────────────────────┘    └────────────────────────────┘
```

### Key Technologies

- **Google ADK (Agent Development Kit)**: Gemini 2.0 with automatic function calling
- **MCP (Model Context Protocol)**: 7 tools for medical operations
- **Ollama**: Local LLM for MedGemma vision and fallback chat
- **SigLIP**: Medical image embeddings (768-dim vectors)
- **Qdrant**: Vector database for RAG similarity search
- **Whisper**: Multi-language speech-to-text
- **SOAP Framework**: Medical consultation structure (Subjective, Objective, Assessment, Plan)

See [backend/README.md](backend/README.md) for detailed setup and API documentation.

\`\`\`

---

## Design Principles

- **Minimum font size**: 20-24px for readability
- **High contrast**: Teal primary, cream background, amber accents
- **Large touch targets**: Minimum 48px, dial pad buttons 60-80px
- **Voice-first**: Microphone button is primary interaction
- **Visual feedback**: Animations for listening, speaking, processing states

---

## Documentation

Comprehensive documentation is available in MkDocs format:

```bash
# Install MkDocs
uv pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin

# Serve documentation locally
mkdocs serve
```

Visit [http://localhost:8000](http://localhost:8000) to browse the full documentation.

**Documentation Sections:**
- Getting Started - Installation, configuration, and quick start
- Architecture - System design and component details
- Features - Detailed feature documentation
- Development - API reference and development guides
- Deployment - Production setup and monitoring
- Reference - SOAP framework, troubleshooting, and more

## Support

For issues or questions, check:
- [Documentation](http://localhost:8000) - Run `mkdocs serve`
- [Troubleshooting Guide](docs/reference/troubleshooting.md)
- Vercel deployment logs
- Browser console for debug messages
- Network tab for API call failures
