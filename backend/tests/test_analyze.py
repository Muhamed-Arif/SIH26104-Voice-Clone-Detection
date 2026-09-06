import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import AnalysisEvent, Alert, AuditLog, User
from tests.fixtures.audio_fixtures import generate_synthetic_audio_payload, generate_genuine_audio_payload


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_analyze_high_risk_chunk(client: AsyncClient, sample_user: User, db_session: AsyncSession):
    # 1. Create a session first
    sess_resp = await client.post("/api/v1/sessions", json={"user_id": str(sample_user.id), "mode": "realtime"})
    session_id = sess_resp.json()["session_id"]

    # 2. Ingest spoof audio chunk
    chunk_payload = generate_synthetic_audio_payload(chunk_id="chunk-synthetic-test-01")
    chunk_payload["session_id"] = session_id

    response = await client.post("/api/v1/analyze", json=chunk_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] == session_id
    assert data["chunk_id"] == "chunk-synthetic-test-01"
    assert data["risk_level"] == "HIGH"
    assert data["risk_score"] >= 70
    assert data["action"] == "BLOCK"
    assert data["alert"] is not None
    assert data["alert"]["severity"] == "HIGH"
    assert data["alert"]["status"] == "OPEN"

    analysis_id = uuid.UUID(data["analysis_id"])

    # Verify DB persistence
    res = await db_session.execute(select(AnalysisEvent).where(AnalysisEvent.analysis_id == analysis_id))
    persisted_event = res.scalar_one_or_none()
    assert persisted_event is not None
    assert persisted_event.risk_score == data["risk_score"]

    # Verify Alert in DB
    alert_res = await db_session.execute(select(Alert).where(Alert.analysis_id == analysis_id))
    persisted_alert = alert_res.scalar_one_or_none()
    assert persisted_alert is not None
    assert persisted_alert.status == "OPEN"

    # Verify Audit Log in DB
    audit_res = await db_session.execute(select(AuditLog).where(AuditLog.analysis_id == analysis_id))
    audit_log = audit_res.scalar_one_or_none()
    assert audit_log is not None
    assert audit_log.outcome == "FLAGGED_HIGH_RISK"


@pytest.mark.asyncio
async def test_analyze_low_risk_chunk(client: AsyncClient, sample_user: User, db_session: AsyncSession):
    sess_resp = await client.post("/api/v1/sessions", json={"user_id": str(sample_user.id), "mode": "realtime"})
    session_id = sess_resp.json()["session_id"]

    chunk_payload = generate_genuine_audio_payload(chunk_id="chunk-genuine-test-01")
    chunk_payload["session_id"] = session_id

    response = await client.post("/api/v1/analyze", json=chunk_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["risk_level"] == "LOW"
    assert data["risk_score"] < 30
    assert data["action"] == "ALLOW"
    assert data["alert"] is None


@pytest.mark.asyncio
async def test_get_analysis_result(client: AsyncClient, sample_user: User):
    # Post analysis
    chunk_payload = generate_synthetic_audio_payload(chunk_id="chunk-query-test")
    analyze_resp = await client.post("/api/v1/analyze", json=chunk_payload)
    analysis_id = analyze_resp.json()["analysis_id"]

    # Get by ID
    get_resp = await client.get(f"/api/v1/results/{analysis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["analysis_id"] == analysis_id


@pytest.mark.asyncio
async def test_manual_verification_override(client: AsyncClient, sample_user: User, db_session: AsyncSession):
    # Post high risk analysis
    chunk_payload = generate_synthetic_audio_payload(chunk_id="chunk-to-verify")
    analyze_resp = await client.post("/api/v1/analyze", json=chunk_payload)
    analysis_id = analyze_resp.json()["analysis_id"]

    # Submit verification
    verify_payload = {
        "analysis_id": analysis_id,
        "verifier_id": str(sample_user.id),
        "decision": "CONFIRMED_SPOOF",
        "notes": "Analyst confirmed unnatural pitch jitter in formant 2.",
    }
    verify_resp = await client.post("/api/v1/verify", json=verify_payload)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "SUCCESS"
    assert verify_resp.json()["decision"] == "CONFIRMED_SPOOF"

    # Verify alert status updated to ACKNOWLEDGED
    alert_res = await db_session.execute(select(Alert).where(Alert.analysis_id == uuid.UUID(analysis_id)))
    alert = alert_res.scalar_one_or_none()
    assert alert.status == "ACKNOWLEDGED"
