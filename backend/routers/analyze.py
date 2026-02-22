import logging
from fastapi import APIRouter
from models.schemas import AnalyzeRequest, AnalyzeResponse, Clause, Resource, RedFlag, SimulationOption
from db.mongo import get_db
from agents.graph import run_analysis_workflow
from agents.base_agents import AgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(request: AnalyzeRequest):
    """Analyze document using reasoning-based agents."""
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
                risk_reasoning="Document not found in system.",
                clauses=[],
                obligations=[],
                deadlines=[],
                red_flags=[],
                resources=[],
                summary="Document not found",
                recommendations=[]
            )
        
        if not doc.get("processed_flag"):
            return AnalyzeResponse(
                session_id=session_id,
                domain="unknown",
                risk_score=0.0,
                risk_level="LOW",
                risk_reasoning="Document is still being processed.",
                clauses=[],
                obligations=[],
                deadlines=[],
                red_flags=[],
                resources=[],
                summary="Document still processing. Please retry in a moment.",
                recommendations=[]
            )
        
        raw_text = doc.get("raw_text", "")
        
        # Run the reasoning-based agent workflow
        final_state = await run_analysis_workflow(session_id, raw_text)
        
        # Extract results from agent analysis
        domain = final_state.get("domain", "unknown")
        risk_assessment = final_state.get("risk_assessment", "")
        red_flags_raw = final_state.get("red_flags", [])
        clauses_raw = final_state.get("clauses", [])
        resources_raw = final_state.get("resources", [])
        obligations = final_state.get("obligations", [])
        
        # Extract risk level from assessment text and calculate numeric score
        risk_level = "MEDIUM"  # Default
        risk_score = 0.5  # Default 50%
        
        if "high" in risk_assessment.lower():
            risk_level = "HIGH"
            risk_score = 0.75  # 75% for HIGH
        elif "low" in risk_assessment.lower():
            risk_level = "LOW"
            risk_score = 0.25  # 25% for LOW
        else:
            risk_level = "MEDIUM"
            risk_score = 0.5  # 50% for MEDIUM
        
        # Build clause objects
        clauses = []
        for i, clause in enumerate(clauses_raw[:10]):  # Limit to 10
            clauses.append(Clause(
                clause_id=f"c{i}",
                text=clause if isinstance(clause, str) else clause.get("text", ""),
                explanation=clause.get("explanation", "") if isinstance(clause, dict) else "",
                relevance_to_student=clause.get("relevance", "") if isinstance(clause, dict) else ""
            ))
        
        # Build red flag objects
        red_flags = []
        for flag in red_flags_raw[:5]:  # Limit to 5
            red_flags.append(RedFlag(
                description=flag,
                reasoning="Identified during document analysis",
                suggested_action="Review this item carefully with relevant support office"
            ))
        
        # Build resource objects
        resources = []
        for res in resources_raw:
            if isinstance(res, dict):
                resources.append(Resource(
                    name=res.get("name", res.get("query", "Resource")),
                    url=res.get("url", ""),
                    reason_relevant=res.get("reason", res.get("context", "Relevant to your situation")),
                    description=res.get("description")
                ))
        
        # Extract recommendations from analysis
        recommendations = []
        if "high" in risk_assessment.lower():
            recommendations.append("Seek guidance from relevant campus office before proceeding")
        if "penalty" in risk_assessment.lower():
            recommendations.append("Understand all penalties and deadlines clearly")
        if "compliance" in risk_assessment.lower():
            recommendations.append("Ensure full compliance with all requirements")
        recommendations.append("Ask questions about any unclear terms")
        
        # Extract simulation options from final state (populated by simulation_agent)
        print(f"\n📊 [ANALYZE API] Extracting simulation options from final state...")
        simulation_options_raw = final_state.get("simulation_options", [])
        print(f"📊 [ANALYZE API] Raw simulation_options count: {len(simulation_options_raw)}")
        print(f"📊 [ANALYZE API] Raw simulation_options: {simulation_options_raw}")
        
        available_simulations = []
        for sim in simulation_options_raw:
            try:
                available_simulations.append(SimulationOption(
                    scenario_type=sim.get("scenario_type", ""),
                    label=sim.get("label", ""),
                    description=sim.get("description", ""),
                    parameters=sim.get("parameters", {}),
                    formula=sim.get("formula", "")
                ))
                print(f"📊 [ANALYZE API] ✓ Added simulation: {sim.get('scenario_type')} - {sim.get('label')}")
            except Exception as e:
                print(f"📊 [ANALYZE API] ✗ Failed to parse simulation: {e}")
                logger.warning(f"Failed to parse simulation option: {e}")
        
        print(f"📊 [ANALYZE API] ✅ Total available_simulations: {len(available_simulations)}")
        
        # Store analysis result
        await db["documents_metadata"].update_one(
            {"_id": session_id},
            {
                "$set": {
                    "domain": domain,
                    "analysis_results": {
                        "risk_assessment": risk_assessment,
                        "risk_level": risk_level,
                        "red_flags": red_flags_raw,
                        "obligations": obligations,
                        "simulation_options": simulation_options_raw
                    }
                }
            }
        )
        
        return AnalyzeResponse(
            session_id=session_id,
            domain=domain,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_reasoning=risk_assessment if risk_assessment else "Analysis complete",
            clauses=clauses,
            obligations=obligations,
            deadlines=[],  # Extracted from obligations if available
            red_flags=red_flags,
            resources=resources,
            summary=risk_assessment if risk_assessment else "Document analyzed.",
            recommendations=recommendations,
            available_simulations=available_simulations
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise
