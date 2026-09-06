from typing import List

from pydantic import BaseModel, Field

from app.database.base import RiskLevel


class RiskFactor(BaseModel):
    code: str
    description: str
    contribution: float = Field(ge=0.0)


class RiskResult(BaseModel):
    """Structured output produced by the risk engine."""

    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    suggested_action: str

    @property
    def severity(self) -> RiskLevel:
        return self.risk_level
