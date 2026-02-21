import logging
from fastapi import APIRouter
from models.schemas import AnalyzeRequest, AnalyzeResponse, Clause, Resource
from db.mongo import get_db
from agents.graph import workflow
from agents.base_agents import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(request: AnalyzeRequest):
    """Analyze document and return risk assessment."""
    try:
        db = get_db()
        session_id = request.session_id
        language = request.language or "en"
        
        # Retrieve document metadata and raw text
        doc = await db["documents_metadata"].find_one({"_id": session_id})
        if not doc:
            return AnalyzeResponse(
                session_id=session_id,
                domain="unknown",
                risk_score=0.0,
                risk_level="LOW",
                clauses=[],
                obligations=[],
                deadlines=[],
                resources=[],
                summary="Document not found"
            )
        
        if not doc.get("processed_flag"):
            return AnalyzeResponse(
                session_id=session_id,
                domain="unknown",
                risk_score=0.0,
                risk_level="LOW",
                clauses=[],
                obligations=[],
                deadlines=[],
                resources=[],
                summary="Document still processing. Please retry in a moment."
            )
        
        raw_text = doc.get("raw_text", "")
        
        # Initialize agent state
        initial_state: AgentState = {
            "session_id": session_id,
            "raw_text": raw_text,
            "domain": "unknown",
            "language": language,
            "clauses": [],
            "risk_output": {},
            "resources": [],
            "translation": None,
            "scenario": None,
            "error": None
        }
        
        # Run the workflow (synchronous)
        final_state = workflow.invoke(initial_state)
        
        # Extract results
        domain = final_state.get("domain", "unknown")
        risk_output = final_state.get("risk_output", {})
        clauses_raw = final_state.get("clauses", [])
        resources_raw = final_state.get("resources", [])
        
        # Build response
        clauses = []
        for i, clause in enumerate(clauses_raw):
            clauses.append(Clause(
                clause_id=f"c{i}",
                text=clause.get("text", ""),
                risk_contribution=clause.get("risk_contribution", 0.0),
                flag=clause.get("flag", ""),
                plain_explanation=clause.get("explanation", "")
            ))
        
        resources = []
        for res in resources_raw:
            resources.append(Resource(
                name=res.get("resource_name", ""),
                url=res.get("url", ""),
                relevance=res.get("score", 0.0),
                description=res.get("description", "")
            ))
        
        # Store analysis result
        await db["documents_metadata"].update_one(
            {"_id": session_id},
            {
                "$set": {
                    "domain": domain,
                    "analysis_results": final_state
                }
            }
        )
        
        return AnalyzeResponse(
            session_id=session_id,
            domain=domain,
            risk_score=risk_output.get("risk_score", 0.0),
            risk_level=risk_output.get("risk_level", "LOW"),
            clauses=clauses,
            obligations=risk_output.get("obligations", []),
            deadlines=risk_output.get("deadlines", []),
            resources=resources,
            summary=risk_output.get("summary", "")
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise
