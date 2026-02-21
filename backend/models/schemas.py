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


class RiskIndicator(BaseModel):
    """Individual risk factor."""
    name: str
    value: float
    contribution: float


class Clause(BaseModel):
    """Extracted clause with risk assessment."""
    clause_id: str
    text: str
    risk_contribution: float
    flag: str
    plain_explanation: str


class Resource(BaseModel):
    """Campus resource reference."""
    name: str
    url: str
    relevance: float
    description: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response for document analysis."""
    session_id: str
    domain: str
    risk_score: float
    risk_level: str
    clauses: List[Clause] = []
    obligations: List[str] = []
    deadlines: List[str] = []
    resources: List[Resource] = []
    summary: str


class TranslateRequest(BaseModel):
    """Request for translation."""
    session_id: str
    target_language: str


class TranslateResponse(BaseModel):
    """Response for translation."""
    language: str
    translated_text: str
    context_note: str = "Student-friendly institutional explanation translated from English."


class ScenarioParams(BaseModel):
    """Parameters for scenario simulation."""
    months_remaining: Optional[int] = None
    penalty_rate_per_month: Optional[float] = None
    base_penalty: Optional[float] = None
    additional_params: Optional[Dict[str, Any]] = None


class SimulateRequest(BaseModel):
    """Request for scenario simulation."""
    session_id: str
    scenario: str
    parameters: ScenarioParams


class SimulateResponse(BaseModel):
    """Response for scenario simulation."""
    scenario: str
    exposure_estimate: float
    formula_used: str
    explanation: str
    caveats: List[str] = []


class ResourceQueryResponse(BaseModel):
    """Response for resource search."""
    results: List[Resource]
