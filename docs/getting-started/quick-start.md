# Quick Start Guide

Get the Rural Medical AI Kiosk running in 5 minutes.

## Prerequisites

- Python 3.10+ with `uv` package manager
- Node.js 18+ with `pnpm`
- Ollama (for local LLM models)
- Google API key (for Gemini 2.0)

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/rural-medical-kiosk-ui.git
cd rural-medical-kiosk-ui
```

## Step 2: Setup Backend

### Install Dependencies with uv

```bash
cd backend

# Install uv if not already installed
pip install uv

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:

```env
# Required for Google ADK SOAP Agent
GOOGLE_API_KEY=your_google_api_key_here
```

!!! tip "Get Google API Key"
    Get your free API key at: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Start Ollama Server

In a separate terminal:

```bash
# Start Ollama server
ollama serve

# Pull required models
ollama pull medgemma
ollama pull gpt-oss:20b
```

### Start Backend Server

```bash
# From backend directory with venv activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend is running: [http://localhost:8000/docs](http://localhost:8000/docs)

## Step 3: Setup Frontend

In a new terminal:

```bash
cd rural-medical-kiosk-ui

# Install dependencies
pnpm install

# Configure environment
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Start Frontend

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000)

## Step 4: Test the System

### Test with Sample Consultation

Create a test consultation with complete SOAP data:

```bash
curl -X POST http://localhost:8000/test/create-sample-consultation
```

This returns a consultation ID that you can use to test report generation.

### Interactive Testing

1. **Open Frontend**: Navigate to http://localhost:3000
2. **Start Consultation**: Click through the welcome screen
3. **Voice Interaction**: Click the microphone and describe symptoms
4. **Upload Image**: Click camera button to analyze a skin condition
5. **View Report**: Click the report button (top-right) when consultation completes
6. **Download PDF**: Choose Patient Summary or Physician Report

## Verify Integration

Check that all services are working:

```bash
# Test backend health
curl http://localhost:8000/health

# Test AI chat
curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d '{
    "consultation_id": "test-123",
    "message": "I have a rash on my arm",
    "language": "en"
  }'

# Test report generation (using test consultation)
curl -X POST http://localhost:8000/test/create-sample-consultation
# Use returned ID:
curl http://localhost:8000/report/{consultation_id}/pdf -o test.pdf
```

## What's Running

After completing these steps, you should have:

- ✅ Backend API running on port 8000
- ✅ Frontend UI running on port 3000
- ✅ Ollama server running on port 11434
- ✅ Google Gemini 2.0 connected via ADK
- ✅ Qdrant vector DB (embedded mode)

## Next Steps

- [Configuration Guide](configuration.md) - Customize settings
- [Testing Guide](testing.md) - Comprehensive testing
- [Architecture Overview](../architecture/overview.md) - Understand the system
- [API Reference](../development/api-reference.md) - API documentation

## Troubleshooting

### Backend won't start

- Check Python version: `python --version` (needs 3.10+)
- Verify virtual environment is activated
- Check `.env` file has `GOOGLE_API_KEY`

### Ollama models not found

```bash
# List installed models
ollama list

# Pull missing models
ollama pull medgemma
ollama pull gpt-oss:20b
```

### Frontend connection errors

- Verify `NEXT_PUBLIC_BACKEND_URL` in `.env.local`
- Check backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `backend/main.py`

### Google API errors

- Verify API key is valid
- Check quota limits at [Google AI Studio](https://aistudio.google.com)
- Ensure Gemini 2.0 Flash Exp is available in your region

For more issues, see [Troubleshooting Guide](../reference/troubleshooting.md).
