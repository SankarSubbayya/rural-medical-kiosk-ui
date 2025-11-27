# Dermatology AI Kiosk - SOAP Framework Implementation Plan

## Executive Summary

This plan transforms the existing rural medical kiosk UI into a complete dermatological guidance system following the SOAP (Subjective, Objective, Assessment, Plan) medical framework. The system acts as a "patient advocate" - gathering information and connecting patients to providers, NOT practicing medicine.

---

## Current State Analysis

### What Exists (Production-Ready UI)
- Voice-first consultation interface with chat
- Camera capture with back-camera preference
- Phone/QR authentication flow
- Health passport timeline view
- Animated AI avatar with status indicators
- Bottom navigation between screens
- Responsive design with accessibility (large touch targets, high contrast)

### What Needs Implementation
- All backend services in `lib/kiosk-services.ts` are placeholders
- No real speech-to-text or text-to-speech
- No AI/LLM integration
- No image analysis pipeline
- No multilingual support
- No SOAP framework workflow
- No physician report generation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
├─────────────────────────────────────────────────────────────────┤
│  Voice Interface  │  Camera (WebRTC)  │  SOAP Flow Controller   │
└────────┬──────────┴─────────┬─────────┴────────────┬────────────┘
         │                    │                       │
         ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (Next.js API Routes)             │
├─────────────────────────────────────────────────────────────────┤
│  /api/speech     │  /api/analyze    │  /api/consultation        │
│  - STT (Whisper) │  - SCIN RAG      │  - SOAP workflow          │
│  - TTS           │  - MedGemma      │  - Report generation      │
│  - Language Det  │  - SigLIP-2      │  - ICD code mapping       │
└────────┬─────────┴────────┬─────────┴──────────────┬────────────┘
         │                  │                         │
         ▼                  ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                          │
├─────────────────────────────────────────────────────────────────┤
│  Speech APIs     │  Vector DB (RAG)  │  Healthcare Facility API  │
│  - Whisper       │  - SCIN embeddings│  - Case submission        │
│  - Google TTS    │  - Pinecone/Weaviate                         │
│  - Azure Speech  │  - ChromaDB       │  - Notification system    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Core Infrastructure

### 1.1 Multilingual Voice System

**Goal:** Voice-only interface supporting 5+ languages with detection

**New Files:**
- `lib/services/speech-service.ts` - Speech-to-text and text-to-speech
- `lib/services/language-service.ts` - Language detection and translation
- `app/api/speech/route.ts` - Speech API endpoint
- `app/api/speech/tts/route.ts` - Text-to-speech endpoint

**Implementation:**

```typescript
// lib/services/speech-service.ts
interface SpeechConfig {
  language?: string; // Auto-detect if not provided
  continuous?: boolean;
}

interface TranscriptionResult {
  text: string;
  language: string;
  confidence: number;
  medicalTermsDetected: string[];
}

// Use Web Speech API for browser-native STT, fallback to Whisper API
// Use Google Cloud TTS or Azure Speech for natural voice output
```

**Language Support (Phase 1 - Minimum 5):**
1. English (en)
2. Hindi (hi)
3. Tamil (ta)
4. Telugu (te)
5. Bengali (bn)

**Component Updates:**
- `components/kiosk/consultation-screen.tsx` - Add language selector, remove text input option
- `components/kiosk/voice-interface.tsx` (new) - Dedicated voice-only interaction component

### 1.2 WebRTC Camera Integration

**Goal:** Replace getUserMedia with proper WebRTC for reliable camera access

**New Files:**
- `lib/services/webrtc-service.ts` - WebRTC camera management
- `components/kiosk/permission-gate.tsx` - Explicit permission request UI

**Features:**
- Permission-gated image capture (explicit consent before every photo)
- Body location selector (arm, face, back, leg, etc.)
- Image quality validation
- Multiple angle capture support

**Privacy Flow:**
```
1. Agent explains why photo is needed
2. "Do I have your permission to take a photo of [body part]?"
3. Wait for explicit "Yes" voice confirmation
4. Show camera preview
5. Countdown and capture
6. Show preview, ask to confirm or retake
```

### 1.3 SOAP Framework State Machine

**Goal:** Implement structured consultation flow following SOAP

**New Files:**
- `lib/soap/soap-state-machine.ts` - Consultation state management
- `lib/soap/types.ts` - SOAP data structures
- `lib/soap/medical-filter.ts` - Filter relevant from irrelevant information

**SOAP State Flow:**
```
GREETING → SUBJECTIVE → OBJECTIVE → ASSESSMENT → PLAN → SUMMARY
    │          │            │           │          │        │
    ▼          ▼            ▼           ▼          ▼        ▼
 Language   Voice       Image       Analysis   Guidance   Reports
 Detection  Narrative   Capture     & ICD      & Triage   Generated
```

**Data Structures:**

```typescript
// lib/soap/types.ts
interface SOAPConsultation {
  id: string;
  patientId: string;
  language: string;
  timestamp: Date;

  subjective: {
    rawTranscript: string[];
    filteredNarrative: string;
    symptoms: Symptom[];
    duration: string;
    onset: string;
    aggravatingFactors: string[];
    relievingFactors: string[];
  };

  objective: {
    images: CapturedImage[];
    bodyLocation: string;
    visualObservations: string[];
    measurements?: { area?: string; count?: number };
  };

  assessment: {
    possibleConditions: DifferentialDiagnosis[];
    icdCodes: ICDCode[];
    confidence: number;
    ragSources: string[];
    urgencyLevel: 'emergency' | 'urgent' | 'routine' | 'self-care';
  };

  plan: {
    patientGuidance: string; // Layman language
    physicianSummary: string; // Formal medical
    transportation: TransportationInfo;
    followUp: string;
    selfCareInstructions?: string[];
  };
}

interface DifferentialDiagnosis {
  condition: string;
  icdCode: string;
  probability: number;
  supportingEvidence: string[];
  contraindications: string[];
}
```

---

## Phase 2: AI & RAG Integration

### 2.1 SCIN Database RAG System

**Goal:** Implement multimodal retrieval using Harvard SCIN database (2GB)

**New Files:**
- `lib/rag/scin-embeddings.ts` - Embedding generation and storage
- `lib/rag/vector-store.ts` - Vector database operations
- `lib/rag/retrieval-service.ts` - Similarity search and context retrieval
- `scripts/ingest-scin.ts` - Database ingestion script

**Architecture:**

```
SCIN Database (2GB)
       │
       ▼
┌──────────────────┐
│ Ingestion Script │
│ - Parse images   │
│ - Extract text   │
│ - Generate embeds│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Vector Store   │
│ (Pinecone/Chroma)│
│ - Image embeddings│
│ - Text embeddings │
│ - Metadata        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Retrieval Service│
│ - Multimodal query│
│ - Re-ranking     │
│ - Context window │
└──────────────────┘
```

**Embedding Models:**
- **SigLIP-2** - For image embeddings (skin condition images)
- **MedGemma** - For text embeddings (medical descriptions)
- Combine both for multimodal retrieval

### 2.2 Diagnostic AI Agent

**Goal:** Implement AI agent that follows medical guidelines strictly

**New Files:**
- `lib/agents/diagnostic-agent.ts` - Main diagnostic reasoning agent
- `lib/agents/prompts/system-prompt.ts` - Carefully crafted system instructions
- `lib/agents/prompts/soap-prompts.ts` - Stage-specific prompts
- `lib/agents/safety-guardrails.ts` - Critical safety checks

