import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import User


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient, sample_user: User):
    payload = {
        "user_id": str(sample_user.id),
        "mode": "realtime",
        "metadata": {"source": "mobile_app"},
    }
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(sample_user.id)
    assert data["mode"] == "realtime"
    assert data["status"] == "active"
    assert "session_id" in data


@pytest.mark.asyncio
async def test_get_session(client: AsyncClient, sample_user: User):
    # Create first
    payload = {
        "user_id": str(sample_user.id),
        "mode": "realtime",
    }
    create_resp = await client.post("/api/v1/sessions", json=payload)
    session_id = create_resp.json()["session_id"]

    # Retrieve
    get_resp = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_get_nonexistent_session(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/sessions/{fake_id}")
    assert response.status_code == 404
    assert response.json()["success"] is False
