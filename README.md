# Agentic Health - Rural Medical AI Kiosk

A highly intuitive, empathetic UI for a rural medical AI kiosk designed to bridge the gap between advanced technology and low-tech literacy users.

## Features

- **Handshake (Login)**: QR code scanning or phone number entry with large dial pad
- **Consultation (Chat)**: Voice-first AI interaction with friendly avatar using GPT-OSS (20B)
- **Camera Capture**: Dermatology image capture for AI analysis using MedGemma
- **Health Passport**: Visual timeline of health records and next steps
- **RAG Similarity Search**: Find similar cases from 6,500+ dermatology images using SigLIP embeddings

---

## Files to Customize

### Core Services (✅ Fully Integrated with Backend)

| File | Purpose | Status |
|------|---------|--------|
| [lib/backend-api.ts](lib/backend-api.ts) | **Backend API client** | ✅ Complete - FastAPI integration |
| [lib/kiosk-services.ts](lib/kiosk-services.ts) | **Service layer** | ✅ Integrated - Uses backend for AI/medical services |

**Integration Status:**

✅ **Completed Integrations:**
- `sendMessageToAI()` - Uses Ollama (gpt-oss:20b) via backend
- `analyzeDermatologyImage()` - Uses MedGemma + SigLIP RAG
- `startVoiceRecognition()` - Uses Whisper for transcription
- `textToSpeech()` - Uses gTTS for voice output

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

**Important**: The frontend now connects to the FastAPI backend for all AI/medical services (chat, image analysis, voice). No additional API keys are needed - the backend handles Ollama, Qdrant, and Whisper integration.

---

## Quick Start Integration Guide

### Step 1: Start Backend Server

First, ensure the FastAPI backend is running:

\`\`\`bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Ollama server (in separate terminal)
ollama serve

# Start FastAPI backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

Verify backend is running: http://localhost:8000/docs

### Step 2: Configure Frontend

Create `.env.local` file:

\`\`\`bash
cp .env.local.example .env.local
\`\`\`

Edit `.env.local`:

\`\`\`env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
\`\`\`

### Step 3: Start Frontend

\`\`\`bash
pnpm install
pnpm dev
\`\`\`

Open http://localhost:3000

### Step 4: Test Integration

The frontend is now fully integrated with the backend:

- **AI Chat**: Uses Ollama (gpt-oss:20b) via `/chat/message`
- **Image Analysis**: Uses MedGemma + SigLIP RAG via `/analyze/image`
- **Voice Input**: Uses Whisper via `/speech/transcribe`
- **Voice Output**: Uses gTTS via `/speech/synthesize`
- **Similar Cases**: Uses Qdrant vector search via `/analyze/similar`

All integration code is in:
- [lib/backend-api.ts](lib/backend-api.ts) - API client
- [lib/kiosk-services.ts](lib/kiosk-services.ts) - Service layer

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

The backend uses:
- **Ollama** for local LLM inference (gpt-oss:20b, MedGemma)
- **SigLIP** for medical image embeddings (768-dim vectors)
- **Qdrant** vector database for similarity search
- **Whisper** for multi-language speech-to-text
- **SOAP framework** for medical consultation structure

See [backend/README.md](backend/README.md) for setup and API documentation.

\`\`\`

---

## Design Principles

- **Minimum font size**: 20-24px for readability
- **High contrast**: Teal primary, cream background, amber accents
- **Large touch targets**: Minimum 48px, dial pad buttons 60-80px
- **Voice-first**: Microphone button is primary interaction
- **Visual feedback**: Animations for listening, speaking, processing states

---

## Support

For issues or questions, check:
- Vercel deployment logs
- Browser console for `[v0]` debug messages
- Network tab for API call failures
