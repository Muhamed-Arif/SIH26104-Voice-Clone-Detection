import uuid
import pytest
from starlette.testclient import TestClient
from main import app
from app.database.connection import get_db
from tests.fixtures.audio_fixtures import generate_synthetic_audio_payload


def test_websocket_stream_flow(sample_user, db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    session_id = str(uuid.uuid4())
    client = TestClient(app)

    with client.websocket_connect(f"/api/v1/stream?session_id={session_id}") as websocket:
        # Initial greeting
        init_data = websocket.receive_json()
        assert init_data["type"] == "CONNECTION_ESTABLISHED"
        assert init_data["session_id"] == session_id
        assert init_data["status"] == "READY"

        # Send ping
        websocket.send_json({"type": "PING", "timestamp": "123456"})
        pong_data = websocket.receive_json()
        assert pong_data["type"] == "PONG"

        # Send chunk frame
        chunk = generate_synthetic_audio_payload("stream-chunk-01")
        websocket.send_json(chunk)

        result = websocket.receive_json()
        assert result["type"] == "ANALYSIS_RESULT"
        assert result["data"]["chunk_id"] == "stream-chunk-01"
        assert result["data"]["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

    app.dependency_overrides.clear()
