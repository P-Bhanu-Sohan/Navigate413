import logging
from fastapi import APIRouter
from models.schemas import ScenarioRequest, ScenarioResponse
from db.mongo import get_db
from agents.specialized_agents import scenario_agent
from agents.base_agents import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["simulate"])


@router.post("/scenario", response_model=ScenarioResponse)
async def simulate_scenario(request: ScenarioRequest):
    """Simulate a scenario to help student understand implications."""
    try:
        db = get_db()
        session_id = request.session_id
        
        # Retrieve analysis results
        doc = await db["documents_metadata"].find_one({"_id": session_id})
        if not doc or "analysis_results" not in doc:
            return ScenarioResponse(
                scenario=request.scenario_description,
                what_happens="No analysis found for this session. Please upload and analyze a document first.",
                implications=["Analysis required"],
                suggested_steps=["Upload a document and run analysis"],
                caveats=["Document analysis is required before scenario simulation"]
            )
        
        analysis = doc["analysis_results"]
        
        # Build state for scenario agent
        state: AgentState = {
            "session_id": session_id,
            "raw_text": "",
            "domain": analysis.get("domain", "unknown"),
            "language": "en",
            "clauses": analysis.get("obligations", []),
            "obligations": analysis.get("obligations", []),
            "financial_details": analysis.get("risk_assessment", ""),
            "housing_details": analysis.get("risk_assessment", ""),
            "visa_details": analysis.get("risk_assessment", ""),
            "risk_assessment": analysis.get("risk_assessment", ""),
            "red_flags": analysis.get("red_flags", []),
            "resources": [],
            "translation": None,
            "scenario": request.scenario_description,
            "error": None
        }
        
        # Run scenario agent
        state = await scenario_agent(state)
        
        scenario_text = state.get("scenario", "")
        
        # Parse scenario response into components
        what_happens = scenario_text.split('\n')[0] if scenario_text else "Scenario analysis complete"
        
        implications = []
        suggested_steps = []
        
        lines = scenario_text.split('\n')
        for line in lines:
            if "impact" in line.lower() or "result" in line.lower():
                implications.append(line.strip())
            if "should" in line.lower() or "recommend" in line.lower():
                suggested_steps.append(line.strip())
        
        return ScenarioResponse(
            scenario=request.scenario_description,
            what_happens=what_happens,
            implications=implications[:3] if implications else ["Review your obligations carefully"],
            suggested_steps=suggested_steps[:3] if suggested_steps else ["Consult with relevant campus office"],
            caveats=[
                "This is a simulated scenario based on document analysis.",
                "Consult Student Legal Services or relevant office for formal guidance."
            ]
        )
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise
