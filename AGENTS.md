# Navigate413 — Full Technical PRD

---

## 1. Project Overview & Goals

Navigate413 is a swarm-style multi-agent document reasoning platform built for UMass Amherst students. It converts complex institutional documents — financial aid letters, visa notices, housing leases, academic standing letters — into structured risk scores, scenario simulations, multilingual explanations, and campus resource referrals. The system is **not a chatbot**; it is a deterministic + probabilistic reasoning engine layered over LangGraph, Gemini, MongoDB Atlas, and FastAPI. The MVP targets a 12–14 hour build window with a DigitalOcean deployment and a clean React dashboard.

---

## 2. Tech Stack Reference

| Layer | Technology | Purpose |
|---|---|---|
| Backend API | FastAPI (Python 3.11+) | REST endpoints, file handling, agent orchestration entry |
| AI Orchestration | LangGraph | Stateful multi-agent swarm graph |
| LLM + Embeddings | Gemini 1.5 Flash / `text-embedding-004` | Structured generation + vector embedding |
| Vector DB | MongoDB Atlas (Vector Search) | Clause embeddings, campus resource retrieval |
| Document DB | MongoDB Atlas | Session metadata, processing state |
| File Storage | DigitalOcean Spaces (S3-compatible) | Temporary upload storage |
| OCR / Extraction | `pdfplumber` + `pytesseract` | Text extraction from PDFs and scanned docs |
| Frontend | React + Tailwind + shadcn/ui | Dashboard, file upload, risk visualization |
| Deployment | DigitalOcean App Platform | Containerized FastAPI + React |
| Optional | ElevenLabs TTS | Voice output of simplified explanations |

---

## 3. Repository Structure

```
navigate413/
├── backend/
│   ├── main.py                    # FastAPI app entrypoint
│   ├── routers/
│   │   ├── upload.py              # POST /upload
│   │   ├── analyze.py             # POST /analyze
│   │   ├── translate.py           # POST /translate
│   │   ├── simulate.py            # POST /simulate
│   │   └── resources.py           # GET /resources
│   ├── agents/
│   │   ├── graph.py               # LangGraph swarm definition
│   │   ├── finance_agent.py
│   │   ├── visa_agent.py
│   │   ├── housing_agent.py
│   │   ├── translation_agent.py
│   │   ├── scenario_agent.py
│   │   └── rag_agent.py
│   ├── tools/
│   │   └── retrieval_tool.py      # GlobalRetrievalTool abstraction
│   ├── pipelines/
│   │   ├── extractor.py           # PDF/OCR text extraction
│   │   └── intent_router.py       # Domain classification
│   ├── models/
│   │   ├── schemas.py             # Pydantic request/response models
│   │   └── risk_models.py         # Deterministic scoring formulas
│   ├── db/
│   │   ├── mongo.py               # MongoDB Atlas client
│   │   └── vector_store.py        # Atlas Vector Search wrapper
│   └── config.py                  # Env vars, constants
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadZone.jsx
│   │   │   ├── RiskScoreCard.jsx
│   │   │   ├── ClauseBreakdown.jsx
│   │   │   ├── ScenarioSimulator.jsx
│   │   │   ├── TranslationPanel.jsx
│   │   │   └── ResourceLinks.jsx
│   │   └── pages/
│   │       └── Dashboard.jsx
└── docker-compose.yml
```

---

## 4. Full API Endpoint Specification

### `POST /api/upload`
Accepts a multipart file upload. Stores the file in DigitalOcean Spaces, creates a session document in MongoDB, triggers async text extraction, and returns a `session_id`.

**Request:** `multipart/form-data` — `file: File`

**Response:**
```json
{
  "session_id": "uuid-v4",
  "file_name": "financial_aid_letter.pdf",
  "status": "processing",
  "upload_timestamp": "2025-04-14T10:00:00Z"
}
```

**Implementation notes:** Use `boto3` with DigitalOcean Spaces endpoint. Store to `documents_metadata_collection`. Kick off background task via FastAPI `BackgroundTasks` to run the extraction pipeline.

---

### `POST /api/analyze`
The core endpoint. Accepts a `session_id`, retrieves the extracted text, runs the intent router, dispatches to the LangGraph swarm, and returns structured agent outputs.

**Request:**
```json
{ "session_id": "uuid-v4", "language": "en" }
```

**Response:**
```json
{
  "session_id": "uuid-v4",
  "domain": "finance",
  "risk_score": 0.74,
  "risk_level": "HIGH",
  "clauses": [
    {
      "clause_id": "c1",
      "text": "Failure to maintain enrollment...",
      "risk_contribution": 0.4,
      "flag": "ENROLLMENT_REQUIREMENT",
      "plain_explanation": "You must stay enrolled full-time or your aid is cancelled."
    }
  ],
  "obligations": ["Maintain 12+ credit hours", "File FAFSA by March 1"],
  "deadlines": ["March 1, 2026"],
  "resources": [
    { "name": "UMass Financial Aid Office", "url": "https://www.umass.edu/financialaid", "relevance": 0.91 }
  ],
  "summary": "This document contains high financial exposure due to enrollment conditions and a hard aid cancellation deadline."
}
```

---

### `POST /api/translate`
Takes a `session_id` and target language, runs the Translation Agent on the stored plain-language summary, and returns translated output.

**Request:**
```json
{ "session_id": "uuid-v4", "target_language": "Spanish" }
```

**Response:**
```json
{
  "language": "Spanish",
  "translated_text": "Este documento contiene una alta exposición financiera...",
  "context_note": "Student-friendly institutional explanation translated from English."
}
```

---

### `POST /api/simulate`
Accepts a `session_id` and scenario parameters. Runs the Scenario Agent's deterministic exposure model and returns computed financial/contractual exposure.

**Request:**
```json
{
  "session_id": "uuid-v4",
  "scenario": "early_termination",
  "parameters": {
    "months_remaining": 8,
    "penalty_rate_per_month": 250,
    "base_penalty": 500
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
  "caveats": ["This is an estimate only. Consult Student Legal Services for formal advice."]
}
```

---

### `GET /api/resources`
Performs a semantic search against `campus_resources_vector_collection` and returns relevant UMass services.

**Query params:** `query=string&domain=finance|visa|housing&top_k=3`

**Response:**
```json
{
  "results": [
    {
      "resource_name": "Student Legal Services",
      "description": "Free legal consultations for UMass students",
      "url": "https://www.umass.edu/slso",
      "domain": "housing",
      "similarity_score": 0.93
    }
  ]
}
```

---

### `GET /api/session/{session_id}`
Retrieves the full stored analysis result for a given session.

---

## 5. LangGraph Swarm Architecture

The LangGraph graph has the following node/edge structure:

```
START
  └─► intent_router_node
        ├─► finance_agent_node
        ├─► visa_agent_node
        └─► housing_agent_node
              └─► rag_agent_node (all paths converge here)
                    ├─► translation_agent_node (if language != "en")
                    └─► scenario_agent_node (if scenario flag set)
                          └─► END (aggregated output)
```

The `intent_router_node` classifies document domain using a zero-shot Gemini prompt with forced JSON output: `{ "domain": "finance|visa|housing|unknown" }`. State is a `TypedDict` passed through the graph containing `raw_text`, `session_id`, `domain`, `clauses`, `risk_output`, `resources`, `translation`, and `scenario`.

Each domain agent calls the `GlobalRetrievalTool` with a generated semantic query, injects top-K context chunks, and then invokes Gemini with a structured output prompt enforcing a Pydantic schema. All agents return their output by merging into the shared graph state using `operator.add` reducers where appropriate.

---

## 6. GlobalRetrievalTool Implementation

```python
def GlobalRetrievalTool(query_text: str, domain_filter: str = None, campus: str = "UMass", top_k: int = 3):
    embedding = gemini_embed(query_text)  # text-embedding-004
    pipeline = [
        {
            "$vectorSearch": {
                "index": "clause_vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 100,
                "limit": top_k,
                "filter": {"domain": domain_filter} if domain_filter else {}
            }
        },
        { "$project": { "clause_text": 1, "domain": 1, "risk_metadata": 1, "score": { "$meta": "vectorSearchScore" } } }
    ]
    return list(embeddings_collection.aggregate(pipeline))
```

All six agents import this single function. No agent implements its own retrieval. This prevents drift and ensures consistent embedding behavior.

---

## 7. Risk Scoring Models

### Finance Agent Risk Score
```
Risk Score = (0.4 × Financial Exposure Indicator)
           + (0.3 × Penalty Escalation Indicator)
           + (0.3 × Deadline Sensitivity Indicator)
```
Each indicator is computed heuristically: Gemini extracts raw clause data, Python code normalizes values 0–1 based on thresholds (e.g., exposure > $5,000 = 1.0, < $500 = 0.1). Final score maps to LOW (< 0.4), MEDIUM (0.4–0.7), HIGH (> 0.7).

### Housing Agent Risk Score
```
Risk Score = (0.35 × Termination Penalty Indicator)
           + (0.35 × Liability Clause Indicator)
           + (0.30 × Payment Obligation Indicator)
```

### Visa/Compliance Risk Level
Visa agent uses categorical classification rather than a continuous score: `COMPLIANT`, `AT_RISK`, `VIOLATION_LIKELY`. Gemini is prompted to detect authorization restrictions, enrollment requirements, and work eligibility language.

### Scenario Simulation Formula
```
Exposure Estimate = base_penalty + (remaining_duration × penalty_rate)
```
This is fully deterministic — no LLM involved. Input params come from either the document (auto-extracted by the housing agent) or user-provided scenario parameters via the `/simulate` endpoint.

---

## 8. MongoDB Schema Design

### `documents_metadata_collection`
```json
{
  "_id": "uuid-v4",
  "user_session_id": "uuid-v4",
  "file_name": "lease_spring2026.pdf",
  "storage_url": "https://spaces.nyc3.digitaloceanspaces.com/...",
  "upload_timestamp": "ISO8601",
  "processed_flag": true,
  "domain": "housing",
  "analysis_results": { /* full agent output embedded */ }
}
```

### `Embeddings`
```json
{
  "_id": "ObjectId",
  "session_id": "uuid-v4",
  "clause_text": "In the event of early termination...",
  "embedding": [0.021, -0.104, ...],  /* 768-dim vector */
  "domain": "housing",
  "risk_metadata": { "flag": "TERMINATION_PENALTY", "severity": "HIGH" }
}
```

### `campus_resources_vector_collection`
Pre-seeded at startup. Contains embedded descriptions of: Financial Aid Office, Student Legal Services Office, International Programs Office, Dean of Students, Housing Support Services, Bursar's Office. Atlas Vector Search index name: `campus_resource_index`.

---

## 9. Text Extraction Pipeline

1. **Upload received** → file saved temporarily to DigitalOcean Spaces.
2. **`pdfplumber`** attempts text extraction. If extracted text is < 100 characters (scanned doc), fall back to **`pytesseract`** OCR on page images rendered via `pdf2image`.
3. Extracted text is stored to `documents_metadata_collection` under `raw_text`.
4. Text is split into clauses using sentence boundary detection (`nltk.sent_tokenize`) grouped into ~3-sentence chunks.
5. Each chunk is embedded via `text-embedding-004` and inserted into `Embeddings` collection.
6. `processed_flag` set to `true`. Session ready for `/analyze`.

---

## 10. Gemini Prompt Engineering Strategy

All agents use **structured JSON output prompting** with explicit schema injection. Every prompt includes: (1) system role definition, (2) retrieved context chunks from `GlobalRetrievalTool`, (3) document clause text, (4) JSON output schema, and (5) instruction to output only valid JSON. Example finance agent system prompt snippet:

```
You are a financial risk analysis agent specializing in university financial aid documents.
Analyze the following document clauses and return ONLY a JSON object matching this schema:
{ "risk_indicators": {...}, "obligations": [...], "deadlines": [...], "plain_explanation": "..." }
Do not include any text outside the JSON object.
```

Gemini 1.5 Flash is used for all agents (fast, cost-effective). Gemini 1.5 Pro is reserved for the optional scenario agent when complex multi-clause reasoning is needed.

---

## 11. Frontend Dashboard Components

The React frontend communicates exclusively with the FastAPI backend. Key component behaviors:

**`UploadZone.jsx`** — Drag-and-drop PDF upload using `react-dropzone`. On submit, calls `POST /api/upload`, stores `session_id` in local state, polls `GET /api/session/{id}` every 2 seconds until `processed_flag = true`, then triggers `/analyze`.

**`RiskScoreCard.jsx`** — Displays domain, numeric risk score as a gauge (0–1), color-coded risk level badge (green/yellow/red), and a one-sentence summary. Uses Tailwind + shadcn `Badge` and `Progress` components.

**`ClauseBreakdown.jsx`** — Renders each flagged clause in an expandable accordion. Each row shows: clause text snippet, risk flag label, contribution weight, and plain-language explanation.

**`ScenarioSimulator.jsx`** — Form inputs for scenario type and parameters. On submit, calls `POST /api/simulate` and renders the returned exposure estimate with the formula breakdown.

**`TranslationPanel.jsx`** — Language selector dropdown (English, Spanish, Mandarin, Hindi). On language change, calls `POST /api/translate` and displays the translated summary in a card.