**System Prompt Core Principles:**
```
You are a PATIENT ADVOCATE, NOT a doctor. Your role is to:
1. Gather comprehensive case history through conversation
2. Document symptoms and visual evidence
3. Suggest POSSIBLE conditions (never diagnose)
4. Triage urgency and connect to healthcare providers
5. Provide practical guidance (transportation, what to expect)

You MUST:
- Never prescribe medications
- Never provide definitive diagnoses
- Always recommend professional consultation
- Flag potential emergencies immediately
- Use simple, understandable language
```

**Critical Condition Detection:**
```typescript
// lib/agents/safety-guardrails.ts
const CRITICAL_CONDITIONS = [
  'melanoma',
  'cellulitis',
  'necrotizing fasciitis',
  'stevens-johnson syndrome',
  'toxic epidermal necrolysis',
  'meningococcal rash',
  'anaphylaxis',
  'severe burns',
  // ... comprehensive list
];

const ESCALATION_PHRASES = [
  'rapidly spreading',
  'fever with rash',
  'difficulty breathing',
  'swelling throat',
  'severe pain',
  // ...
];
```

### 2.3 De-escalation & Common Sense Engine

**Goal:** Appropriately handle non-medical or minor issues

**New Files:**
- `lib/agents/deescalation-service.ts` - Handle non-emergency cases
- `lib/agents/common-sense-checks.ts` - Basic interrogation logic

**Common Sense Checks:**
```typescript
interface CommonSenseCheck {
  pattern: RegExp | string[];
  question: string;
  ifYes: 'dismiss' | 'continue' | 'educate';
  response: string;
}

const COMMON_SENSE_CHECKS: CommonSenseCheck[] = [
  {
    pattern: ['blue', 'paint', 'ink', 'marker'],
    question: "That looks like it might be paint or ink. Have you tried washing the area with soap and water?",
    ifYes: 'dismiss',
    response: "Great! If it washes off, it's not a skin condition. Let me know if you have other concerns."
  },
  {
    pattern: ['tattoo', 'henna', 'mehndi'],
    question: "Is that a tattoo or henna design?",
    ifYes: 'dismiss',
    response: "I see! Tattoos aren't skin conditions. Is there something else I can help with?"
  },
  {
    pattern: ['acne', 'pimple', 'teenager'],
    question: "This looks like common acne. Is this appearing during puberty?",
    ifYes: 'educate',
    response: "This is very normal during adolescence. Keep the area clean, avoid touching it, and it will improve over time. Would you like some general skincare tips?"
  }
];
```

---

## Phase 3: Report Generation & Delivery

### 3.1 Dual Report System

**Goal:** Generate two versions of case history

**New Files:**
- `lib/reports/patient-report.ts` - Simple language report
- `lib/reports/physician-report.ts` - Formal medical report
- `lib/reports/icd-mapper.ts` - Map conditions to ICD codes
- `lib/reports/pdf-generator.ts` - Generate downloadable reports
- `components/kiosk/report-screen.tsx` - Report display UI

**Patient Report (Voice Output):**
```
Simple explanation of:
- What we observed
- What it might be (possibilities, not diagnosis)
- What to do next
- How urgent it is
- Where to go (specific directions)
- What to tell the doctor
```

**Physician Report (Formal):**
```
DERMATOLOGY CONSULTATION REFERRAL
Patient ID: [anonymized]
Date: [timestamp]
Location: [kiosk location]

SUBJECTIVE:
[Filtered medical narrative]

OBJECTIVE:
[Image attachments]
[Visual observations]

ASSESSMENT:
Differential Diagnosis:
1. [Condition] - ICD-10: [code] - Confidence: [%]
   Supporting: [evidence]
2. [Condition] - ICD-10: [code] - Confidence: [%]
   Supporting: [evidence]

PLAN:
[Recommended actions]
[Urgency level]

Generated by: Agentic Health Kiosk
Case ID: [unique identifier]
```

### 3.2 Healthcare Facility Integration

**Goal:** Send case histories to remote healthcare facilities

**New Files:**
- `lib/services/facility-service.ts` - Healthcare facility API
- `lib/services/notification-service.ts` - Alert notifications
- `app/api/facility/submit/route.ts` - Case submission endpoint

