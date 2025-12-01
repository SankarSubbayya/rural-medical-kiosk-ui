# Deployment Guide

## Agentic Health - Rural Medical AI Kiosk

This guide provides step-by-step instructions to deploy the Rural Medical AI Kiosk system locally or on cloud infrastructure.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Local Development)](#quick-start-local-development)
3. [Environment Configuration](#environment-configuration)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Vector Database Setup (Qdrant)](#vector-database-setup-qdrant)
7. [Local LLM Setup (Ollama + MedGemma)](#local-llm-setup-ollama--medgemma)
8. [Docker Deployment](#docker-deployment)
9. [Cloud Deployment Options](#cloud-deployment-options)
10. [Verification & Testing](#verification--testing)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| pnpm | 8+ | Package manager |
| uv | Latest | Python package manager |
| Docker | 24+ | Container runtime (optional) |
| Ollama | Latest | Local LLM hosting |
| Qdrant | 1.12+ | Vector database |

### API Keys Required

| Service | Environment Variable | Purpose |
|---------|---------------------|---------|
| Google Gemini | `GOOGLE_API_KEY` | SOAP Orchestrator Agent (Gemini 2.0 Flash) |

---

## Quick Start (Local Development)

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/your-org/rural-medical-kiosk-ui.git
cd rural-medical-kiosk-ui

# Start all services (requires Docker)
docker compose up -d

# Or manually start each component:

# Terminal 1: Start Qdrant
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Terminal 2: Start Ollama with MedGemma
ollama serve
ollama pull medgemma:4b

# Terminal 3: Start Backend
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env  # Configure your API keys
uv run python main.py

# Terminal 4: Start Frontend
cd ..
pnpm install
pnpm dev
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Kiosk UI |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Qdrant Dashboard | http://localhost:6333/dashboard | Vector DB admin |

---

## Environment Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# =============================================================================
# GOOGLE ADK CONFIGURATION
# =============================================================================
# Required: Google Gemini API key for SOAP Orchestrator Agent
GOOGLE_API_KEY=your_google_api_key_here

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
# Gemini model for agent reasoning
GEMINI_MODEL=gemini-2.0-flash-exp

# Ollama endpoint for MedGemma
OLLAMA_BASE_URL=http://localhost:11434

# MedGemma model name (must be pulled in Ollama)
MEDGEMMA_MODEL=medgemma:4b

# =============================================================================
# VECTOR DATABASE (QDRANT)
# =============================================================================
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=scin_dermatology

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# =============================================================================
# SPEECH SERVICES
# =============================================================================
# Whisper model size: tiny, base, small, medium, large
WHISPER_MODEL=base

# Google TTS language
TTS_LANGUAGE=en
```

### Frontend Environment Variables

Create `.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Enable debug mode
NEXT_PUBLIC_DEBUG=true
```

---

## Backend Deployment

### Using uv (Recommended)

```bash
cd backend

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt

# Run the server
uv run python main.py
```

### Using pip (Alternative)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

### Production Mode

```bash
# Use Gunicorn with Uvicorn workers
uv pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

---

## Frontend Deployment

### Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Production Build

```bash
# Build for production
pnpm build

# Start production server
pnpm start
```

### Static Export (Optional)

```bash
# Export as static HTML (limited functionality)
pnpm build
# Output in .next/ directory
```

---

## Vector Database Setup (Qdrant)

### Option 1: Docker (Recommended)

```bash
# Run Qdrant with persistent storage
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### Option 2: Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

volumes:
  qdrant_storage:
```

### Option 3: Qdrant Cloud

1. Create account at https://cloud.qdrant.io
2. Create a cluster
3. Update environment variables:

```bash
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key
```

### Initialize SCIN Dataset

```bash
# The backend automatically initializes the collection on first run
# To manually seed the database:
cd backend
uv run python -c "from app.services.rag_service import RAGService; RAGService().initialize_collection()"
```

---

## Local LLM Setup (Ollama + MedGemma)

### Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from https://ollama.com/download
```

### Start Ollama Server

```bash
# Start the Ollama service
ollama serve
```

### Pull Required Models

```bash
# MedGemma for medical image analysis (required)
ollama pull medgemma:4b

# Alternative: Quantized version for lower memory
ollama pull medgemma:4b-q8_0

# Verify installation
ollama list
```

### Model Requirements

| Model | VRAM | RAM | Disk |
|-------|------|-----|------|
| medgemma:4b | 6GB | 8GB | 4GB |
| medgemma:4b-q8_0 | 4GB | 6GB | 3GB |

---

## Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - qdrant
      - ollama
    volumes:
      - ./backend:/app
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  # Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    restart: unless-stopped

  # Local LLM Server
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

volumes:
  qdrant_storage:
  ollama_models:
```

### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
```

### Frontend Dockerfile

Create `Dockerfile.frontend`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN pnpm build

# Production image
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
```

### Deploy with Docker Compose

```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

---

## Cloud Deployment Options

### Option 1: Google Cloud Run

```bash
# Backend
cd backend
gcloud run deploy agentic-health-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY}"

# Frontend
cd ..
gcloud run deploy agentic-health-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 2: Vercel (Frontend) + Railway (Backend)

**Frontend (Vercel):**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Backend (Railway):**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Deploy
cd backend
railway up
```

### Option 3: AWS EC2

```bash
# SSH into EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install dependencies
sudo yum install -y docker git
sudo systemctl start docker

# Clone and deploy
git clone https://github.com/your-org/rural-medical-kiosk-ui.git
cd rural-medical-kiosk-ui
docker compose up -d
```

---

## Verification & Testing

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Agent endpoint
curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "language": "en"}'

# Qdrant health
curl http://localhost:6333/health

# Ollama health
curl http://localhost:11434/api/tags
```

### End-to-End Test

```bash
# Run the test suite
cd backend
uv run pytest tests/ -v

# Test agent conversation flow
curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a red rash on my arm that has been itchy for two weeks",
    "language": "en"
  }'
```

### Expected Response

```json
{
  "success": true,
  "response": "I understand you have a red, itchy rash on your arm that's been bothering you for two weeks. Can you tell me more about when it started and if anything makes it better or worse?",
  "stage": "SUBJECTIVE",
  "consultation_id": "uuid-here"
}
```

---

## Troubleshooting

### Common Issues

#### 1. Google API Key Error

```
Error: Invalid API key
```

**Solution:**
- Ensure `GOOGLE_API_KEY` is set without quotes
- Verify key is valid at https://console.cloud.google.com
- Check `.env` file format:
  ```bash
  # Correct
  GOOGLE_API_KEY=AIza...

  # Wrong
  GOOGLE_API_KEY='AIza...'
  GOOGLE_API_KEY="AIza..."
  ```

#### 2. Qdrant Connection Failed

```
Error: Connection refused to localhost:6333
```

**Solution:**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

#### 3. Ollama Model Not Found

```
Error: model 'medgemma:4b' not found
```

**Solution:**
```bash
# Pull the model
ollama pull medgemma:4b

# Verify installation
ollama list
```

#### 4. CORS Errors

```
Error: CORS policy blocked
```

**Solution:**
- Add frontend URL to `CORS_ORIGINS` in backend `.env`
- Restart backend after changes

#### 5. Out of Memory (OOM)

```
Error: CUDA out of memory
```

**Solution:**
- Use quantized model: `ollama pull medgemma:4b-q8_0`
- Reduce batch size in analysis service
- Add swap space on Linux

### Logs

```bash
# Backend logs
cd backend && uv run python main.py 2>&1 | tee app.log

# Docker logs
docker compose logs -f backend

# Qdrant logs
docker logs qdrant
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT ARCHITECTURE                      │
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐ │
│  │   Frontend   │────▶│   Backend    │────▶│  External Services   │ │
│  │  (Next.js)   │     │  (FastAPI)   │     │                      │ │
│  │  Port: 3000  │     │  Port: 8000  │     │  • Google Gemini API │ │
│  └──────────────┘     └──────────────┘     │  • Qdrant (6333)     │ │
│                              │              │  • Ollama (11434)    │ │
│                              │              └──────────────────────┘ │
│                              ▼                                       │
│                    ┌──────────────────┐                             │
│                    │  SOAP Agent      │                             │
│                    │  (Gemini 2.0)    │                             │
│                    │                  │                             │
│                    │  ┌────────────┐  │                             │
│                    │  │ MCP Tools  │  │                             │
│                    │  │ • medgemma │  │                             │
│                    │  │ • siglip   │  │                             │
│                    │  │ • safety   │  │                             │
│                    │  └────────────┘  │                             │
│                    └──────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/rural-medical-kiosk-ui/issues
- Documentation: See `docs/` directory

---

*Built with Google Agent Development Kit for the ADK Course Capstone Project*