**`ResourceLinks.jsx`** — Displays the top-3 campus resources returned by the RAG agent, each with name, description, and direct URL button.

---

## 12. Iterative Development Roadmap (12–14 Hour MVP)

### Phase 1 — Foundation (Hours 0–3)
Set up the FastAPI app skeleton with all routers registered but returning stubs. Configure MongoDB Atlas connection (`pymongo` + Motor for async). Create DigitalOcean Spaces bucket and verify `boto3` connectivity. Implement `POST /api/upload` end-to-end: file → Spaces → metadata document in MongoDB. Implement the text extraction pipeline (`pdfplumber` → `pytesseract` fallback). Write `GlobalRetrievalTool` with the Atlas Vector Search pipeline and verify it returns results against pre-seeded campus resource data. **Milestone: file upload → extracted text stored in DB.**

### Phase 2 — Core Agent Logic (Hours 3–7)
Build the LangGraph graph in `graph.py`. Implement `intent_router_node` first and verify it correctly classifies sample documents. Implement `finance_agent_node` with full Gemini structured output + risk score computation. Implement `housing_agent_node` and `visa_agent_node` using the same pattern. Wire `rag_agent_node` to call `GlobalRetrievalTool` after domain agent and append resource results to state. Implement `POST /api/analyze` to invoke the graph and return the aggregated state as the response. **Milestone: upload a financial aid PDF, receive structured JSON risk output.**

### Phase 3 — Translation + Simulation (Hours 7–9)
Implement `translation_agent_node` with a simple Gemini prompt that takes the stored plain-language summary and translates to the target language. Wire to `POST /api/translate`. Implement `scenario_agent_node` with the deterministic formula and parameter parsing. Wire to `POST /api/simulate`. Seed `campus_resources_vector_collection` with 10–15 UMass resource descriptions and embed them. **Milestone: Spanish translation working; lease early-termination scenario returning dollar estimate.**

### Phase 4 — Frontend (Hours 9–12)
Scaffold React app with Vite. Build `UploadZone`, `RiskScoreCard`, and `ClauseBreakdown` components first — these cover the core user value. Add `ScenarioSimulator` and `TranslationPanel`. Connect all components to live backend endpoints. Implement polling loop for async processing status. Style with Tailwind — prioritize readability over aesthetics. **Milestone: full browser flow working end-to-end.**

### Phase 5 — Deployment + Polish (Hours 12–14)
Dockerize FastAPI backend (`Dockerfile` + `requirements.txt`). Push to DigitalOcean App Platform via GitHub integration. Deploy React frontend as a separate static site or bundled via the same app. Verify all endpoints reachable from production URL. Add error handling for failed extractions and LLM timeouts. Smoke test with three document types: financial aid letter, housing lease, I-20 notice. Record demo video. **Milestone: live URL, all three document types produce valid risk outputs.**

---

## 13. Error Handling & Edge Cases

Uploads that fail OCR extraction should return a `422 Unprocessable Entity` with `"error": "text_extraction_failed"` and advise the user to re-upload a text-based PDF. LangGraph agent nodes should be wrapped in `try/except` with fallback outputs that return a low-confidence result rather than crashing the graph — partial output is better than a 500 error during a demo. Gemini API failures should trigger a single retry with exponential backoff (1s, 2s) before returning a fallback. MongoDB connection failures should be caught at app startup and surfaced clearly. All LLM outputs must be validated against Pydantic schemas before being stored or returned — if Gemini returns malformed JSON, the agent should retry the prompt once with an explicit reminder to return only valid JSON.

---

## 14. Security & Data Handling Notes

Sessions are anonymous (no user authentication in MVP). `session_id` is a UUID v4 generated server-side and acts as an access token for the session. No PII is stored beyond the uploaded document. Uploaded files are deleted from DigitalOcean Spaces after processing completes (or after 24 hours via lifecycle policy). All MongoDB collections should use Atlas IP access list restricted to the DigitalOcean App Platform outbound IPs. API keys (Gemini, MongoDB, DigitalOcean) must be stored as environment variables — never hardcoded. In production, add `python-jose` JWT authentication before any real student data is handled.

---

## 15. Stretch Goals (Post-MVP)

If core features are complete before the deadline, implement in this priority order: (1) ElevenLabs TTS on the plain-language summary for accessibility, and (2) a shareable report export as a structured PDF with risk scores, obligations checklist, and resource links — useful for students bringing Navigate413 output to an advisor meeting.