import logging
from typing import TypedDict, Optional, List, Dict, Any
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from tools.retrieval_tool import GlobalRetrievalTool

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class AgentState(TypedDict):
    """Shared state dictionary for the agent workflow."""
    session_id: str
    raw_text: str
    domain: str
    language: str
    clauses: List[str]
    obligations: List[str]
    financial_details: Optional[str]
    housing_details: Optional[str]
    visa_details: Optional[str]
    risk_assessment: Optional[str]
    red_flags: List[str]
    resources: List[Dict[str, Any]]
    translation: Optional[str]
    scenario: Optional[str]
    error: Optional[str]


async def get_context_for_agent(
    query_text: str,
    domain: str = None,
    top_k: int = 5
) -> str:
    """
    Global retrieval tool accessible to all agents.
    Returns relevant context from vector store and MongoDB.
    """
    try:
        context = await GlobalRetrievalTool(
            query_text=query_text,
            domain_filter=domain,
            top_k=top_k,
            collection_type="clause"
        )
        
        # Format context for agent consumption
        context_str = "\n".join([
            f"- {c.get('clause_text', '')}" for c in context
        ])
        
        return context_str if context_str else "No relevant context found."
    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        return f"[Context retrieval failed: {e}]"


async def call_gemini_with_reasoning(
    prompt: str,
    temperature: float = 0.7
) -> str:
    """
    Call Gemini for open-ended reasoning without JSON rigidity.
    Uses natural language output for better agent reasoning.
    """
    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={
                "temperature": temperature,
                "top_p": 0.9,
            }
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini call error: {e}")
        return f"Error generating response: {e}"


async def router_agent(state: AgentState) -> AgentState:
    """
    Router Agent: Classifies document and extracts initial context.
    Uses reasoning to understand what type of document this is and why.
    """
    try:
        text = state.get("raw_text", "")
        
        prompt = f"""You are the Router Agent for document analysis. Analyze this document excerpt and determine:

1. What TYPE of document is this? (financial aid, lease agreement, visa requirement, etc.)
2. What DOMAIN does it belong to? (finance, housing, visa, or multiple)
3. What is the PRIMARY PURPOSE of this document?
4. What are the 2-3 most CRITICAL concerns a student should be aware of?

Document:
{text[:3000]}

Provide your analysis in clear paragraphs. Be specific about the document type and domain."""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.5)
        
        # Extract domain from reasoning (simplified)
        if "finance" in analysis.lower() or "aid" in analysis.lower():
            state["domain"] = "finance"
        elif "housing" in analysis.lower() or "lease" in analysis.lower():
            state["domain"] = "housing"
        elif "visa" in analysis.lower() or "immigration" in analysis.lower():
            state["domain"] = "visa"
        else:
            state["domain"] = "general"
        
        logger.info(f"Router classified document as: {state['domain']}")
        return state
        
    except Exception as e:
        logger.error(f"Router agent error: {e}")
        state["error"] = str(e)
        return state


async def finance_agent(state: AgentState) -> AgentState:
    """
    Finance Agent: Extracts financial obligations, deadlines, and costs.
    Uses reasoning to identify financial touchpoints and hidden fees.
    """
    try:
        text = state.get("raw_text", "")
        
        # Get relevant financial context from retrieval tool
        context = await get_context_for_agent(
            query_text="tuition fees payment deadlines penalties financial obligations",
            domain="finance",
            top_k=5
        )
        
        prompt = f"""You are the Finance Agent for document analysis. Your goal is to identify every financial touchpoint in this document.

DOCUMENT TO ANALYZE:
{text[:4000]}

RELEVANT CONTEXT FROM SIMILAR DOCUMENTS:
{context}

Analyze the document and:
1. List ALL financial obligations (tuition, fees, payments, deposits, etc.)
2. Identify EVERY deadline associated with payments
3. Find ANY penalties or fees for late/missed payments
4. Highlight HIDDEN COSTS or unusual financial terms
5. Explain the FINANCIAL IMPACT if obligations aren't met

Be thorough and scrutinize every financial detail. Present your findings as clear, actionable insights for a student."""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.7)
        
        state["financial_details"] = analysis
        
        # Extract obligations as a list (simple line-by-line parsing)
        lines = analysis.split('\n')
        obligations = [line.strip() for line in lines if line.strip() and len(line) > 20]
        state["obligations"].extend(obligations[:10])  # Keep top findings
        
        return state
        
    except Exception as e:
        logger.error(f"Finance agent error: {e}")
        state["error"] = str(e)
        return state


async def housing_agent(state: AgentState) -> AgentState:
    """
    Housing Agent: Processes lease terms, dates, and cancellation policies.
    Uses reasoning to identify logistical and legal housing realities.
    """
    try:
        text = state.get("raw_text", "")
        
        # Get relevant housing context
        context = await get_context_for_agent(
            query_text="move-in move-out lease cancellation maintenance responsibilities",
            domain="housing",
            top_k=5
        )
        
        prompt = f"""You are the Housing Agent specializing in residential agreements and leases.

DOCUMENT TO ANALYZE:
{text[:4000]}

RELEVANT HOUSING CONTEXT:
{context}

Your task:
1. Identify ALL move-in and move-out dates
2. Detail maintenance responsibilities and who pays for what
3. ANALYZE the cancellation policy - what is the "point of no return"?
4. Calculate any BUYOUT COSTS if the lease is broken early
5. Identify PENALTIES for damages, early termination, or policy violations
6. Flag any UNUSUAL or UNFAIR terms that disadvantage the tenant

Present your findings as a practical guide for the student."""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.7)
        
        state["housing_details"] = analysis
        state["clauses"].append(analysis)
        
        return state
        
    except Exception as e:
        logger.error(f"Housing agent error: {e}")
        state["error"] = str(e)
        return state


async def visa_agent(state: AgentState) -> AgentState:
    """
    Visa Agent: Extracts visa requirements and compliance obligations.
    Uses reasoning to ensure international students maintain legal standing.
    """
    try:
        text = state.get("raw_text", "")
        
        # Get relevant visa context
        context = await get_context_for_agent(
            query_text="visa I-20 F-1 J-1 immigration compliance status international",
            domain="visa",
            top_k=5
        )
        
        prompt = f"""You are the Visa and Immigration Compliance Agent for international students.

DOCUMENT TO ANALYZE:
{text[:4000]}

RELEVANT COMPLIANCE CONTEXT:
{context}

Your task:
1. Extract ALL visa-related requirements (I-20, employment, health insurance, etc.)
2. Identify COMPLIANCE OBLIGATIONS for F-1/J-1 status maintenance
3. List STATUS CHANGE NOTIFICATIONS or conditions that could jeopardize visa
4. Flag any CRITICAL DEADLINES for visa renewals or form submissions
5. Identify LEGAL RISKS if obligations aren't met
6. Highlight any unusual provisions that could affect immigration status

Be comprehensive - missing a compliance obligation could result in visa revocation."""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.5)
        
        state["visa_details"] = analysis
        state["obligations"].append(analysis)
        
        return state
        
    except Exception as e:
        logger.error(f"Visa agent error: {e}")
        state["error"] = str(e)
        return state


async def rag_agent(state: AgentState) -> AgentState:
    """
    RAG Agent: Bridges documents to campus resources.
    Uses reasoning to match student situations with actual support services.
    """
    try:
        financial_context = state.get("financial_details", "")
        housing_context = state.get("housing_details", "")
        visa_context = state.get("visa_details", "")
        
        # Determine what resources to search for based on agent findings
        search_queries = []
        if financial_context and "penalty" in financial_context.lower():
            search_queries.append("financial aid emergency loans bursar")
        if financial_context and "tuition" in financial_context.lower():
            search_queries.append("tuition payment plans financial assistance")
        if housing_context:
            search_queries.append("housing off-campus residential life")
        if visa_context:
            search_queries.append("international students visa immigration")
        
        resources = []
        for query in search_queries:
            context = await get_context_for_agent(
                query_text=query,
                top_k=3
            )
            if context and "No relevant context" not in context:
                resources.append({
                    "query": query,
                    "context": context
                })
        
        state["resources"] = resources
        return state
        
    except Exception as e:
        logger.error(f"RAG agent error: {e}")
        state["error"] = str(e)
        return state


async def risk_agent(state: AgentState) -> AgentState:
    """
    Risk Agent: Performs holistic risk assessment through reasoning.
    Identifies red flags and explains risks in human terms, not math.
    """
    try:
        text = state.get("raw_text", "")
        financial = state.get("financial_details", "")
        housing = state.get("housing_details", "")
        visa = state.get("visa_details", "")
        
        prompt = f"""You are the Risk Agent - the final auditor of this document analysis. Your job is to identify RISKS and RED FLAGS.

ORIGINAL DOCUMENT:
{text[:3000]}

FINANCIAL ANALYSIS:
{financial}

HOUSING ANALYSIS:
{housing}

VISA ANALYSIS:
{visa}

Now analyze and:
1. IDENTIFY CONFLICTS between different sections or clauses
2. FLAG HIGH-LIABILITY TERMS that could harm the student
3. Highlight PREDATORY PRACTICES (e.g., excessive penalties, waived rights)
4. Look for AMBIGUOUS LANGUAGE that could be interpreted against the student
5. Assess OVERALL RISK LEVEL based on reasoning, not math

Assign an overall risk level: LOW, MEDIUM, or HIGH

Provide specific reasoning for each red flag. Be direct about what could go wrong."""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.7)
        
        state["risk_assessment"] = analysis
        
        # Extract red flags (simple pattern matching on reasoning)
        if "high" in analysis.lower():
            state["red_flags"].append("Document contains high-risk terms")
        if "predatory" in analysis.lower():
            state["red_flags"].append("Potentially predatory practices identified")
        if "ambiguous" in analysis.lower():
            state["red_flags"].append("Ambiguous language that could harm student")
        
        return state
        
    except Exception as e:
        logger.error(f"Risk agent error: {e}")
        state["error"] = str(e)
        return state
