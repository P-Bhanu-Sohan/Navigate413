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
    rag_context: List[Dict[str, Any]]  # Retrieved clauses from campus_embeddings collection
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
        print(f"🔀 [ROUTER] Analyzing document ({len(text)} chars)")
        
        prompt = f"""You are the Router Agent for document analysis. Analyze this document and classify it.

Document excerpt:
{text[:3000]}

CRITICAL: You MUST end your response with EXACTLY one of these lines:
DOMAIN: finance
DOMAIN: housing
DOMAIN: visa
DOMAIN: unknown

Classify based on:
- "finance" if about: financial aid, tuition, scholarships, loans, payment plans, bursar, fees
- "housing" if about: lease, rent, apartment, dorm, residential, sublease, move-in/out
- "visa" if about: F-1, J-1, I-20, immigration, work authorization, visa status
- "unknown" if none of the above

Provide brief analysis, then end with the DOMAIN line."""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.3)
        print(f"🔀 [ROUTER] Gemini analysis: {analysis[:200]}...")
        
        # Extract domain from explicit DOMAIN: line
        domain = "unknown"
        for line in analysis.split('\n'):
            if line.strip().startswith("DOMAIN:"):
                domain = line.split("DOMAIN:")[1].strip().lower()
                break
        
        # Fallback: keyword matching if DOMAIN line not found
        if domain == "unknown":
            analysis_lower = analysis.lower()
            if any(word in analysis_lower for word in ["financial aid", "tuition", "scholarship", "loan", "bursar", "payment"]):
                domain = "finance"
            elif any(word in analysis_lower for word in ["lease", "rent", "housing", "apartment", "residential"]):
                domain = "housing"
            elif any(word in analysis_lower for word in ["visa", "f-1", "j-1", "i-20", "immigration"]):
                domain = "visa"
        
        state["domain"] = domain
        print(f"🔀 [ROUTER] ✓ Classified as: {domain}")
        logger.info(f"Router classified document as: {domain}")
        return state
        
    except Exception as e:
        logger.error(f"Router agent error: {e}")
        print(f"🔀 [ROUTER] ✗ Error: {e}")
        state["error"] = str(e)
        state["domain"] = "unknown"
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

Analyze the document and extract KEY OBLIGATIONS as concise bullet points.

OUTPUT FORMAT - Return ONLY a bulleted list of obligations:
• [Action item with specific amount/deadline]
• [Action item with specific amount/deadline]

EXAMPLE:
• Pay $2,000 security deposit by March 1, 2026
• Maintain 12+ credit hours per semester
• File FAFSA renewal by April 15, 2026

RULES:
1. Each bullet point must be a SINGLE, ACTIONABLE item
2. Include specific amounts, dates, and requirements
3. Keep each bullet under 15 words
4. Extract 5-8 most critical obligations only
5. Do NOT copy full sentences from the document
6. Do NOT add explanations or context - just the action items

OBLIGATIONS:"""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.3)
        
        state["financial_details"] = analysis
        
        # Extract clean bullet points (remove bullet symbols, clean whitespace)
        lines = analysis.split('\n')
        obligations = []
        for line in lines:
            line = line.strip()
            # Remove bullet symbols and clean up
            line = line.lstrip('•●-*').strip()
            # Only keep lines that are actual obligations (not empty, not too short)
            if line and len(line) > 10 and not line.endswith(':'):
                obligations.append(line)
        
        state["obligations"].extend(obligations[:8])  # Keep top 8 obligations
        
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
        
        prompt = f"""You are the Visa Agent specializing in F-1/J-1 student visa compliance.

DOCUMENT TO ANALYZE:
{text[:4000]}

RELEVANT VISA CONTEXT:
{context}

Extract KEY VISA OBLIGATIONS as concise bullet points.

OUTPUT FORMAT - Return ONLY a bulleted list:
• [Specific visa compliance action]
• [Specific visa compliance action]

EXAMPLE:
• Maintain full-time enrollment (12+ credits)
• Report address changes to ISSS within 10 days
• Renew I-20 before expiration date

RULES:
1. Each bullet = ONE actionable compliance item
2. Include specific requirements and deadlines
3. Keep each bullet under 15 words
4. Extract 3-6 most critical obligations only
5. Do NOT copy full document text

