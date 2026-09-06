from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    """Application service for dashboard analytics."""

    def __init__(self, db: AsyncSession):
        self.repository = AnalyticsRepository(db)

    async def get_overview(self) -> dict:
        return await self.repository.overview()

    async def get_risk_summary(self) -> dict:
        return await self.repository.risk_summary()

    async def get_sessions(self, limit: int = 50) -> dict:
        sessions = await self.repository.sessions(limit=limit)
        return {"sessions": sessions, "total": len(sessions)}
