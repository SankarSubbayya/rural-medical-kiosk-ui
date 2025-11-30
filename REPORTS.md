# Report Generation System

The rural medical kiosk includes a comprehensive report generation system that produces both patient-friendly summaries and formal physician reports with PDF export capabilities.

## Features

- **Patient Summary Reports**: Simple, plain-language summaries suitable for patients with low health literacy
- **Physician SOAP Reports**: Formal medical documentation following the SOAP framework with ICD-10 codes
- **PDF Export**: Professional PDF reports with proper formatting using ReportLab
- **Multi-language Support**: Reports can be generated in English, Hindi, Tamil, Telugu, and Bengali
- **Formatted Text View**: In-app report viewer with smart formatting for easy reading

## How It Works

### 1. Report Generation Flow

```
Consultation Complete → SOAP Data Saved → Generate Report → View/Download
```

When a consultation reaches the COMPLETED stage:
1. All SOAP sections are populated (Subjective, Objective, Assessment, Plan)
2. Report button appears in the consultation screen (top-right corner)
3. User can choose to generate Patient or Physician report
4. Reports can be viewed in-app or downloaded as PDF

### 2. Report Types

#### Patient Summary Report
- **Audience**: Patients and caregivers
- **Language**: Simple, non-technical
- **Content**:
  - Main symptoms in plain language
  - What the AI system found
  - Urgency level (Emergency/Urgent/Routine)
  - Step-by-step next actions
  - Self-care instructions
  - Important disclaimers

**Example Output**:
```
Here is what we found:
You came in because of Red, itchy rash on back.
You can schedule an appointment with a doctor when convenient.

What to do next:
1. Schedule an appointment with a dermatologist within 1-2 weeks
2. Bring this report to your appointment
3. Take photos if the rash changes

In the meantime, you can:
- Keep the affected area clean and dry
- Avoid scratching or picking at the rash
- Use fragrance-free moisturizer
...
```

#### Physician SOAP Report
- **Audience**: Medical professionals
- **Language**: Clinical, technical terminology
- **Content**:
  - Complete SOAP documentation
  - Differential diagnoses with ICD-10 codes
  - Confidence scores and evidence
  - RAG-retrieved similar cases
  - Recommended diagnostic tests
  - Referral information
  - Formal medical disclaimers

**Example Output**:
```
SUBJECTIVE
==========
Chief Complaint: Red, itchy rash on back
Duration: 3 days

Reported Symptoms:
- Red, itchy rash (3 days)

History: No significant medical history

OBJECTIVE
=========
Primary Location: back
Images Captured: 1

Visual Observations:
- Red, flat patches
- Slightly raised borders
...

ASSESSMENT
==========
Differential Diagnoses:
1. Contact Dermatitis (L25.9) - Confidence: 75%
   Supporting Evidence:
   - Red, itchy rash
   - Flat patches with raised borders
   ...
```

### 3. PDF Generation

PDFs are generated server-side using ReportLab with:
- Professional formatting
- Page headers and footers
- Proper pagination
- Consistent styling
- Downloadable as `.pdf` files

**File naming**: `medical-patient-summary-{consultation_id}.pdf` or `medical-physician-report-{consultation_id}.pdf`

## Frontend Integration

### Components

#### ReportViewer Component
**File**: `components/kiosk/report-viewer.tsx`

Modal component that displays formatted text reports with:
- Smart text formatting (headers, lists, key-value pairs)
- Download button
- Responsive design
- Accessibility features

#### Consultation Screen
**File**: `components/kiosk/consultation-screen.tsx`

Integrates reports with:
- Floating report button (appears when consultation exists)
- Report menu modal for choosing report type
- View and Download options
- Error handling and user feedback

### API Client Methods

**File**: `lib/backend-api.ts`

```typescript
// Fetch formatted text report
async getTextReport(
  consultationId: string,
  reportType: 'patient' | 'physician' = 'patient'
): Promise<ApiResponse<{ report_text: string }>>

// Generate and download PDF
async generateAndDownloadPDF(
  consultationId: string,
  reportType: 'patient' | 'physician' = 'physician'
): Promise<{ success: boolean; error?: string }>
```

## Backend Implementation

### Services

#### ReportService
**File**: `backend/app/services/report_service.py`

Core service with methods:
- `generate_patient_report()` - Creates patient-friendly summary
- `generate_physician_report()` - Creates formal SOAP documentation
- `generate_pdf_report()` - Converts report to PDF using ReportLab

### API Endpoints

**File**: `backend/app/routers/report.py`

```python
# Generate patient report (text)
POST /report/patient
Body: { "consultation_id": "uuid", "language": "en" }

# Generate physician report (text)
POST /report/physician
Body: { "consultation_id": "uuid", "language": "en" }

# Download PDF report
GET /report/{consultation_id}/pdf
Query params: ?report_type=patient|physician
```

## Testing

### Test Endpoint

To test report functionality without completing a full consultation:

```bash
# Create sample consultation
curl -X POST http://localhost:8000/test/create-sample-consultation

# Returns:
{
  "status": "created",
  "consultation_id": "97e13cb5-a978-422e-9ed6-fd7074982105",
  "message": "Sample consultation created. You can now test reports..."
}
```

### Test in Frontend

1. Start the frontend: `pnpm dev`
2. Open http://localhost:3000
3. Start a consultation (the test consultation ID will be available)
4. Click the report button (top-right, FileText icon)
5. Choose Patient Summary or Physician Report
6. Click "View" to see formatted report or "Download PDF" to save

### Verify PDF Generation

```bash
# Generate and save PDF
curl -o test-report.pdf http://localhost:8000/report/{consultation_id}/pdf

# Verify it's a valid PDF
file test-report.pdf
# Output: test-report.pdf: PDF document, version 1.4, 1 page(s)
```

## Error Handling

The system handles various error cases:

### Frontend Errors
- **No consultation ID**: Shows "No consultation available" message
- **404 Not Found**: "Consultation report is not ready yet. Please complete the consultation first."
- **Network errors**: "Failed to connect to the server. Please check your connection."
- **PDF generation failures**: User-friendly error messages with TTS feedback

### Backend Errors
- **Missing consultation**: Returns 404 with clear error message
- **Incomplete SOAP data**: Returns 400 with details about missing sections
- **PDF generation failures**: Returns 500 with error details

## Language Support

Reports can be generated in multiple languages:
- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)

Pass the `language` parameter in the request:
```json
{
  "consultation_id": "uuid",
  "language": "hi"
}
```

## Technical Details

### Data Flow

```
┌─────────────────┐
│  Frontend UI    │
│  (User clicks   │
│  report button) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend API    │
│  /report/*      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ReportService   │
│ - Load SOAP     │
│ - Format text   │
│ - Generate PDF  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response       │
│  (text or PDF   │
│   blob)         │
└─────────────────┘
```

### SOAP Data Requirements

For a report to be generated, the consultation must have:

**Minimum Requirements**:
- `consultation_id`
- `current_stage = COMPLETED`
- `subjective.chief_complaint`
- `assessment.differential_diagnoses` (at least one)
- `plan.patient_guidance`

**Optional but Recommended**:
- `objective.images` (captured photos)
- `objective.visual_observations`
- `assessment.rag_sources` (similar cases)
- `plan.recommended_tests`

### PDF Styling

ReportLab configuration:
- **Font**: Helvetica (regular and bold)
- **Page size**: Letter (8.5" x 11")
- **Margins**: 1 inch on all sides
- **Header**: Logo and title
- **Footer**: Page numbers and disclaimers
- **Sections**: Clear visual separation with headings

## Security Considerations

- Reports contain sensitive medical information
- PDF generation happens server-side (no client-side access to full SOAP data)
- Downloads use temporary blob URLs (auto-revoked after use)
- No persistent storage of generated PDFs
- Reports are tied to consultation IDs (access control should be implemented)

## Future Enhancements

Potential improvements:
- [ ] Email delivery of reports
- [ ] Digital signatures for physicians
- [ ] QR codes linking to online reports
- [ ] Printable prescriptions (when approved by physician)
- [ ] Integration with EMR systems
- [ ] Report versioning and audit trail
- [ ] Custom report templates per facility
