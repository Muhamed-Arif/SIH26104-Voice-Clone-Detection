import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import RiskLevel
from app.database.repositories.analysis_repository import AnalysisRepository
from app.database.repositories.session_repository import SessionRepository
from app.security.authentication import get_current_user


@pytest.mark.asyncio
async def test_analytics_endpoints_use_persisted_data(
    client: AsyncClient, db_session: AsyncSession, sample_user
):
    async def admin_user():
        return {"user_id": sample_user.id, "role": "admin"}

    from main import app
    app.dependency_overrides[get_current_user] = admin_user
    session_id = __import__("uuid").uuid4()
    await SessionRepository(db_session).create_session(session_id, sample_user.id)
    await AnalysisRepository(db_session).create_analysis_event(
        analysis_id=__import__("uuid").uuid4(),
        session_id=session_id,
        chunk_id="analytics-test",
        synthetic_probability=0.9,
        confidence=0.8,
        risk_score=85,
        risk_level=RiskLevel.HIGH,
    )
    await db_session.commit()

    overview = await client.get("/api/v1/analytics/overview")
    risk = await client.get("/api/v1/analytics/risk")
    sessions = await client.get("/api/v1/analytics/sessions")

    assert overview.status_code == 200
    assert overview.json()["total_analyses"] == 1
    assert overview.json()["risk_distribution"]["HIGH"] == 1
    assert risk.json()["average_risk_score"] == 85.0
    assert sessions.json()["total"] == 1
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analytics_requires_admin(client: AsyncClient):
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 401
