import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.analysis_repository import AnalysisRepository
from app.database.base import RiskLevel


class ResultAggregator:
    """Aggregates analysis metrics and scores across chunks within a session."""

    def __init__(self, db: AsyncSession):
        self.analysis_repo = AnalysisRepository(db)

    async def aggregate_session_metrics(
        self, session_id: uuid.UUID
    ) -> Dict[str, Any]:
        events = await self.analysis_repo.get_session_events(session_id, limit=500)
        if not events:
            return {
                "session_id": str(session_id),
                "total_chunks": 0,
                "average_risk_score": 0.0,
                "max_risk_score": 0,
                "overall_risk_level": "LOW",
                "synthetic_ratio": 0.0,
                "high_risk_chunks_count": 0,
            }

        total_chunks = len(events)
        total_risk = sum(e.risk_score for e in events)
        max_risk = max(e.risk_score for e in events)
        high_risk_count = sum(1 for e in events if e.risk_level == RiskLevel.HIGH)
        avg_risk = total_risk / total_chunks

        if max_risk >= 70 or high_risk_count > 0:
            overall_level = "HIGH"
        elif avg_risk >= 30:
            overall_level = "MEDIUM"
        else:
            overall_level = "LOW"

        return {
            "session_id": str(session_id),
            "total_chunks": total_chunks,
            "average_risk_score": round(avg_risk, 2),
            "max_risk_score": max_risk,
            "overall_risk_level": overall_level,
            "high_risk_chunks_count": high_risk_count,
            "synthetic_ratio": round(high_risk_count / total_chunks, 3),
        }
