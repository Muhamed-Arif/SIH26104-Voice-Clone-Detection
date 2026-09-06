from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class RecentAnalysisStatistics(BaseModel):
    period: str
    analyses: int
    high_risk: int
    average_risk_score: float
    average_confidence: float


class AnalyticsOverview(BaseModel):
    total_analyses: int
    total_sessions: int
    average_confidence: float
    average_risk_score: float
    high_risk_alerts: int
    risk_distribution: Dict[str, int] = Field(default_factory=dict)
    severity_distribution: Dict[str, int] = Field(default_factory=dict)
    recent: List[RecentAnalysisStatistics] = Field(default_factory=list)


class RiskAnalytics(BaseModel):
    risk_distribution: Dict[str, int] = Field(default_factory=dict)
    severity_distribution: Dict[str, int] = Field(default_factory=dict)
    average_risk_score: float
    average_confidence: float


class SessionAnalytics(BaseModel):
    session_id: str
    status: str
    mode: str
    start_time: datetime
    end_time: datetime | None = None
    analysis_count: int
    average_risk_score: float
    highest_risk_level: str


class SessionAnalyticsResponse(BaseModel):
    sessions: List[SessionAnalytics] = Field(default_factory=list)
    total: int
