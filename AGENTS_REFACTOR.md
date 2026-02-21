# Agent System Refactor - Feature/Agents Branch

## What Changed

### ❌ Removed
- **Math-based Risk Engine**: No more risk indicators (0-1 scores), financial exposure calculations, penalty escalation scoring
- **JSON Rigidity**: Removed strict JSON enforcement with retry logic
- **RiskModel Dependency**: Eliminated all mathematical risk computations
- **Variable Extraction**: Stopped trying to extract and score individual indicators

### ✅ Added

#### 1. **Reasoning-Based Agents**
Each agent now uses plain language reasoning instead of JSON/math:

- **Router Agent**: Classifies document by analyzing purpose, type, and critical concerns
- **Finance Agent**: Identifies all financial touchpoints through logical analysis
- **Housing Agent**: Processes terms, dates, and policies via reasoning
- **Visa Agent**: Extracts compliance requirements through legal analysis
- **RAG Agent**: Bridges findings to actual campus resources
- **Risk Agent**: Performs holistic risk assessment through reasoning (LOW/MEDIUM/HIGH)

#### 2. **Global Retrieval Tool**
`get_context_for_agent()` function accessible to ALL agents:
```python
context = await get_context_for_agent(
    query_text="your specific query",
    domain="finance/housing/visa",
    top_k=5
)
```

#### 3. **Better Prompts**
All agents use Gemini's standard output mode with:
- Clear role definition
- Task-focused instructions
- Context injection from retrieval tool
- Natural language expectations

#### 4. **Simplified AgentState**
```typescript
AgentState {
  session_id: str
  raw_text: str
  domain: str
  clauses: List[str]
  obligations: List[str]
  financial_details: str          // Natural language findings
  housing_details: str            // Natural language findings
  visa_details: str               // Natural language findings
  risk_assessment: str            // Reasoned risk analysis
  red_flags: List[str]           // Text-based red flags
  resources: List[Dict]          // Campus resources
  error: Optional[str]
}
```

## Agent Flow

```
Document Input
    ↓
Router Agent (classify + extract critical concerns)
    ↓
Domain-Specific Agent (Finance/Housing/Visa)
    ↓
RAG Agent (match to campus resources)
    ↓
Risk Agent (holistic reasoning-based assessment)
    ↓
Output (findings, red flags, resources)
```

## Key Improvements

1. **No Math** - Pure logical reasoning by agents
2. **No JSON Parsing** - Natural language from Gemini
3. **Accessible Retrieval** - All agents can call `get_context_for_agent()`
4. **Better Prompts** - Based on sample prompts provided
5. **Human-Readable Output** - Plain text analysis instead of score matrices
6. **Red Flags** - Text-based instead of calculated risk indicators
7. **Flexibility** - Agents can reason about ambiguity instead of forcing structure

## Usage Example

```python
from agents import run_analysis_workflow

result = await run_analysis_workflow(
    session_id="session_123",
    raw_text=document_content
)

# Access outputs
print(result["financial_details"])      # Agent reasoning about finances
print(result["risk_assessment"])        # Agent reasoning about risks
print(result["red_flags"])              # List of identified red flags
print(result["resources"])              # Campus resources to help
```

## Next Steps

1. Update main.py endpoints to consume new AgentState structure
2. Update frontend to display text-based findings instead of risk scores
3. Add specialized reasoning for edge cases
4. Implement agent memory/context carrying between agents
5. Add user feedback loop to improve agent reasoning
