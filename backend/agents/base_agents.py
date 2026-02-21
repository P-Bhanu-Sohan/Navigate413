import logging
from typing import TypedDict, Optional, List, Dict, Any
import json
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from tools.retrieval_tool import GlobalRetrievalTool
from models.risk_models import RiskModel

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class AgentState(TypedDict):
    """Shared state dictionary for the LangGraph."""
    session_id: str
    raw_text: str
    domain: str
    language: str
    clauses: List[Dict[str, Any]]
    risk_output: Dict[str, Any]
    resources: List[Dict[str, Any]]
    translation: Optional[str]
    scenario: Optional[Dict[str, Any]]
    error: Optional[str]


async def call_gemini_structured(
    prompt: str,
    schema_name: str = "output"
) -> Optional[Dict[str, Any]]:
    """Call Gemini with structured JSON output enforcement."""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from Gemini: {response_text}")
            # Retry with explicit instruction
            retry_prompt = prompt + "\n\nYOU MUST RESPOND WITH ONLY VALID JSON, NO OTHER TEXT."
            response = model.generate_content(retry_prompt)
            response_text = response.text.strip()
            return json.loads(response_text)
    except Exception as e:
        logger.error(f"Gemini call error: {e}")
        return None


async def finance_agent(state: AgentState) -> AgentState:
    """Analyze financial documents for risk."""
    try:
        text = state.get("raw_text", "")
        session_id = state.get("session_id", "")
        
        # Retrieve relevant clauses
        context = await GlobalRetrievalTool(
            query_text="financial obligations, penalties, deadlines, aid cancellation",
            domain_filter="finance",
            top_k=5,
            collection_type="clause"
        )
        
        context_str = "\n".join([c.get("clause_text", "") for c in context])
        
        prompt = f"""You are a financial risk analysis agent specializing in university financial aid documents.
        
Retrieved context:
{context_str}

Document excerpt:
{text[:2000]}

Analyze and return ONLY a JSON object with this exact structure:
{{
    "risk_indicators": {{
        "financial_exposure_amount": <number>,
        "financial_exposure_indicator": <0-1>,
        "penalty_escalation_indicator": <0-1>,
        "deadline_sensitivity_indicator": <0-1>
    }},
    "obligations": ["obligation1", "obligation2"],
    "deadlines": ["deadline1", "deadline2"],
    "clauses": [
        {{
            "text": "clause text",
            "flag": "FLAG_NAME",
            "risk_contribution": <0-1>,
            "explanation": "plain language explanation"
        }}
    ],
    "plain_explanation": "one sentence summary"
}}

Return ONLY the JSON object, no other text."""
        
        result = await call_gemini_structured(prompt, "finance_output")
        
        if result:
            # Calculate risk score
            indicators = result.get("risk_indicators", {})
            risk_score = RiskModel.finance_risk_score(
                indicators.get("financial_exposure_indicator", 0),
                indicators.get("penalty_escalation_indicator", 0),
                indicators.get("deadline_sensitivity_indicator", 0)
            )
            
            state["domain"] = "finance"
            state["risk_output"] = {
                "risk_score": risk_score,
                "risk_level": RiskModel.risk_level_from_score(risk_score),
                "indicators": indicators,
                "obligations": result.get("obligations", []),
                "deadlines": result.get("deadlines", []),
                "summary": result.get("plain_explanation", "")
            }
            state["clauses"] = result.get("clauses", [])
        
        return state
    except Exception as e:
        logger.error(f"Finance agent error: {e}")
        state["error"] = str(e)
        return state


