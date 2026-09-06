from typing import List, Optional
from pydantic import BaseModel, Field
from app.database.base import RiskLevel


class RiskAssessment(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Composite risk score from 0 to 100")
    risk_level: RiskLevel = Field(..., description="Categorical risk classification: LOW, MEDIUM, HIGH")
    reason_codes: List[str] = Field(default_factory=list, description="Reason codes describing risk drivers")
    suggested_action: str = Field(..., description="Action recommendation: ALLOW, ALERT, or BLOCK")
