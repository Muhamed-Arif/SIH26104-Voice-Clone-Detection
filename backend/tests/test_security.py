import uuid
import pytest
from httpx import AsyncClient
from app.core.exceptions import InvalidAudioChunkException
from app.security.authentication import create_access_token
from app.security.validation import validate_dsp_chunk
from app.schemas.audio import DSPAudioChunk


def test_token_creation_and_validation():
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, role="admin")
    assert isinstance(token, str)
    assert len(token) > 20


def test_dsp_validation_success():
    chunk = DSPAudioChunk(
        waveform="dGVzdF93YXZlZm9ybQ==",
        sample_rate=16000,
        chunk_id="valid-chunk-01",
        quality="HIGH",
        timestamp="2026-09-05T22:00:00Z",
    )
    assert validate_dsp_chunk(chunk) is True


def test_dsp_validation_invalid_sample_rate():
    chunk = DSPAudioChunk(
        waveform="dGVzdF93YXZlZm9ybQ==",
        sample_rate=0,
        chunk_id="invalid-rate-chunk",
        quality="HIGH",
        timestamp="2026-09-05T22:00:00Z",
    )
    with pytest.raises(InvalidAudioChunkException):
        validate_dsp_chunk(chunk)


def test_dsp_validation_empty_chunk_id():
    chunk = DSPAudioChunk(
        waveform="dGVzdF93YXZlZm9ybQ==",
        sample_rate=16000,
        chunk_id="   ",
        quality="HIGH",
        timestamp="2026-09-05T22:00:00Z",
    )
    with pytest.raises(InvalidAudioChunkException):
        validate_dsp_chunk(chunk)


@pytest.mark.asyncio
async def test_validation_error_shape(client: AsyncClient):
    # Invalid request body without required fields
    response = await client.post("/api/v1/analyze", json={"sample_rate": 16000})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
