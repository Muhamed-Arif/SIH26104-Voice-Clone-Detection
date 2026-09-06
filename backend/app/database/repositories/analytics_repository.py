from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Alert, AnalysisEvent, RiskLevel, Session


class AnalyticsRepository:
    """Read-only aggregate queries for the analysis dashboard."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def overview(self) -> dict[str, Any]:
        analysis_stats = await self.db.execute(
            select(
                func.count(AnalysisEvent.analysis_id),
                func.avg(AnalysisEvent.confidence),
                func.avg(AnalysisEvent.risk_score),
            )
        )
        total_analyses, average_confidence, average_risk_score = analysis_stats.one()

        total_sessions = await self.db.scalar(select(func.count(Session.session_id))) or 0
        high_risk_alerts = await self.db.scalar(
            select(func.count(Alert.alert_id)).where(Alert.severity == RiskLevel.HIGH.value)
        ) or 0

        risk_distribution = await self._distribution(AnalysisEvent.risk_level)
        severity_distribution = await self._distribution(Alert.severity)
        recent = await self.recent_statistics()

        return {
            "total_analyses": int(total_analyses or 0),
            "total_sessions": int(total_sessions),
            "average_confidence": round(float(average_confidence or 0.0), 4),
            "average_risk_score": round(float(average_risk_score or 0.0), 2),
            "high_risk_alerts": int(high_risk_alerts),
            "risk_distribution": risk_distribution,
            "severity_distribution": severity_distribution,
            "recent": recent,
        }

    async def risk_summary(self) -> dict[str, Any]:
        overview = await self.overview()
        return {
            "risk_distribution": overview["risk_distribution"],
            "severity_distribution": overview["severity_distribution"],
            "average_risk_score": overview["average_risk_score"],
            "average_confidence": overview["average_confidence"],
        }

    async def recent_statistics(self, periods: int = 7) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        statistics: list[dict[str, Any]] = []
        for days_ago in range(periods - 1, -1, -1):
            start = (now - timedelta(days=days_ago + 1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            result = await self.db.execute(
                select(
                    func.count(AnalysisEvent.analysis_id),
                    func.sum(case((AnalysisEvent.risk_level == RiskLevel.HIGH, 1), else_=0)),
                    func.avg(AnalysisEvent.risk_score),
                    func.avg(AnalysisEvent.confidence),
                ).where(AnalysisEvent.created_at >= start, AnalysisEvent.created_at < end)
            )
            analyses, high_risk, average_risk_score, average_confidence = result.one()
            statistics.append(
                {
                    "period": start.date().isoformat(),
                    "analyses": int(analyses or 0),
                    "high_risk": int(high_risk or 0),
                    "average_risk_score": round(float(average_risk_score or 0.0), 2),
                    "average_confidence": round(float(average_confidence or 0.0), 4),
                }
            )
        return statistics

    async def sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        risk_order = case(
            (AnalysisEvent.risk_level == RiskLevel.HIGH, 3),
            (AnalysisEvent.risk_level == RiskLevel.MEDIUM, 2),
            else_=1,
        )
        result = await self.db.execute(
            select(
                Session.session_id,
                Session.status,
                Session.mode,
                Session.start_time,
                Session.end_time,
                func.count(AnalysisEvent.analysis_id).label("analysis_count"),
                func.coalesce(func.avg(AnalysisEvent.risk_score), 0.0).label("average_risk_score"),
                func.coalesce(func.max(risk_order), 1).label("highest_risk_order"),
            )
            .outerjoin(AnalysisEvent, AnalysisEvent.session_id == Session.session_id)
            .group_by(Session.session_id)
            .order_by(Session.start_time.desc())
            .limit(limit)
        )
        rows = result.all()
        risk_names = {1: RiskLevel.LOW.value, 2: RiskLevel.MEDIUM.value, 3: RiskLevel.HIGH.value}
        return [
            {
                "session_id": str(row.session_id),
                "status": row.status,
                "mode": row.mode,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "analysis_count": int(row.analysis_count or 0),
                "average_risk_score": round(float(row.average_risk_score or 0.0), 2),
                "highest_risk_level": risk_names.get(int(row.highest_risk_order), RiskLevel.LOW.value),
            }
            for row in rows
        ]

    async def _distribution(self, column: Any) -> dict[str, int]:
        result = await self.db.execute(
            select(column, func.count()).group_by(column)
        )
        return {
            (key.value if isinstance(key, RiskLevel) else str(key)): int(count)
            for key, count in result.all()
            if key is not None
        }