**Integration Flow:**
```
1. Consultation complete
2. Generate physician report
3. Submit to facility queue
4. Notify on-call provider
5. Track case status
6. Update patient on next steps
```

---

## Phase 4: UI/UX Enhancements

### 4.1 Voice-Only Interface Redesign

**Goal:** Remove all text input, make voice primary

**Component Updates:**
- Remove text input from `consultation-screen.tsx`
- Add visual voice activity indicator
- Add voice command hints
- Implement voice-guided navigation

**Voice Commands:**
```
"Go back" - Previous screen
"Start over" - Reset consultation
"Help" - Instructions
"Yes" / "No" - Confirmations
"Take photo" - Trigger camera
"Send to doctor" - Submit case
```

### 4.2 SOAP Flow Visualization

**Goal:** Show patient progress through consultation

**New Components:**
- `components/kiosk/soap-progress.tsx` - Visual progress indicator
- `components/kiosk/step-guide.tsx` - Current step instructions

**Visual Design:**
```
[S]─────[O]─────[A]─────[P]
 ●       ○       ○       ○
Story   Photo   Review  Plan
```

### 4.3 Language Selection

**Goal:** Easy language switching

**New Components:**
- `components/kiosk/language-selector.tsx` - Language picker
- Voice-activated language detection

**Flow:**
```
1. System speaks greeting in detected language
2. "I detected [language]. Is this correct?"
3. If no, show language grid
4. Confirm and continue
```

---

## Phase 5: Advanced Features

### 5.1 Offline Support

**Goal:** Function without internet, sync when connected

**New Files:**
- `lib/offline/queue-manager.ts` - Offline action queue
- `lib/offline/sync-service.ts` - Background sync
- `lib/offline/local-storage.ts` - IndexedDB wrapper

**Offline Capabilities:**
- Cache language models locally
- Store consultations in IndexedDB
- Queue image uploads
- Sync on reconnection

### 5.2 Fine-Tuned Embeddings (Advanced)

**Goal:** Train custom embeddings for better retrieval

**Training Approach:**
```
1. Contrastive Loss Function:
   - Same diagnosis images → closer in embedding space
   - Different diagnoses → farther apart

2. Isotropic Distribution:
   - Even spread across unit hypersphere
   - Better semantic separation

3. Validation via Clustering:
   - K-means on embeddings
   - Verify same-diagnosis images cluster together
```

**New Files:**
- `scripts/train-embeddings/` - Training scripts
- `lib/rag/custom-embeddings.ts` - Custom model inference

---

## Implementation Priority & Phases

### MVP (Weeks 1-4)
1. Voice interface with 5 languages
2. Basic SOAP flow without RAG
3. Camera with permission gates
4. Simple AI responses (not RAG)
5. Patient voice summary

### Phase 2 (Weeks 5-8)
1. SCIN database ingestion
2. RAG retrieval system
3. ICD code mapping
4. Physician report generation
5. Basic facility submission

### Phase 3 (Weeks 9-12)
1. De-escalation engine
2. Common sense checks
3. Offline support
4. Extended language support
5. Fine-tuned embeddings

---

## File Structure (Final)

