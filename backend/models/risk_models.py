from pydantic import BaseModel
from typing import Optional, List


class RiskModel:
    """Risk scoring formulas."""
    
    @staticmethod
    def normalize_value(value: float, min_threshold: float, max_threshold: float) -> float:
        """Normalize a value to 0-1 range based on thresholds."""
        if value <= min_threshold:
            return 0.0
        if value >= max_threshold:
            return 1.0
        return (value - min_threshold) / (max_threshold - min_threshold)
    
    @staticmethod
    def finance_risk_score(
        financial_exposure: float,
        penalty_escalation: float,
        deadline_sensitivity: float
    ) -> float:
        """
        Calculate finance domain risk score.
        Risk Score = (0.4 × Financial Exposure Indicator)
                   + (0.3 × Penalty Escalation Indicator)
                   + (0.3 × Deadline Sensitivity Indicator)
        """
        score = (0.4 * financial_exposure +
                 0.3 * penalty_escalation +
                 0.3 * deadline_sensitivity)
        return min(1.0, max(0.0, score))
    
    @staticmethod
    def housing_risk_score(
        termination_penalty: float,
        liability_clause: float,
        payment_obligation: float
    ) -> float:
        """
        Calculate housing domain risk score.
        Risk Score = (0.35 × Termination Penalty Indicator)
                   + (0.35 × Liability Clause Indicator)
                   + (0.30 × Payment Obligation Indicator)
        """
        score = (0.35 * termination_penalty +
                 0.35 * liability_clause +
                 0.30 * payment_obligation)
        return min(1.0, max(0.0, score))
    
    @staticmethod
    def risk_level_from_score(score: float) -> str:
        """Map numeric risk score to level."""
        if score < 0.4:
            return "LOW"
        elif score < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"


class FinanceIndicators(BaseModel):
    """Finance risk indicators."""
    financial_exposure_amount: float
    financial_exposure_indicator: float
    penalty_escalation_indicator: float
    deadline_sensitivity_indicator: float


class HousingIndicators(BaseModel):
    """Housing risk indicators."""
    termination_penalty_indicator: float
    liability_clause_indicator: float
    payment_obligation_indicator: float


class VisaRiskLevel(BaseModel):
    """Visa risk classification."""
    level: str  # COMPLIANT, AT_RISK, VIOLATION_LIKELY
    factors: List[str]
