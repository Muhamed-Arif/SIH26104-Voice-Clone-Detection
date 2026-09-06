import uuid
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class DSPAudioChunk(BaseModel):
    """DSP chunk payload contract from Member 2."""
    waveform: Union[str, List[float]] = Field(
        ...,
        description="Audio waveform represented as base64 string, byte string, or float array",
    )
    sample_rate: int = Field(
        default=16000,
        description="Sample rate in Hz (standard: 16000)",
    )
    chunk_id: str = Field(
        ...,
        description="Unique identifier for this audio chunk",
    )
    quality: str = Field(
        default="HIGH",
        description="Estimated audio signal quality metric (e.g. HIGH, MEDIUM, DEGRADED)",
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 string timestamp of chunk capture",
    )
    session_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional session ID if not provided in URL or header context",
    )
