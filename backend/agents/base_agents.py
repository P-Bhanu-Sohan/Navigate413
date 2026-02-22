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
    simulation_options: List[Dict[str, Any]]  # Dynamic simulations extracted from document
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


async def simulation_agent(state: AgentState) -> AgentState:
    """
    Simulation Agent: Extracts simulation parameters from document using Gemini.
    Identifies what-if scenarios relevant to the document and extracts numeric values.
    """
    try:
        print(f"\n{'='*60}")
        print(f"🎲 [SIMULATION_AGENT] Starting simulation extraction...")
        print(f"{'='*60}")
        
        text = state.get("raw_text", "")
        domain = state.get("domain", "unknown")
        financial = state.get("financial_details", "")
        housing = state.get("housing_details", "")
        visa = state.get("visa_details", "")
        
        print(f"🎲 [SIMULATION_AGENT] Domain: {domain}")
        print(f"🎲 [SIMULATION_AGENT] Raw text length: {len(text)} chars")
        print(f"🎲 [SIMULATION_AGENT] Has financial details: {bool(financial)}")
        print(f"🎲 [SIMULATION_AGENT] Has housing details: {bool(housing)}")
        print(f"🎲 [SIMULATION_AGENT] Has visa details: {bool(visa)}")
        
        logger.info(f"[SIMULATION_AGENT] Extracting simulations for domain: {domain}")
        
        # Build domain-specific prompt
        if domain == "housing":
            prompt = f"""Analyze this housing/lease document and extract simulation parameters.

DOCUMENT:
{text[:3000]}

HOUSING ANALYSIS:
{housing[:1000] if housing else "N/A"}

Extract ONLY if found in document. Output JSON format:
{{
  "simulations": [
    {{
      "scenario_type": "early_termination",
      "label": "Early Lease Termination",
      "description": "Calculate cost of breaking lease early",
      "parameters": {{
        "base_penalty": <number or 0>,
        "monthly_penalty": <number or 0>,
        "months_remaining": <number or 6>
      }},
      "formula": "base_penalty + (months_remaining × monthly_penalty)"
    }},
    {{
      "scenario_type": "late_rent",
      "label": "Late Rent Payment",
      "description": "Calculate late rent fees",
      "parameters": {{
        "monthly_rent": <number or 0>,
        "late_fee_percent": <number or 5>,
        "daily_fee": <number or 0>,
        "days_late": 1
      }},
      "formula": "monthly_rent × (late_fee_percent/100) + (daily_fee × days_late)"
    }},
    {{
      "scenario_type": "security_deposit",
      "label": "Security Deposit Return",
      "description": "Estimate deposit return after deductions",
      "parameters": {{
        "deposit_amount": <number or 0>,
        "cleaning_fee": 0,
        "damage_cost": 0,
        "unpaid_balance": 0
      }},
      "formula": "deposit_amount - cleaning_fee - damage_cost - unpaid_balance"
    }}
  ]
}}

RULES:
1. Extract actual numbers from document (rent, fees, deposits)
2. Use 0 for values not found
3. Only include simulations relevant to this document
4. Output ONLY valid JSON, no other text"""

        elif domain == "finance":
            prompt = f"""You are analyzing a financial aid document for a university student. Extract ALL relevant simulation scenarios.

DOCUMENT:
{text[:4000]}

FINANCIAL ANALYSIS:
{financial[:1500] if financial else "N/A"}

Your task: Identify EVERY possible "what-if" scenario a student might want to simulate based on this document.

Think about:
- What happens if they drop courses/credits?
- What happens if they withdraw mid-semester?
- What if they miss deadlines (FAFSA, verification, etc.)?
- What if their enrollment status changes (full-time to part-time)?
- What if they lose eligibility for certain aid types?
- What about loan repayment scenarios?
- What if they take a leave of absence?
- SAP (Satisfactory Academic Progress) violations?

Output JSON with 3-6 relevant simulations:
{{
  "simulations": [
    {{
      "scenario_type": "credit_reduction",
      "label": "Credit Hour Reduction Impact",
      "description": "Estimate aid reduction when dropping below full-time",
      "parameters": {{
        "current_aid": <extract from doc or use 15000>,
        "current_credits": 15,
        "new_credits": 9,
        "full_time_threshold": 12
      }},
      "formula": "Prorated aid based on enrollment intensity"
    }},
    {{
      "scenario_type": "withdrawal_refund",
      "label": "Mid-Semester Withdrawal",
      "description": "Calculate tuition refund and aid return if withdrawing",
      "parameters": {{
        "tuition_charged": <from doc or 16000>,
        "aid_disbursed": <from doc or 12000>,
        "weeks_completed": 4,
        "total_weeks": 15
      }},
      "formula": "Federal Return of Title IV calculation"
    }},
    {{
      "scenario_type": "fafsa_deadline_miss",
      "label": "FAFSA Late Filing Impact",
      "description": "Estimate priority aid loss from late FAFSA",
      "parameters": {{
        "total_aid": <from doc>,
        "days_late": 30,
        "state_aid_at_risk": <from doc or 2000>,
        "institutional_aid_at_risk": <from doc or 3000>
      }},
      "formula": "Priority deadline aid loss estimation"
    }},
    {{
      "scenario_type": "part_time_switch",
      "label": "Full-Time to Part-Time Impact",
      "description": "Aid changes when switching to part-time enrollment",
      "parameters": {{
        "current_grants": <from doc>,
        "current_loans": <from doc>,
        "new_enrollment_status": 0.5
      }},
      "formula": "Adjusted aid based on enrollment status"
    }},
    {{
      "scenario_type": "gpa_drop_impact",
      "label": "GPA Drop / SAP Violation Risk",
      "description": "Aid loss risk if GPA falls below requirements",
      "parameters": {{
        "current_gpa": 2.5,
        "required_gpa": 2.0,
        "total_aid_at_risk": <from doc>
      }},
      "formula": "SAP violation consequences assessment"
    }},
    {{
      "scenario_type": "loan_repayment_estimate",
      "label": "Monthly Loan Repayment",
      "description": "Estimate monthly payments after graduation",
      "parameters": {{
        "total_loan_amount": <from doc or 10000>,
        "interest_rate": 5.5,
        "repayment_years": 10
      }},
      "formula": "Standard 10-year repayment calculation"
    }}
  ]
}}

IMPORTANT RULES:
1. Extract ACTUAL dollar amounts from the document - look for tuition, fees, grants, loans, scholarships
2. Include AT LEAST 3 simulations, ideally 4-6 based on document content
3. Make parameters realistic based on what you see in the document
4. Every simulation MUST have scenario_type, label, description, parameters, formula
5. Output ONLY valid JSON, no markdown, no explanation"""

        elif domain == "visa":
            prompt = f"""Analyze this visa/immigration document and extract simulation parameters.

DOCUMENT:
{text[:3000]}

VISA ANALYSIS:
{visa[:1000] if visa else "N/A"}

Extract ONLY if relevant. Output JSON format:
{{
  "simulations": [
    {{
      "scenario_type": "work_hours_violation",
      "label": "Work Hour Violation Risk",
      "description": "Calculate risk of working over allowed hours",
      "parameters": {{
        "hours_worked": 20,
        "max_allowed_hours": 20
      }},
      "formula": "Risk score based on excess hours"
    }},
    {{
      "scenario_type": "course_load_drop",
      "label": "Course Load Drop Impact",
      "description": "Calculate SEVIS violation risk",
      "parameters": {{
        "current_credits": 12,
        "minimum_credits": 12,
        "has_rpe_approval": false
      }},
      "formula": "Risk score based on credit deficit"
    }}
  ]
}}

RULES:
1. Extract requirements from document
2. Use standard F-1 defaults (20 hrs work, 12 credits)
3. Only include simulations relevant to this document
4. Output ONLY valid JSON, no other text"""
        else:
            # Unknown domain - no simulations
            print(f"🎲 [SIMULATION_AGENT] ⚠️ Unknown domain '{domain}' - no simulations available")
            state["simulation_options"] = []
            return state
        
        print(f"🎲 [SIMULATION_AGENT] Calling Gemini to extract simulation parameters...")
        response = await call_gemini_with_reasoning(prompt, temperature=0.2)
        print(f"🎲 [SIMULATION_AGENT] Gemini response length: {len(response)} chars")
        print(f"🎲 [SIMULATION_AGENT] Gemini response preview: {response[:200]}...")
        
        # Parse JSON response
        import json
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()
            
            print(f"🎲 [SIMULATION_AGENT] Parsing JSON response...")
            data = json.loads(clean_response)
            simulations = data.get("simulations", [])
            
            print(f"🎲 [SIMULATION_AGENT] Found {len(simulations)} simulations in response")
            
            # Validate and clean simulations
            valid_simulations = []
            for sim in simulations:
                if all(k in sim for k in ["scenario_type", "label", "parameters", "formula"]):
                    valid_simulations.append(sim)
                    print(f"🎲 [SIMULATION_AGENT] ✓ Valid: {sim.get('scenario_type')} - {sim.get('label')}")
                else:
                    print(f"🎲 [SIMULATION_AGENT] ✗ Invalid simulation (missing keys): {sim}")
            
            state["simulation_options"] = valid_simulations
            print(f"🎲 [SIMULATION_AGENT] ✅ Total valid simulations: {len(valid_simulations)}")
            logger.info(f"[SIMULATION_AGENT] Extracted {len(valid_simulations)} simulations")
            
        except json.JSONDecodeError as e:
            print(f"🎲 [SIMULATION_AGENT] ❌ JSON parse error: {e}")
            print(f"🎲 [SIMULATION_AGENT] Raw response was: {response[:500]}")
            logger.error(f"[SIMULATION_AGENT] Failed to parse JSON: {e}")
            state["simulation_options"] = []
        
        return state
        
    except Exception as e:
        print(f"🎲 [SIMULATION_AGENT] ❌ ERROR: {e}")
        logger.error(f"Simulation agent error: {e}")
        state["simulation_options"] = []
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
        
        prompt = f"""You are the Risk Agent. Analyze this document and output ONLY a risk level and red flags.

DOCUMENT EXCERPT:
{text[:3000]}

FINANCIAL ANALYSIS:
{financial[:500] if financial else "N/A"}

HOUSING ANALYSIS:
{housing[:500] if housing else "N/A"}

VISA ANALYSIS:
{visa[:500] if visa else "N/A"}

OUTPUT FORMAT (be extremely concise):
RISK_LEVEL: [LOW/MEDIUM/HIGH]
RED_FLAGS: [comma-separated list of 3-5 specific red flags, or NONE]

Example:
RISK_LEVEL: HIGH
RED_FLAGS: $2000 security deposit handling unclear, Late fee policy exceeds MA law, No clear termination clause"""

        analysis = await call_gemini_with_reasoning(prompt, temperature=0.5)
        
        # Extract risk level
        risk_level = "MEDIUM"
        if "RISK_LEVEL:" in analysis:
            level_line = [line for line in analysis.split('\n') if "RISK_LEVEL:" in line][0]
            if "HIGH" in level_line.upper():
                risk_level = "HIGH"
            elif "LOW" in level_line.upper():
                risk_level = "LOW"
        
        state["risk_assessment"] = ""  # No paragraph - just use visual risk score/level above
        
        # Extract red flags from analysis
        if "RED_FLAGS:" in analysis:
            flags_line = [line for line in analysis.split('\n') if "RED_FLAGS:" in line]
            if flags_line:
                flags_text = flags_line[0].replace("RED_FLAGS:", "").strip()
                if flags_text and flags_text.upper() != "NONE":
                    flags = [f.strip() for f in flags_text.split(',')]
                    state["red_flags"].extend(flags[:5])
        
        return state
        
    except Exception as e:
        logger.error(f"Risk agent error: {e}")
        state["error"] = str(e)
        return state