```
app/
├── api/
│   ├── speech/
│   │   ├── route.ts           # STT endpoint
│   │   └── tts/route.ts       # TTS endpoint
│   ├── analyze/
│   │   ├── route.ts           # Image analysis
│   │   └── rag/route.ts       # RAG query
│   ├── consultation/
│   │   ├── route.ts           # SOAP workflow
│   │   └── report/route.ts    # Report generation
│   └── facility/
│       └── submit/route.ts    # Case submission
├── page.tsx
├── layout.tsx
└── globals.css

components/
├── kiosk/
│   ├── welcome-screen.tsx
│   ├── consultation-screen.tsx  # Updated - voice only
│   ├── soap-progress.tsx        # NEW
│   ├── voice-interface.tsx      # NEW
│   ├── permission-gate.tsx      # NEW
│   ├── camera-capture.tsx       # Updated
│   ├── language-selector.tsx    # NEW
│   ├── report-screen.tsx        # NEW
│   ├── health-passport-screen.tsx
│   ├── ai-avatar.tsx
│   └── ...
└── ui/

lib/
├── services/
│   ├── speech-service.ts        # NEW
│   ├── language-service.ts      # NEW
│   ├── webrtc-service.ts        # NEW
│   ├── facility-service.ts      # NEW
│   └── notification-service.ts  # NEW
├── soap/
│   ├── soap-state-machine.ts    # NEW
│   ├── types.ts                 # NEW
│   └── medical-filter.ts        # NEW
├── agents/
│   ├── diagnostic-agent.ts      # NEW
│   ├── deescalation-service.ts  # NEW
│   ├── common-sense-checks.ts   # NEW
│   ├── safety-guardrails.ts     # NEW
│   └── prompts/
│       ├── system-prompt.ts     # NEW
│       └── soap-prompts.ts      # NEW
├── rag/
│   ├── scin-embeddings.ts       # NEW
│   ├── vector-store.ts          # NEW
│   ├── retrieval-service.ts     # NEW
│   └── custom-embeddings.ts     # NEW (Advanced)
├── reports/
│   ├── patient-report.ts        # NEW
│   ├── physician-report.ts      # NEW
│   ├── icd-mapper.ts            # NEW
│   └── pdf-generator.ts         # NEW
├── offline/
│   ├── queue-manager.ts         # NEW
│   ├── sync-service.ts          # NEW
│   └── local-storage.ts         # NEW
├── kiosk-services.ts            # Update with real implementations
└── utils.ts

scripts/
├── ingest-scin.ts               # NEW - SCIN database ingestion
└── train-embeddings/            # NEW (Advanced)

hooks/
├── use-mobile.ts
├── use-toast.ts
├── use-voice.ts                 # NEW
├── use-soap.ts                  # NEW
└── use-offline.ts               # NEW
```

---

## Environment Variables Required

```env
# Speech Services
OPENAI_API_KEY=               # For Whisper STT
GOOGLE_TTS_API_KEY=           # For Text-to-Speech
AZURE_SPEECH_KEY=             # Alternative TTS

# AI Models
GOOGLE_AI_API_KEY=            # For MedGemma
HUGGINGFACE_TOKEN=            # For SigLIP-2

# Vector Database
PINECONE_API_KEY=             # Or ChromaDB config
PINECONE_ENVIRONMENT=
PINECONE_INDEX=

# Healthcare Integration
FACILITY_API_URL=
FACILITY_API_KEY=

# Storage
DATABASE_URL=                  # PostgreSQL for records
BLOB_STORAGE_URL=             # For images
```

---

## Safety & Compliance Checklist

- [ ] Never provide diagnoses - only possibilities
- [ ] Never prescribe medications
- [ ] Always recommend professional consultation
- [ ] Flag emergencies with immediate escalation
- [ ] Explicit permission before every photo
- [ ] Data encrypted at rest and in transit
- [ ] Audit logging for all consultations
- [ ] Anonymization options for research use
- [ ] HIPAA-aware data handling (if applicable)
- [ ] Clear disclaimers in all outputs

---

## Success Metrics

1. **Language Detection Accuracy**: >95% for supported languages
2. **STT Accuracy**: >90% word error rate
3. **RAG Retrieval Relevance**: Top-5 results include correct diagnosis >80%
4. **Emergency Detection**: 100% sensitivity for critical conditions
5. **User Completion Rate**: >70% complete full SOAP flow
6. **Time to Guidance**: <10 minutes average consultation

---

## Next Steps

1. Review and approve this plan
2. Set up development environment with required API keys
3. Begin Phase 1 implementation starting with speech services
4. Acquire and prepare SCIN database for ingestion
