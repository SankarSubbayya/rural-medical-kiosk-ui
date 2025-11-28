# Dermatology Kiosk - Python Backend

A FastAPI backend for the Rural Medical AI Kiosk, providing dermatological guidance using the SOAP medical framework.

**IMPORTANT: This system is NOT a doctor. It provides guidance and case history preparation only.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                              │
│         (Voice-first interface, WebRTC camera)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Python)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Chat Service   │  │ Analysis Service│  │ Report Service  │  │
│  │  (Ollama)       │  │  (MedGemma)     │  │                 │  │
│  │                 │  │                 │  │                 │  │
│  │ - Conversation  │  │ - Image analysis│  │ - SOAP compile  │  │
│  │ - SOAP flow     │  │ - Visual feats  │  │ - ICD mapping   │  │
│  │ - Med filtering │  │ - Condition ID  │  │ - PDF generate  │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                     │           │
│  ┌────────┴────────┐  ┌────────┴────────┐           │           │
│  │ Speech Service  │  │  RAG Service    │           │           │
│  │ (Whisper/gTTS)  │  │  (Qdrant)       │           │           │
│  │                 │  │                 │           │           │
│  │ - STT (5+ lang) │  │ - SCIN database │           │           │
│  │ - TTS output    │  │ - SigLIP embed  │           │           │
│  │ - Lang detect   │  │ - Similar cases │           │           │
│  └─────────────────┘  └─────────────────┘           │           │
│                                                      │           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Safety Service                           │ │
│  │   - Critical condition detection                            │ │
│  │   - "Do Not Play Doctor" guardrails                         │ │
│  │   - Response sanitization                                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Model Responsibilities

| Model | Purpose | When Used |
|-------|---------|-----------|
| **gpt-oss:20b** (Ollama) | Conversational AI, SOAP flow, medical info filtering | Throughout consultation |
| **MedGemma** (Ollama) | Medical image analysis, condition suggestion | When patient shares skin image |
| **llava** (Ollama) | Fallback vision model | If MedGemma unavailable |
| **SigLIP** (HuggingFace) | 768-dim image embeddings for Qdrant RAG | Similarity search in 6,500+ SCIN images |
| **Whisper** (local) | Speech-to-text (5+ languages) | Voice input processing |
| **gTTS** | Text-to-speech (multilingual) | Voice output |

## SOAP Framework

The consultation follows the medical SOAP framework:

1. **S**ubjective - Patient's narrative, symptoms (via voice)
2. **O**bjective - Skin images, visual observations
3. **A**ssessment - Possible conditions with ICD-10 codes
4. **P**lan - Guidance, next steps, reports

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
│
├── app/
│   ├── config.py          # Settings and constants
│   │
│   ├── models/            # Pydantic data models
│   │   ├── soap.py        # SOAP consultation models
│   │   ├── chat.py        # Chat/conversation models
│   │   └── analysis.py    # Image analysis models
│   │
│   ├── services/          # Business logic
│   │   ├── chat_service.py      # Ollama conversation
│   │   ├── analysis_service.py  # MedGemma analysis
│   │   ├── rag_service.py       # Qdrant RAG retrieval
│   │   ├── speech_service.py    # Whisper/TTS
│   │   ├── report_service.py    # Report generation
│   │   └── safety_service.py    # Medical guardrails
│   │
│   └── routers/           # API endpoints
│       ├── consultation.py    # SOAP management
│       ├── chat.py           # Conversational AI
│       ├── analysis.py       # Image analysis
│       ├── speech.py         # Voice services
│       └── report.py         # Report generation
│
└── scripts/
    ├── ingest_scin.py              # Legacy SCIN ingestion
    ├── embed_scin_siglip.py        # SigLIP embedding for SCIN
    ├── test_siglip_embedding.py    # Test embedding pipeline
    ├── check_embedding_deps.py     # Dependency checker
    └── README_EMBEDDING.md         # Embedding documentation
```

## Prerequisites

### 1. Install Ollama

Download and install Ollama from https://ollama.ai/

```bash
# Verify installation
ollama --version
```

### 2. Pull Required Models

```bash
# Chat model (13GB) - for conversation and SOAP flow
ollama pull gpt-oss:20b

# MedGemma (5GB) - for medical image analysis
ollama pull amsaravi/medgemma-4b-it:q8

