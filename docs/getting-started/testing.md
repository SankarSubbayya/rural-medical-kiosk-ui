# Testing Guide

Comprehensive testing guide for the Rural Medical AI Kiosk.

## Overview

This guide covers:

- Unit testing individual components
- Integration testing API endpoints
- End-to-end testing user workflows
- Testing with sample data
- Performance testing
- Multi-language testing

## Quick Test with Sample Data

The fastest way to test the report system without completing a full consultation:

```bash
# Create a sample consultation
curl -X POST http://localhost:8000/test/create-sample-consultation

# Returns:
{
  "status": "created",
  "consultation_id": "97e13cb5-a978-422e-9ed6-fd7074982105",
  "message": "Sample consultation created..."
}
```

Use the returned ID to test reports in the frontend or via API.

## Frontend Testing

### Manual Testing Workflow

1. **Start Both Servers**
   ```bash
   # Terminal 1: Backend
   cd backend && source .venv/bin/activate
   uvicorn main:app --reload

   # Terminal 2: Frontend
   pnpm dev
   ```

2. **Test Welcome Screen**
   - Navigate to http://localhost:3000
   - Verify welcome screen loads
   - Check QR code and phone number options
   - Test "Skip to Demo" button

3. **Test Consultation Flow**
   - Click through to consultation
   - Test voice input (microphone button)
   - Send text messages via chat
   - Upload test image
   - Verify AI responses

4. **Test Report Generation**
   - Complete consultation or use test endpoint
   - Click report button (top-right)
   - Choose Patient Summary
   - Click "View" - verify formatted report displays
   - Click "Download" - verify PDF downloads
   - Repeat for Physician Report

### Component Testing

Create test files in `__tests__` directory:

```typescript
// __tests__/report-viewer.test.tsx
import { render, screen } from '@testing-library/react';
import { ReportViewer } from '@/components/kiosk/report-viewer';

describe('ReportViewer', () => {
  it('renders report text correctly', () => {
    render(
      <ReportViewer
        consultationId="test-123"
        reportType="patient"
        isOpen={true}
        onClose={() => {}}
      />
    );

    expect(screen.getByText(/Report/i)).toBeInTheDocument();
  });
});
```

## Backend Testing

### API Endpoint Testing

#### 1. Health Check

```bash
curl http://localhost:8000/health

# Expected: {"status": "healthy"}
```

#### 2. Test SOAP Agent

```bash
curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d '{
    "consultation_id": "test-001",
    "message": "I have a red rash on my arm",
    "language": "en"
  }'
```

#### 3. Test Image Analysis

```bash
curl -X POST http://localhost:8000/analyze/image \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "base64_encoded_image_here",
    "body_location": "arm"
  }'
```

#### 4. Test Speech Services

```bash
# Text-to-speech
curl -X POST http://localhost:8000/speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how can I help you today?",
    "language": "en"
  }' \
  -o test-audio.mp3
```

#### 5. Test Report Generation

```bash
# Create test consultation first
CONSULT_ID=$(curl -X POST http://localhost:8000/test/create-sample-consultation \
  -s | jq -r '.consultation_id')

# Generate patient report
curl -X POST http://localhost:8000/report/patient \
  -H "Content-Type: application/json" \
  -d "{
    \"consultation_id\": \"$CONSULT_ID\",
    \"language\": \"en\"
  }"

# Download PDF
curl -o test-report.pdf \
  http://localhost:8000/report/$CONSULT_ID/pdf

# Verify PDF
file test-report.pdf
```

### Python Unit Tests

Create tests in `backend/tests/`:

```python
# backend/tests/test_report_service.py
import pytest
from app.services.report_service import ReportService
from app.models.soap import SOAPConsultation

def test_generate_patient_report():
    """Test patient report generation"""
    service = ReportService()
    consultation = create_test_consultation()

    report = service.generate_patient_report(consultation, language="en")

    assert "what we found" in report.lower()
    assert "what to do next" in report.lower()
    assert consultation.subjective.chief_complaint in report

def test_generate_physician_report():
    """Test physician report generation"""
    service = ReportService()
    consultation = create_test_consultation()

    report = service.generate_physician_report(consultation, language="en")

    assert "SUBJECTIVE" in report
    assert "OBJECTIVE" in report
    assert "ASSESSMENT" in report
    assert "PLAN" in report

def test_generate_pdf_report():
    """Test PDF generation"""
    service = ReportService()
    consultation = create_test_consultation()

    pdf_bytes = service.generate_pdf_report(consultation, report_type="patient")

    assert pdf_bytes.startswith(b'%PDF')  # PDF header
    assert len(pdf_bytes) > 0
```

Run tests:

```bash
cd backend
pytest tests/ -v
```

## Integration Testing

### End-to-End Workflow Test

Test the complete consultation flow:

```bash
#!/bin/bash
# test-e2e.sh

echo "1. Creating consultation..."
CONSULT=$(curl -X POST http://localhost:8000/consultation/create \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "test-patient", "kiosk_id": "test-kiosk"}' \
  -s)

CONSULT_ID=$(echo $CONSULT | jq -r '.id')
echo "   Consultation ID: $CONSULT_ID"

echo "2. Sending greeting message..."
curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d "{
    \"consultation_id\": \"$CONSULT_ID\",
    \"message\": \"Hello\",
    \"language\": \"en\"
  }" \
  -s | jq '.response'

echo "3. Describing symptoms..."
curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d "{
    \"consultation_id\": \"$CONSULT_ID\",
    \"message\": \"I have a red itchy rash on my arm for 3 days\",
    \"language\": \"en\"
  }" \
  -s | jq '.response'

echo "4. Uploading image..."
# ... image upload logic ...

echo "5. Generating report..."
curl -X POST http://localhost:8000/report/patient \
  -H "Content-Type: application/json" \
  -d "{
    \"consultation_id\": \"$CONSULT_ID\",
    \"language\": \"en\"
  }" \
  -s | jq '.report_text'

echo "✅ End-to-end test complete!"
```

## Multi-Language Testing

Test all supported languages:

```bash
# Create test consultation
CONSULT_ID=$(curl -X POST http://localhost:8000/test/create-sample-consultation \
  -s | jq -r '.consultation_id')

# Test each language
for lang in en hi ta te bn; do
  echo "Testing language: $lang"

  curl -X POST http://localhost:8000/report/patient \
    -H "Content-Type: application/json" \
    -d "{
      \"consultation_id\": \"$CONSULT_ID\",
      \"language\": \"$lang\"
    }" \
    -s | jq -r '.report_text' | head -n 5

  echo "---"
done
```

## Performance Testing

### Load Testing with Apache Bench

```bash
# Test report endpoint performance
ab -n 100 -c 10 \
  -p post-data.json \
  -T application/json \
  http://localhost:8000/report/patient
```

### Response Time Testing

```bash
# Measure API response times
time curl -X POST http://localhost:8000/agent/message \
  -H "Content-Type: application/json" \
  -d '{
    "consultation_id": "perf-test",
    "message": "test message",
    "language": "en"
  }' \
  -s > /dev/null
```

## Automated Testing

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        cd backend
        pip install uv
        uv venv
        source .venv/bin/activate
        uv pip install -r requirements.txt

    - name: Run tests
      run: |
        cd backend
        source .venv/bin/activate
        pytest tests/ -v

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install pnpm
      uses: pnpm/action-setup@v2
      with:
        version: 8

    - name: Install dependencies
      run: pnpm install

    - name: Run tests
      run: pnpm test
```

## Test Checklist

### Before Release

- [ ] All API endpoints return expected responses
- [ ] Frontend loads without errors
- [ ] Voice input/output works
- [ ] Image upload and analysis functional
- [ ] Reports generate correctly (both types)
- [ ] PDFs download successfully
- [ ] Multi-language support working
- [ ] Error handling displays user-friendly messages
- [ ] Performance is acceptable (<2s response times)
- [ ] Mobile/tablet responsive design works

### Regression Testing

After any major changes:

1. Run full test suite: `pytest backend/tests/`
2. Test all API endpoints with sample data
3. Manual walkthrough of user flows
4. Check browser console for errors
5. Verify PDF generation still works
6. Test on different devices/browsers

## Debugging Tips

### Backend Debugging

```python
# Add debug logging in backend
import logging
logging.basicConfig(level=logging.DEBUG)

# In your code
logger = logging.getLogger(__name__)
logger.debug(f"Consultation ID: {consultation_id}")
logger.debug(f"SOAP data: {consultation.dict()}")
```

### Frontend Debugging

```typescript
// Enable detailed logging
console.log('[DEBUG] Report data:', reportData);
console.log('[DEBUG] API response:', response);

// Use React DevTools
// Check component state and props
```

### Network Debugging

```bash
# Watch backend logs
tail -f backend/logs/app.log

# Monitor network traffic
# Use browser DevTools > Network tab

# Check backend server logs
# Look for errors in uvicorn output
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 404 on report | Consultation not saved | Check backend logs, verify consultation exists |
| PDF download fails | ReportLab error | Check backend requirements, verify fonts installed |
| Voice not working | HTTPS required | Use localhost or setup SSL |
| Slow responses | Model loading | Pre-load Ollama models, increase timeout |

## Next Steps

- [Troubleshooting Guide](../reference/troubleshooting.md)
- [API Reference](../development/api-reference.md)
- [Deployment Guide](../deployment/production.md)
