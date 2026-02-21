import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from agents.base_agents import AgentState, call_gemini_structured
import json

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


async def translation_agent(state: AgentState) -> AgentState:
    """Translate plain-language summary to target language."""
    try:
        summary = state.get("risk_output", {}).get("summary", "")
        language = state.get("language", "en")
        
        if language == "en":
            state["translation"] = summary
            return state
        
        prompt = f"""Translate this student-friendly explanation to {language}. Return ONLY the translated text, no JSON needed.

Original text:
{summary}"""
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        state["translation"] = response.text.strip()
        return state
    except Exception as e:
        logger.error(f"Translation agent error: {e}")
        state["error"] = str(e)
        return state


async def scenario_agent(state: AgentState) -> AgentState:
    """Simulate deterministic financial/contractual scenarios."""
    try:
        domain = state.get("domain", "")
        scenario_params = state.get("scenario", {})
        
        if not scenario_params:
            return state
        
        scenario_type = scenario_params.get("scenario", "")
        params = scenario_params.get("parameters", {})
        
        # Deterministic formula for scenario exposure
        exposure = 0.0
        formula = ""
        explanation = ""
        
        if scenario_type == "early_termination":
            base_penalty = params.get("base_penalty", 0)
            months_remaining = params.get("months_remaining", 0)
            penalty_rate = params.get("penalty_rate_per_month", 0)
            
            exposure = base_penalty + (months_remaining * penalty_rate)
            formula = "base_penalty + (months_remaining × penalty_rate)"
            explanation = f"Terminating the lease {months_remaining} months early would cost approximately ${exposure:.2f} based on the contract terms."
        
        state["scenario"] = {
            "scenario": scenario_type,
            "exposure_estimate": exposure,
            "formula_used": formula,
            "explanation": explanation,
            "caveats": ["This is an estimate only. Consult Student Legal Services for formal advice."]
        }
        
        return state
    except Exception as e:
        logger.error(f"Scenario agent error: {e}")
        state["error"] = str(e)
        return state
