# Navigate413 - Document Analysis Platform for UMass Students

Navigate413 is a swarm-style multi-agent document reasoning platform that converts complex institutional documents into structured risk scores, scenario simulations, and campus resource referrals.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB Atlas account
- Gemini API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file in the `backend` directory:
```env
GEMINI_API_KEY=your_key_here
MONGODB_URI=mongodb+srv://...
```

Run the backend:
```bash
cd backend
uvicorn main:app --reload
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## Architecture

- **Backend**: FastAPI with LangGraph agent orchestration
- **AI**: Google Gemini 1.5 Flash with structured output
- **Database**: MongoDB Atlas with Vector Search
- **Frontend**: React + Tailwind CSS

## Features

✅ **Document Upload** - PDF and scanned document support
✅ **Risk Analysis** - Financial, housing, and visa domain analysis
✅ **Plain Language Explanations** - Student-friendly summaries
✅ **Scenario Simulation** - Deterministic financial exposure modeling
✅ **Translation** - Multi-language support
✅ **Resource Referrals** - Semantic search for campus services

## Project Structure

```
navigate413/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── agents/                 # LangGraph agents
│   ├── routers/                # API endpoints
│   ├── db/                     # Database connectivity
│   ├── pipelines/              # Text extraction & routing
│   ├── models/                 # Pydantic schemas & risk models
│   └── tools/                  # Retrieval tools
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page layouts
│   │   └── main.jsx            # Entry point
│   └── index.html              # HTML template
└── docker-compose.yml          # Container orchestration
```

## API Endpoints

- `POST /api/upload` - Upload document
- `POST /api/analyze` - Analyze document
- `POST /api/translate` - Translate summary
- `POST /api/simulate` - Scenario simulation
- `GET /api/resources` - Search campus resources
- `GET /api/session/{session_id}` - Get session results

## Development Notes

- All agents use synchronous/blocking wrappers around async functions for LangGraph compatibility
- Vector embeddings are generated using Gemini's `text-embedding-004`
- Risk scores use formula-based calculation, not ML models
- Document text extraction falls back from pdfplumber to pytesseract for scanned docs

## Deployment

Docker image is provided. For DigitalOcean App Platform:

1. Push to GitHub
2. Connect repository to DigitalOcean App Platform
3. Set environment variables
4. Deploy

## License

Internal project for UMass Amherst
