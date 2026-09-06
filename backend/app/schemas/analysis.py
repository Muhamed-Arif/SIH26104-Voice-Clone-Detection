import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.database.base import RiskLevel
from app.risk_engine.models.risk_result import RiskFactor


class MLPrediction(BaseModel):
    """External prediction contract with Member 1."""
    synthetic_probability: float = Field(..., ge=0.0, le=1.0, description="Model synthetic probability")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence score")
    model_version: str = Field(default="v0.3", description="Model version tag")


class AlertResponse(BaseModel):
    alert_id: uuid.UUID
    analysis_id: uuid.UUID
    severity: str
    status: str
    acknowledged_by: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResultResponse(BaseModel):
    analysis_id: uuid.UUID
    session_id: uuid.UUID
    chunk_id: str
    synthetic_probability: float
    confidence: float
    risk_score: int
    risk_level: RiskLevel
    audio_quality: str
    action: str
    latency_ms: float
    model_version: Optional[str]
    created_at: datetime
    reason_codes: List[str] = Field(default_factory=list)
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    alert: Optional[AlertResponse] = None

    model_config = {"from_attributes": True}
