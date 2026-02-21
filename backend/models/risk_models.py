from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class RiskAssessment(BaseModel):
    """Text-based risk assessment - no math."""
    risk_level: str  # LOW, MEDIUM, or HIGH
    reasoning: str  # Why this risk level?
    red_flags: List[str]  # Specific concerns
    recommendations: List[str]  # What should the student do?


class FinancialAnalysis(BaseModel):
    """Financial findings from reasoning."""
    obligations: List[str]  # What must be paid?
    deadlines: List[str]  # When?
    hidden_costs: List[str]  # Unexpected fees?
    summary: str  # Plain language explanation


class HousingAnalysis(BaseModel):
    """Housing findings from reasoning."""
    move_in_date: Optional[str]
    move_out_date: Optional[str]
    cancellation_policy: str  # Plain language explanation
    buyout_costs: Optional[str]
    maintenance_responsibilities: List[str]
    summary: str


class VisaAnalysis(BaseModel):
    """Visa/compliance findings from reasoning."""
    status: str  # COMPLIANT, AT_RISK, or VIOLATION_LIKELY
    requirements: List[str]  # What's required?
    deadlines: List[str]  # Critical dates
    compliance_obligations: List[str]  # What must be done?
    reasoning: str  # Why this status?


class DocumentAnalysisResult(BaseModel):
    """Complete analysis result."""
    session_id: str
    document_domain: str  # finance, housing, visa, or mixed
    financial_analysis: Optional[FinancialAnalysis] = None
    housing_analysis: Optional[HousingAnalysis] = None
    visa_analysis: Optional[VisaAnalysis] = None
    overall_risk: RiskAssessment
    resources: List[Dict[str, Any]]  # Campus resources
    analysis_notes: str  # Any caveats or special considerations
