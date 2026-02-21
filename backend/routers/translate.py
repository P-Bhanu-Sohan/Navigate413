import logging
from fastapi import APIRouter
from models.schemas import TranslateRequest, TranslateResponse
from db.mongo import get_db
from agents.specialized_agents import translation_agent
from agents.base_agents import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["translate"])


@router.post("/translate", response_model=TranslateResponse)
async def translate_summary(request: TranslateRequest):
    """Translate summary to target language."""
    try:
        db = get_db()
        session_id = request.session_id
        
        # Retrieve analysis results
        doc = await db["documents_metadata"].find_one({"_id": session_id})
        if not doc or "analysis_results" not in doc:
            return TranslateResponse(
                language=request.target_language,
                translated_text="No analysis found for this session",
                context_note="Student-friendly institutional explanation translated from English."
            )
        
        analysis = doc["analysis_results"]
        
        # Build state for translation agent
        state: AgentState = {
            "session_id": session_id,
            "raw_text": "",
            "domain": analysis.get("domain", "unknown"),
            "language": request.target_language,
            "clauses": [],
            "risk_output": analysis.get("risk_output", {}),
            "resources": [],
            "translation": None,
            "scenario": None,
            "error": None
        }
        
        # Run translation agent
        state = await translation_agent(state)
        
        return TranslateResponse(
            language=request.target_language,
            translated_text=state.get("translation", "Translation failed"),
            context_note="Student-friendly institutional explanation translated from English."
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise
