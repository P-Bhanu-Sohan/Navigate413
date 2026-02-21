import logging
from fastapi import APIRouter
from models.schemas import SimulateRequest, SimulateResponse
from db.mongo import get_db
from agents.specialized_agents import scenario_agent
from agents.base_agents import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["simulate"])


@router.post("/simulate", response_model=SimulateResponse)
async def simulate_scenario(request: SimulateRequest):
    """Simulate financial/contractual scenario."""
    try:
        db = get_db()
        session_id = request.session_id
        
        # Retrieve analysis results
        doc = await db["documents_metadata"].find_one({"_id": session_id})
        if not doc or "analysis_results" not in doc:
            return SimulateResponse(
                scenario=request.scenario,
                exposure_estimate=0.0,
                formula_used="Unknown",
                explanation="No analysis found for this session",
                caveats=["This is an estimate only. Consult Student Legal Services for formal advice."]
            )
        
        analysis = doc["analysis_results"]
        
        # Build state for scenario agent
        scenario_dict = {
            "scenario": request.scenario,
            "parameters": request.parameters.dict()
        }
        
        state: AgentState = {
            "session_id": session_id,
            "raw_text": "",
            "domain": analysis.get("domain", "unknown"),
            "language": "en",
            "clauses": [],
            "risk_output": analysis.get("risk_output", {}),
            "resources": [],
            "translation": None,
            "scenario": scenario_dict,
            "error": None
        }
        
        # Run scenario agent
        state = await scenario_agent(state)
        
        scenario_result = state.get("scenario", {})
        
        return SimulateResponse(
            scenario=scenario_result.get("scenario", request.scenario),
            exposure_estimate=scenario_result.get("exposure_estimate", 0.0),
            formula_used=scenario_result.get("formula_used", "Unknown"),
            explanation=scenario_result.get("explanation", "Simulation failed"),
            caveats=scenario_result.get("caveats", ["This is an estimate only. Consult Student Legal Services for formal advice."])
        )
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise
