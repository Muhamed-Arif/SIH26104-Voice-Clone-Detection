from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.schemas.analytics import AnalyticsOverview, RiskAnalytics, SessionAnalyticsResponse
from app.security.dependencies import require_admin
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview", response_model=AnalyticsOverview, summary="Get system-wide analytics overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> AnalyticsOverview:
    return await AnalyticsService(db).get_overview()

@router.get("/summary", response_model=AnalyticsOverview, include_in_schema=False)
async def get_analytics_summary_legacy(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> AnalyticsOverview:
    return await AnalyticsService(db).get_overview()

@router.get("/risk", response_model=RiskAnalytics, summary="Get risk and severity distributions")
async def get_risk_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> RiskAnalytics:
    return await AnalyticsService(db).get_risk_summary()

@router.get("/sessions", response_model=SessionAnalyticsResponse, summary="List recent session analytics")
async def get_session_analytics(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> SessionAnalyticsResponse:
    return await AnalyticsService(db).get_sessions(limit=limit)