# LLaVA (4.7GB) - fallback vision model
ollama pull llava:latest
```

### 3. Verify Models

```bash
ollama list
```

You should see:
```
NAME                          SIZE
gpt-oss:20b                   13 GB
amsaravi/medgemma-4b-it:q8    5 GB
llava:latest                  4.7 GB
```

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local Ollama)
```

### 4. Start Ollama Server

```bash
# In a separate terminal
ollama serve
```

### 5. Embed SCIN Database with SigLIP (Recommended)

The system uses SigLIP (Sigmoid Loss for Language Image Pre-training) to create high-quality embeddings of 6,500+ dermatology images for similarity search.

```bash
# Quick test with 10 images
python scripts/test_siglip_embedding.py

# Embed full SCIN dataset (~30-45 minutes on GPU)
python scripts/embed_scin_siglip.py

# Or embed subset for testing
python scripts/embed_scin_siglip.py --limit 1000
```

**Why SigLIP?**
- Superior fine-grained visual recognition for medical images
- 768-dimensional embeddings optimized for cosine similarity
- Better zero-shot performance than CLIP on specialized domains

See [scripts/README_EMBEDDING.md](scripts/README_EMBEDDING.md) for detailed documentation.

### 6. Run Server

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Consultation Management
- `POST /consultation/create` - Start new consultation
- `GET /consultation/{id}` - Get consultation state
- `PUT /consultation/{id}/stage` - Update SOAP stage

### Conversational AI (Ollama)
- `POST /chat/message` - Send message, get AI response
- `POST /chat/{id}/start` - Get initial greeting
- `GET /chat/{id}/history` - Get conversation history

### Image Analysis (MedGemma + RAG)
- `POST /analyze/image` - Analyze skin image
- `POST /analyze/quick` - Simplified analysis
- `GET /analyze/similar` - Find similar cases

### Speech Services
- `POST /speech/transcribe` - Voice to text
- `POST /speech/synthesize` - Text to voice
- `POST /speech/detect-language` - Detect language
- `GET /speech/languages` - List supported languages

### Reports
- `POST /report/patient` - Patient-friendly report
- `POST /report/physician` - Formal medical report
- `GET /report/{id}/pdf` - Download PDF
- `POST /report/submit` - Submit to facility

## Supported Languages

| Code | Language |
|------|----------|
| en | English |
| hi | Hindi (हिन्दी) |
| ta | Tamil (தமிழ்) |
| te | Telugu (తెలుగు) |
| bn | Bengali (বাংলা) |

## Safety Features

The system enforces strict medical safety:

- **Never diagnoses** - Only suggests possibilities
- **Never prescribes** - No medication recommendations
- **Critical detection** - Flags serious conditions
- **Response sanitization** - Removes unsafe language
- **Mandatory disclaimers** - All outputs include warnings

## Environment Variables

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gpt-oss:20b
OLLAMA_MEDGEMMA_MODEL=amsaravi/medgemma-4b-it:q8
OLLAMA_VISION_MODEL=llava:latest

# Qdrant Vector Store
QDRANT_EMBEDDED=true              # Use embedded mode (no server needed)
QDRANT_PATH=./qdrant_data         # Storage path for embedded mode
# For server mode:
# QDRANT_EMBEDDED=false
# QDRANT_HOST=localhost
# QDRANT_PORT=6333

# Speech
WHISPER_MODEL=base                # tiny/base/small/medium/large

# Optional
HUGGINGFACE_TOKEN=hf_...          # For private models
```

## Vector Database Options

### Embedded Mode (Default)
No separate server required. Qdrant runs in-process.

```env
QDRANT_EMBEDDED=true
QDRANT_PATH=./qdrant_data
```

### Server Mode
For production or when you need to share the database.

```bash
# Start Qdrant server
docker run -p 6333:6333 qdrant/qdrant
```

```env
QDRANT_EMBEDDED=false
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Development

### Run with Hot Reload
```bash
uvicorn main:app --reload
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Health Check
```bash
curl http://localhost:8000/health
```

### Test Ollama Connection
```bash
curl http://localhost:11434/api/tags
```

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### Model Not Found
```bash
# Pull the required model
ollama pull gpt-oss:20b
ollama pull amsaravi/medgemma-4b-it:q8
```

### Memory Issues
If you have limited RAM, consider using smaller models:
```env
OLLAMA_CHAT_MODEL=llama3.2:3b
OLLAMA_MEDGEMMA_MODEL=alibayram/medgemma:4b
```

## License

This project is for educational and social utility purposes.