VISA OBLIGATIONS:"""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.3)
        
        state["visa_details"] = analysis
        
        # Extract clean bullet points
        lines = analysis.split('\n')
        obligations = []
        for line in lines:
            line = line.strip().lstrip('•●-*').strip()
            if line and len(line) > 10 and not line.endswith(':'):
                obligations.append(line)
        
        state["obligations"].extend(obligations[:6])
        
        return state
        
    except Exception as e:
        logger.error(f"Visa agent error: {e}")
        state["error"] = str(e)
        return state


async def rag_agent(state: AgentState) -> AgentState:
    """
    RAG Agent: Retrieval-Augmented Generation for document context enrichment.
    Searches the campus_embeddings collection ONLY to find similar document clauses.
    Does NOT handle campus resources (that's handled separately by another dev).
    """
    logger.info("[RAG_AGENT] Starting RAG agent execution")
    
    try:
        # Get context from upstream agents
        raw_text = state.get("raw_text", "")
        domain = state.get("domain", "general")
        financial_context = state.get("financial_details", "")
        housing_context = state.get("housing_details", "")
        visa_context = state.get("visa_details", "")
        
        logger.info(f"[RAG_AGENT] Domain: {domain}")
        logger.info(f"[RAG_AGENT] Has financial context: {bool(financial_context)}")
        logger.info(f"[RAG_AGENT] Has housing context: {bool(housing_context)}")
        logger.info(f"[RAG_AGENT] Has visa context: {bool(visa_context)}")
        
        # Build semantic queries based on document content and domain
        search_queries = []
        
        # Always search with a snippet from the raw document for similarity
        if raw_text:
            # Take first 200 chars as a semantic anchor
            doc_snippet = raw_text[:200].strip()
            search_queries.append(doc_snippet)
            logger.info(f"[RAG_AGENT] Added document snippet query: {doc_snippet[:50]}...")
        
        # Add domain-specific semantic queries based on agent findings
        if domain == "finance" or financial_context:
            search_queries.append("tuition payment deadline penalty financial obligation fee")
            logger.info("[RAG_AGENT] Added finance-related query")
        
        if domain == "housing" or housing_context:
            search_queries.append("lease termination move-out penalty deposit liability")
            logger.info("[RAG_AGENT] Added housing-related query")
        
        if domain == "visa" or visa_context:
            search_queries.append("visa compliance I-20 enrollment status immigration")
            logger.info("[RAG_AGENT] Added visa-related query")
        
        logger.info(f"[RAG_AGENT] Total search queries: {len(search_queries)}")
        
        # Search campus_embeddings collection for similar clauses
        retrieved_clauses = []
        
        for i, query in enumerate(search_queries):
            logger.info(f"[RAG_AGENT] Executing query {i+1}/{len(search_queries)}")
            
            # Use GlobalRetrievalTool with collection_type="clause" (campus_embeddings only)
            results = await GlobalRetrievalTool(
                query_text=query,
                domain_filter=None,  # No domain filter for clauses
                top_k=3,
                collection_type="clause"  # campus_embeddings collection ONLY
            )
            
            logger.info(f"[RAG_AGENT] Query {i+1} returned {len(results)} results")
            
            for result in results:
                clause_text = result.get("clause_text", "")
                score = result.get("score", 0)
                
                if clause_text and clause_text not in [c.get("text") for c in retrieved_clauses]:
                    retrieved_clauses.append({
                        "text": clause_text,
                        "score": score,
                        "query": query[:50]
                    })
                    logger.info(f"[RAG_AGENT] Found clause (score={score:.3f}): {clause_text[:60]}...")
        
        # Deduplicate and sort by relevance score
        retrieved_clauses = sorted(
            retrieved_clauses, 
            key=lambda x: x.get("score", 0), 
            reverse=True
        )[:10]  # Keep top 10 most relevant
        
        logger.info(f"[RAG_AGENT] Total unique clauses retrieved: {len(retrieved_clauses)}")
        
        # Store retrieved context in state for downstream use
        state["rag_context"] = retrieved_clauses
        
        # Format context for potential use in prompts
        if retrieved_clauses:
            context_summary = "\n".join([
                f"- {c['text'][:150]}... (relevance: {c['score']:.2f})" 
                for c in retrieved_clauses[:5]
            ])
            logger.info(f"[RAG_AGENT] Context summary:\n{context_summary}")
        else:
            logger.info("[RAG_AGENT] No similar clauses found in campus_embeddings collection")
        
        logger.info("[RAG_AGENT] ✓ RAG agent completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"[RAG_AGENT] FAILED: {e}", exc_info=True)
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
