import logging
import asyncio
from agents.base_agents import AgentState, call_gemini_with_reasoning, get_context_for_agent

logger = logging.getLogger(__name__)


async def translation_agent(state: AgentState) -> AgentState:
    """
    Translation Agent: Translates complex clauses to plain language.
    Uses reasoning to explain legal/financial jargon in simple terms.
    """
    try:
        clauses = state.get("clauses", [])
        language = state.get("language", "en")
        
        if language == "en" or not clauses:
            return state
        
        clauses_text = "\n".join(clauses[:5])  # Top 5 clauses
        
        prompt = f"""You are a translation agent. Translate these legal/financial clauses into plain, simple language that a student can understand.

ORIGINAL CLAUSES:
{clauses_text}

TARGET LANGUAGE: {language}

Provide clear, simple explanations. Avoid jargon. Make sure the student understands what they're actually agreeing to."""

        translation = await call_gemini_with_reasoning(prompt, temperature=0.6)
        state["translation"] = translation
        
        return state
        
    except Exception as e:
        logger.error(f"Translation agent error: {e}")
        return state


async def scenario_agent(state: AgentState) -> AgentState:
    """
    Scenario Agent: Simulates real-world scenarios to help students understand implications.
    Uses reasoning to walk through "what if" situations.
    """
    try:
        financial = state.get("financial_details", "")
        housing = state.get("housing_details", "")
        obligations = state.get("obligations", [])
        
        if not financial and not housing and not obligations:
            return state
        
        context = f"""
FINANCIAL DETAILS: {financial}
HOUSING DETAILS: {housing}
KEY OBLIGATIONS: {', '.join(obligations[:3])}
"""
        
        prompt = f"""You are a scenario analyst. Create 2-3 realistic "what if" scenarios based on these document details.

{context}

For each scenario:
1. Describe the situation (e.g., "Student loses on-campus job in month 3")
2. Explain what happens based on the document terms
3. Show the financial/legal implications
4. Suggest what the student should do

Make scenarios concrete and actionable."""

        scenarios = await call_gemini_with_reasoning(prompt, temperature=0.8)
        state["scenario"] = scenarios
        
        return state
        
    except Exception as e:
        logger.error(f"Scenario agent error: {e}")
        return state
