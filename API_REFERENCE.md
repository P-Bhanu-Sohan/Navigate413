# Navigate413 API Reference

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently anonymous. Sessions are identified by `session_id` (UUID v4).

## Endpoints

### 1. Upload Document
Upload a PDF document for processing.

**Request:**
```http
POST /api/upload
Content-Type: multipart/form-data

file: <binary PDF data>
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "financial_aid_letter.pdf",
  "status": "processing",
  "upload_timestamp": "2025-04-14T10:00:00Z"
}
```

**Status Codes:**
- 200: Upload successful, processing started
- 400: Invalid file format
- 413: File too large (>50MB)
- 422: File unreadable/unprocessable

---

### 2. Analyze Document
Get comprehensive risk analysis of an uploaded document.

**Request:**
```http
POST /api/analyze
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "en"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "domain": "finance|visa|housing|unknown",
  "risk_score": 0.74,
  "risk_level": "LOW|MEDIUM|HIGH",
  "clauses": [
    {
      "clause_id": "c1",
      "text": "Failure to maintain enrollment...",
      "risk_contribution": 0.4,
      "flag": "ENROLLMENT_REQUIREMENT",
      "plain_explanation": "You must stay enrolled full-time or your aid is cancelled."
    }
  ],
  "obligations": [
    "Maintain 12+ credit hours",
    "File FAFSA by March 1"
  ],
  "deadlines": [
    "March 1, 2026"
  ],
  "resources": [
    {
      "name": "UMass Financial Aid Office",
      "url": "https://www.umass.edu/financialaid",
      "relevance": 0.91,
      "description": "..."
    }
  ],
  "summary": "This document contains high financial exposure due to enrollment conditions and a hard aid cancellation deadline."
}
```

**Risk Levels:**
- `LOW`: Risk score < 0.4
- `MEDIUM`: Risk score 0.4-0.7
- `HIGH`: Risk score > 0.7

**Domains:**
- `finance`: Financial aid, scholarships, loans
- `visa`: Student visas, work authorization
- `housing`: Lease agreements, housing contracts
- `unknown`: Could not determine domain

**Status Codes:**
- 200: Analysis successful
- 404: Session not found
- 409: Document still processing (retry after a few seconds)

---

### 3. Translate Summary
Translate the plain-language summary to another language.

**Request:**
```http
POST /api/translate
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_language": "Spanish"
}
```

**Response:**
```json
{
  "language": "Spanish",
  "translated_text": "Este documento contiene una alta exposición financiera...",
  "context_note": "Student-friendly institutional explanation translated from English."
}
```

**Supported Languages:**
- English (en)
- Spanish (es)
- Mandarin (zh)
- Hindi (hi)

---

### 4. Simulate Scenario
Simulate a financial or contractual scenario with specific parameters.

**Request:**
```http
POST /api/simulate
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario": "early_termination",
  "parameters": {
    "months_remaining": 8,
    "penalty_rate_per_month": 250,
    "base_penalty": 500,
    "additional_params": null
  }
}
```

**Response:**
```json
{
  "scenario": "early_termination",
  "exposure_estimate": 2500.00,
  "formula_used": "base_penalty + (months_remaining × penalty_rate)",
  "explanation": "Terminating the lease 8 months early would cost approximately $2,500 based on the contract terms.",
  "caveats": [
    "This is an estimate only. Consult Student Legal Services for formal advice."
  ]
}
```

**Scenario Types:**
- `early_termination`: Lease early termination costs
- `enrollment_change`: Financial aid impact of enrollment changes

---

### 5. Search Campus Resources
Find relevant UMass services and resources.

**Request:**
```http
GET /api/resources?query=financial+aid&domain=finance&top_k=3
```

**Query Parameters:**
- `query` (required): Search query
- `domain` (optional): Filter by domain (finance|visa|housing)
- `top_k` (optional): Number of results (1-10, default 3)

**Response:**
```json
{
  "results": [
    {
      "name": "Student Legal Services",
      "description": "Free legal consultations for UMass students",
      "url": "https://www.umass.edu/slso",
      "relevance": 0.93
    }
  ]
}
```

---

### 6. Get Session Results
Retrieve full stored analysis and metadata for a session.

**Request:**
```http
GET /api/session/{session_id}
```

**Response:**
```json
{
  "_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_session_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "financial_aid_letter.pdf",
  "upload_timestamp": "2025-04-14T10:00:00Z",
  "processed_flag": true,
  "domain": "finance",
  "raw_text": "...",
  "analysis_results": { /* full analysis output */ }
}
```

---

## Error Responses

All errors return JSON with this structure:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

### Common Errors

| Code | Message | Solution |
|------|---------|----------|
| 404 | Session not found | Use correct session_id from upload response |
| 409 | Document still processing | Wait and retry after 2-5 seconds |
| 422 | Text extraction failed | Upload a text-based (not scanned) PDF |
| 500 | Internal server error | Check backend logs |

---

## Rate Limits

Currently none implemented (MVP). Production deployment should enforce:
- 100 uploads/hour per IP
- 1000 analyses/hour per IP

---

## Session Lifecycle

1. **Upload** → Receive `session_id`
2. **Check Status** → `GET /api/session/{session_id}` until `processed_flag: true`
3. **Analyze** → `POST /api/analyze` with `session_id`
4. **Translate** → `POST /api/translate` with `session_id` (optional)
5. **Simulate** → `POST /api/simulate` with `session_id` (optional)
6. **Search** → `GET /api/resources` for campus services

---

## Example Workflow

### cURL Examples

```bash
# 1. Upload a document
curl -X POST http://localhost:8000/api/upload \
  -F "file=@financial_aid_letter.pdf"

# 2. Poll for processing (wait 2-5 seconds)
curl http://localhost:8000/api/session/{session_id}

# 3. Analyze (once processed_flag is true)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_id": "{session_id}", "language": "en"}'

# 4. Translate
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"session_id": "{session_id}", "target_language": "Spanish"}'

# 5. Run scenario simulation
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "{session_id}",
    "scenario": "early_termination",
    "parameters": {
      "months_remaining": 8,
      "penalty_rate_per_month": 250,
      "base_penalty": 500
    }
  }'
```

---

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok"
}
```