async def housing_agent(state: AgentState) -> AgentState:
    """Analyze housing documents for risk."""
    try:
        text = state.get("raw_text", "")
        
        # Retrieve relevant clauses
        context = await GlobalRetrievalTool(
            query_text="lease termination, penalties, liability, payment obligations",
            domain_filter="housing",
            top_k=5,
            collection_type="clause"
        )
        
        context_str = "\n".join([c.get("clause_text", "") for c in context])
        
        prompt = f"""You are a housing contract analysis agent for university leases.

Retrieved context:
{context_str}

Document excerpt:
{text[:2000]}

Analyze and return ONLY a JSON object with this exact structure:
{{
    "risk_indicators": {{
        "termination_penalty_indicator": <0-1>,
        "liability_clause_indicator": <0-1>,
        "payment_obligation_indicator": <0-1>
    }},
    "obligations": ["obligation1"],
    "clauses": [
        {{
            "text": "clause text",
            "flag": "FLAG_NAME",
            "risk_contribution": <0-1>,
            "explanation": "plain language explanation"
        }}
    ],
    "extracted_parameters": {{
        "base_penalty": <number or null>,
        "penalty_rate_per_month": <number or null>
    }},
    "plain_explanation": "one sentence summary"
}}

Return ONLY the JSON object, no other text."""
        
        result = await call_gemini_structured(prompt, "housing_output")
        
        if result:
            # Calculate risk score
            indicators = result.get("risk_indicators", {})
            risk_score = RiskModel.housing_risk_score(
                indicators.get("termination_penalty_indicator", 0),
                indicators.get("liability_clause_indicator", 0),
                indicators.get("payment_obligation_indicator", 0)
            )
            
            state["domain"] = "housing"
            state["risk_output"] = {
                "risk_score": risk_score,
                "risk_level": RiskModel.risk_level_from_score(risk_score),
                "indicators": indicators,
                "obligations": result.get("obligations", []),
                "summary": result.get("plain_explanation", ""),
                "scenario_parameters": result.get("extracted_parameters", {})
            }
            state["clauses"] = result.get("clauses", [])
        
        return state
    except Exception as e:
        logger.error(f"Housing agent error: {e}")
        state["error"] = str(e)
        return state


async def visa_agent(state: AgentState) -> AgentState:
    """Analyze visa/compliance documents."""
    try:
        text = state.get("raw_text", "")
        
        # Retrieve relevant clauses
        context = await GlobalRetrievalTool(
            query_text="work authorization, enrollment requirements, visa status, compliance",
            domain_filter="visa",
            top_k=5,
            collection_type="clause"
        )
        
        context_str = "\n".join([c.get("clause_text", "") for c in context])
        
        prompt = f"""You are a visa and international student compliance agent.

Retrieved context:
{context_str}

Document excerpt:
{text[:2000]}

Analyze and return ONLY a JSON object with this exact structure:
{{
    "risk_level": "COMPLIANT|AT_RISK|VIOLATION_LIKELY",
    "risk_factors": ["factor1", "factor2"],
    "clauses": [
        {{
            "text": "clause text",
            "flag": "FLAG_NAME",
            "explanation": "plain language explanation"
        }}
    ],
    "obligations": ["obligation1"],
    "plain_explanation": "one sentence summary"
}}

Return ONLY the JSON object, no other text."""
        
        result = await call_gemini_structured(prompt, "visa_output")
        
        if result:
            risk_level = result.get("risk_level", "AT_RISK")
            risk_score = 0.2 if risk_level == "COMPLIANT" else (0.5 if risk_level == "AT_RISK" else 0.9)
            
            state["domain"] = "visa"
            state["risk_output"] = {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_factors": result.get("risk_factors", []),
                "obligations": result.get("obligations", []),
                "summary": result.get("plain_explanation", "")
            }
            state["clauses"] = result.get("clauses", [])
        
        return state
    except Exception as e:
        logger.error(f"Visa agent error: {e}")
        state["error"] = str(e)
        return state


async def rag_agent(state: AgentState) -> AgentState:
    """Retrieve and provide relevant campus resources."""
    try:
        domain = state.get("domain", "unknown")
        summary = state.get("risk_output", {}).get("summary", "")
        
        # Search for relevant resources
        resources = await GlobalRetrievalTool(
            query_text=summary,
            domain_filter=domain if domain != "unknown" else None,
            top_k=3,
            collection_type="resource"
        )
        
        state["resources"] = resources
        return state
    except Exception as e:
        logger.error(f"RAG agent error: {e}")
        state["error"] = str(e)
        return state
