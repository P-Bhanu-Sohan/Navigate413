from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UploadRequest(BaseModel):
    """Request for file upload."""
    pass  # File comes via multipart form


class UploadResponse(BaseModel):
    """Response for file upload."""
    session_id: str
    file_name: str
    status: str = "processing"
    upload_timestamp: datetime


class AnalyzeRequest(BaseModel):
    """Request for document analysis."""
    session_id: str
    language: str = "en"


class RedFlag(BaseModel):
    """A specific concern identified in the document."""
    description: str
    reasoning: str
    suggested_action: Optional[str] = None


class Clause(BaseModel):
    """Extracted clause with explanation (no math)."""
    clause_id: str
    text: str
    explanation: str
    relevance_to_student: str


class Resource(BaseModel):
    """Campus resource reference."""
    name: str
    url: str
    reason_relevant: str  # Why is this relevant to the student?
    description: Optional[str] = None


class SimulationOption(BaseModel):
    """A simulation option extracted from document analysis."""
    scenario_type: str  # e.g., "early_termination", "credit_reduction"
    label: str  # Human-readable label
    description: str  # What this simulation calculates
    parameters: Dict[str, Any]  # Default values extracted from document
    formula: str  # The formula used


class AnalyzeResponse(BaseModel):
    """Response for document analysis."""
    session_id: str
    domain: str
    risk_score: float = 0.5  # 0.0 to 1.0 numeric score for frontend gauge
    risk_level: str  # LOW, MEDIUM, HIGH
    risk_reasoning: str  # Why this level?
    clauses: List[Clause] = []
    obligations: List[str] = []
    deadlines: List[str] = []
    red_flags: List[RedFlag] = []
    resources: List[Resource] = []
    summary: str
    recommendations: List[str] = []
    available_simulations: List[SimulationOption] = []  # Dynamic simulations based on document


class TranslateRequest(BaseModel):
    """Request for translation."""
    session_id: str
    target_language: str


class TranslateResponse(BaseModel):
    """Response for translation."""
    language: str
    translated_text: str
    context_note: str = "Student-friendly explanation translated from English."


class SimulateRequest(BaseModel):
    """Request for scenario simulation."""
    session_id: str
    scenario_type: str  # e.g., "early_termination", "credit_reduction"
    parameters: Dict[str, Any]  # User-provided or default values (can include booleans)


class SimulateResponse(BaseModel):
    """Response for scenario simulation."""
    scenario_type: str
    scenario_label: str
    exposure_estimate: float
    formula_used: str
    explanation: str
    breakdown: Dict[str, Any] = {}  # Show calculation steps
    caveats: List[str] = []
    severity: str = "UNKNOWN"  # NONE, LOW, MODERATE, HIGH, CRITICAL
    is_risk: bool = False  # True if this is a risk assessment (0-100), False if dollar amount


class ResourceQueryResponse(BaseModel):
    """Response for resource search."""
    results: List[Resource]
    total_found: int
