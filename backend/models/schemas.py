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


class TranslateRequest(BaseModel):
    """Request for translation."""
    session_id: str
    target_language: str


class TranslateResponse(BaseModel):
    """Response for translation."""
    language: str
    translated_text: str
    context_note: str = "Student-friendly explanation translated from English."


class ScenarioRequest(BaseModel):
    """Request for scenario simulation."""
    session_id: str
    scenario_description: str


class ScenarioResponse(BaseModel):
    """Response for scenario simulation."""
    scenario: str
    what_happens: str  # Plain language explanation
    implications: List[str]
    suggested_steps: List[str]
    caveats: List[str] = []


class ResourceQueryResponse(BaseModel):
    """Response for resource search."""
    results: List[Resource]
    total_found: int
