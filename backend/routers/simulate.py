import logging
import json
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from models.schemas import SimulateRequest, SimulateResponse
from db.mongo import get_db
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["simulate"])

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


async def get_gemini_simulation(scenario_type: str, parameters: dict) -> dict:
    """
    Use Gemini to reason about ALL simulations with proper domain knowledge.
    Returns: {"result": float, "reasoning": str, "severity": str, "is_risk": bool}
    """
    print(f"🤖 [GEMINI SIM] Getting Gemini simulation for {scenario_type}")
    print(f"🤖 [GEMINI SIM] Parameters: {parameters}")
    
    # Build domain-specific prompts
    if scenario_type == "work_hours_violation":
        hours_worked = parameters.get("hours_worked", 0)
        max_allowed = parameters.get("max_allowed_hours", 20)
        
        prompt = f"""You are an F-1 immigration compliance expert at a US university.

STUDENT SITUATION:
- Working {hours_worked} hours per week
- Maximum allowed: {max_allowed} hours/week during semester

F-1 WORK RULES:
- Max 20 hrs/week during school, unlimited during breaks
- ANY violation can trigger SEVIS termination
- Consequences: deportation, 3-10 year US bar, loss of degree progress

Respond with ONLY valid JSON:
{{"result": <risk 0-100>, "severity": "<NONE|LOW|MODERATE|HIGH|CRITICAL>", "reasoning": "<2 sentences on consequences>", "is_risk": true}}

Guidelines:
- At or under limit: 0, NONE
- 1-2 hrs over: 80+, HIGH (already violating)
- 3+ hrs over: 90+, CRITICAL"""

    elif scenario_type == "course_load_drop":
        current = parameters.get("current_credits", 12)
        minimum = parameters.get("minimum_credits", 12)
        has_approval = parameters.get("has_rpe_approval", False)
        
        prompt = f"""You are an F-1 immigration compliance expert.

STUDENT SITUATION:
- Enrolled in {current} credits
- Minimum required: {minimum} credits for full-time status
- Has RCL/RPE approval from DSO: {"Yes" if has_approval else "No"}

F-1 ENROLLMENT RULES:
- Must maintain full-time (12 undergrad, 9 grad)
- Below minimum WITHOUT approval = status violation
- With DSO approval, reduced load is legal

Respond with ONLY valid JSON:
{{"result": <risk 0-100>, "severity": "<NONE|LOW|MODERATE|HIGH|CRITICAL>", "reasoning": "<2 sentences>", "is_risk": true}}

Guidelines:
- Meeting minimum: 0, NONE
- Below WITH approval: 15-25, LOW
- Below WITHOUT approval: 90+, CRITICAL"""

    elif scenario_type == "early_termination":
        base_penalty = parameters.get("base_penalty", 0)
        months = parameters.get("months_remaining", 0)
        monthly = parameters.get("monthly_penalty", 0)
        
        prompt = f"""You are a housing/lease legal expert for university students.

LEASE TERMINATION SCENARIO:
- Base early termination penalty: ${base_penalty}
- Months remaining on lease: {months}
- Monthly penalty rate: ${monthly}/month

Calculate the total cost and assess severity. Consider:
- Massachusetts tenant protection laws
- Landlord duty to mitigate (re-rent the unit)
- Typical university housing policies
- Student's potential negotiating options

Respond with ONLY valid JSON:
{{"result": <total dollar cost estimate>, "severity": "<LOW|MODERATE|HIGH>", "reasoning": "<2-3 sentences explaining the cost breakdown and any mitigating factors>", "is_risk": false}}"""

    elif scenario_type == "late_rent":
        rent = parameters.get("monthly_rent", 0)
        late_pct = parameters.get("late_fee_percent", 5)
        daily = parameters.get("daily_fee", 0)
        days = parameters.get("days_late", 0)
        
        prompt = f"""You are a housing legal expert for university students.

LATE RENT SCENARIO:
- Monthly rent: ${rent}
- Late fee percentage: {late_pct}%
- Daily late fee: ${daily}
- Days late: {days}

Calculate total fees. Consider:
- MA law caps late fees
- Grace periods (typically 10-15 days)
- Impact on rental history/references

Respond with ONLY valid JSON:
{{"result": <total fee estimate>, "severity": "<LOW|MODERATE|HIGH>", "reasoning": "<2 sentences on fees and consequences>", "is_risk": false}}"""

    elif scenario_type == "security_deposit":
        deposit = parameters.get("deposit_amount", 0)
        cleaning = parameters.get("cleaning_fee", 0)
        damage = parameters.get("damage_cost", 0)
        unpaid = parameters.get("unpaid_balance", 0)
        
        prompt = f"""You are a housing legal expert for university students.

SECURITY DEPOSIT RETURN SCENARIO:
- Original deposit: ${deposit}
- Estimated cleaning deduction: ${cleaning}
- Estimated damage deduction: ${damage}
- Unpaid rent/utilities: ${unpaid}

Calculate expected return. Consider:
- MA requires itemized deductions within 30 days
- Normal wear and tear cannot be deducted
- Students can dispute unfair deductions

Respond with ONLY valid JSON:
{{"result": <expected return amount>, "severity": "<LOW|MODERATE|HIGH>", "reasoning": "<2 sentences on what to expect>", "is_risk": false}}"""

    elif scenario_type == "credit_reduction":
        current_aid = parameters.get("current_aid", 0)
        current_credits = parameters.get("current_credits", 12)
        new_credits = parameters.get("new_credits", 12)
        full_time = parameters.get("full_time_credits", 12)
        
        prompt = f"""You are a financial aid expert at a US university.

CREDIT REDUCTION SCENARIO:
- Current financial aid: ${current_aid}
- Current credits: {current_credits}
- Proposed new credits: {new_credits}
- Full-time threshold: {full_time} credits

Assess aid impact. Consider:
- Most aid requires at least half-time (6 credits)
- Pell Grant prorates by enrollment
- Some scholarships require full-time
- Loan eligibility thresholds

Respond with ONLY valid JSON:
{{"result": <estimated aid reduction in dollars>, "severity": "<LOW|MODERATE|HIGH|CRITICAL>", "reasoning": "<2-3 sentences on aid impact>", "is_risk": false}}"""

    elif scenario_type == "withdrawal_refund":
        tuition = parameters.get("tuition", 0)
        weeks = parameters.get("weeks_completed", 0)
        total_weeks = parameters.get("total_weeks", 15)
        
        prompt = f"""You are a university financial aid and registrar expert.

WITHDRAWAL REFUND SCENARIO:
- Semester tuition: ${tuition}
- Weeks completed: {weeks} of {total_weeks} total
- Withdrawal timing: {"Early" if weeks <= 2 else "Mid" if weeks <= 6 else "Late"} semester

Calculate refund based on typical university policies. Consider:
- Federal Title IV refund requirements
- Most schools: 100% week 1, decreasing to 0% after ~60% of term
- UMass-style refund schedules
- Housing/meal plan separate considerations

Respond with ONLY valid JSON:
{{"result": <estimated refund amount>, "severity": "<LOW|MODERATE|HIGH>", "reasoning": "<2-3 sentences on refund calculation and what affects it>", "is_risk": false}}"""

    elif scenario_type == "missed_deadline":
        total_aid = parameters.get("total_aid", 0)
        days_late = parameters.get("days_late", 0)
        
        prompt = f"""You are a financial aid expert at a US university.

MISSED FAFSA DEADLINE SCENARIO:
- Typical aid package: ${total_aid}
- Days past priority deadline: {days_late}

Assess impact. Consider:
- Priority deadlines vs final deadlines
- State aid often has strict deadlines
- Federal aid available until June 30
- Institutional aid may be exhausted

Respond with ONLY valid JSON:
{{"result": <estimated aid reduction>, "severity": "<LOW|MODERATE|HIGH|CRITICAL>", "reasoning": "<2-3 sentences on what aid is at risk>", "is_risk": false}}"""

    else:
        # Dynamic handling for any scenario type not explicitly defined
        # Let Gemini reason about it based on the scenario name and parameters
        scenario_name = scenario_type.replace("_", " ").title()
        param_list = "\n".join([f"- {k}: {v}" for k, v in parameters.items()])
        
        prompt = f"""You are an expert advisor for university students. Analyze this scenario.

SCENARIO: {scenario_name}
PARAMETERS:
{param_list}

Based on the scenario name and parameters, provide an intelligent assessment.
Consider relevant rules, regulations, deadlines, or compliance requirements.

Respond with ONLY valid JSON:
{{"result": <numeric value - risk score 0-100 if compliance/risk, or dollar amount if financial>, "severity": "<NONE|LOW|MODERATE|HIGH|CRITICAL>", "reasoning": "<2-3 sentences explaining the assessment>", "is_risk": <true if this is a risk/compliance assessment, false if financial calculation>}}"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        print(f"🤖 [GEMINI SIM] Raw response: {response_text[:300]}...")
        
        # Clean markdown if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        print(f"🤖 [GEMINI SIM] Parsed: result={result.get('result')}, severity={result.get('severity')}")
        return result
        
    except Exception as e:
        print(f"🤖 [GEMINI SIM] Error: {e}")
        logger.error(f"Gemini simulation failed: {e}")
        return {"result": 0, "severity": "ERROR", "reasoning": f"Simulation error: {str(e)}", "is_risk": False}


# ALL simulations use Gemini reasoning for intelligent assessment
SIMULATION_FORMULAS = {
    # Housing simulations
    "early_termination": {
        "label": "Early Lease Termination",
        "formula": "Gemini-assessed cost based on MA tenant law and lease terms",
        "required_params": ["base_penalty", "months_remaining", "monthly_penalty"],
        "domain": "housing"
    },
    "late_rent": {
        "label": "Late Rent Payment",
        "formula": "Gemini-assessed fees considering MA law and grace periods",
        "required_params": ["monthly_rent", "late_fee_percent", "daily_fee", "days_late"],
        "domain": "housing"
    },
    "security_deposit": {
        "label": "Security Deposit Return Estimate",
        "formula": "Gemini-assessed return considering MA deposit laws",
        "required_params": ["deposit_amount", "cleaning_fee", "damage_cost", "unpaid_balance"],
        "domain": "housing"
    },
    # Finance simulations
    "credit_reduction": {
        "label": "Credit Hour Reduction Impact",
        "formula": "Gemini-assessed aid impact based on federal aid rules",
        "required_params": ["current_aid", "current_credits", "new_credits", "full_time_credits"],
        "domain": "finance"
    },
    "withdrawal_refund": {
        "label": "Mid-Semester Withdrawal Refund",
        "formula": "Gemini-assessed refund based on Title IV and university policies",
        "required_params": ["tuition", "weeks_completed", "total_weeks"],
        "domain": "finance"
    },
    "missed_deadline": {
        "label": "Missed FAFSA Deadline Impact",
        "formula": "Gemini-assessed aid risk based on deadline types",
        "required_params": ["total_aid", "days_late"],
        "domain": "finance"
    },
    # Visa simulations
    "work_hours_violation": {
        "label": "Work Hour Violation Risk",
        "formula": "Gemini-assessed risk based on F-1 work authorization rules",
        "required_params": ["hours_worked", "max_allowed_hours"],
        "domain": "visa"
    },
    "course_load_drop": {
        "label": "Course Load Drop Impact",
        "formula": "Gemini-assessed SEVIS compliance risk",
        "required_params": ["current_credits", "minimum_credits", "has_rpe_approval"],
        "domain": "visa"
    }
}






@router.post("/simulate", response_model=SimulateResponse)
async def run_simulation(request: SimulateRequest):
    """Run Gemini-powered scenario simulation with intelligent reasoning."""
    try:
        print(f"\n{'='*60}")
        print(f"🧮 [SIMULATE API] POST /api/simulate called")
        print(f"{'='*60}")
        
        scenario_type = request.scenario_type
        parameters = request.parameters
        
        print(f"🧮 [SIMULATE API] Scenario type: {scenario_type}")
        print(f"🧮 [SIMULATE API] Parameters: {parameters}")
        
        # Check if scenario type exists in predefined formulas
        if scenario_type in SIMULATION_FORMULAS:
            scenario = SIMULATION_FORMULAS[scenario_type]
            scenario_label = scenario["label"]
            scenario_formula = scenario["formula"]
            scenario_domain = scenario["domain"]
            required_params = scenario.get("required_params", [])
            print(f"🧮 [SIMULATE API] Found predefined scenario: {scenario_label}")
        else:
            # Dynamic scenario - handle via Gemini
            scenario_label = scenario_type.replace("_", " ").title()
            scenario_formula = "Gemini-assessed based on scenario context"
            scenario_domain = "general"
            required_params = list(parameters.keys())
            print(f"🧮 [SIMULATE API] Dynamic scenario: {scenario_label}")
        
        # ALL simulations use Gemini for intelligent reasoning
        print(f"🧮 [SIMULATE API] Using Gemini for intelligent assessment...")
        gemini_result = await get_gemini_simulation(scenario_type, parameters)
        
        result = gemini_result.get("result", 0)
        explanation = gemini_result.get("reasoning", "Assessment completed.")
        severity = gemini_result.get("severity", "UNKNOWN")
        is_risk = gemini_result.get("is_risk", False)
        
        print(f"🧮 [SIMULATE API] ✅ Gemini Result: {result}, severity: {severity}")
        print(f"🧮 [SIMULATE API] Reasoning: {explanation}")
        
        # Build breakdown with Gemini's assessment
        breakdown = {param: parameters.get(param, 0) for param in required_params}
        breakdown["gemini_result"] = result
        breakdown["severity"] = severity
        breakdown["is_risk_assessment"] = is_risk
        
        # Domain-specific caveats
        caveats = []
        
        if scenario_domain == "housing":
            caveats.append("This estimate considers MA tenant protection laws.")
            caveats.append("Contact Student Legal Services for lease-related questions.")
        elif scenario_domain == "finance":
            caveats.append("This estimate is based on typical federal and institutional aid policies.")
            caveats.append("Contact the Financial Aid Office for your specific situation.")
        elif scenario_domain == "visa":
            caveats.append("Immigration consequences are serious - this is for awareness only.")
            caveats.append("Contact the International Programs Office IMMEDIATELY for any concerns.")
        else:
            caveats.append("This is an AI-generated estimate for guidance only.")
            caveats.append("Consult the appropriate campus office for official information.")
        
        print(f"🧮 [SIMULATE API] ✅ Returning response")
        print(f"{'='*60}\n")
        
        return SimulateResponse(
            scenario_type=scenario_type,
            scenario_label=scenario_label,
            exposure_estimate=round(float(result), 2),
            formula_used=scenario_formula,
            explanation=explanation,
            breakdown=breakdown,
            caveats=caveats,
            severity=severity,
            is_risk=is_risk
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🧮 [SIMULATE API] ❌ ERROR: {e}")
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


