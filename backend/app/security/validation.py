import base64
from typing import Any
from app.core.exceptions import InvalidAudioChunkException
from app.schemas.audio import DSPAudioChunk


def validate_dsp_chunk(chunk: DSPAudioChunk) -> bool:
    """Validates DSP chunk integrity, sample rate, and waveform format.
    
    # TODO(M5): Add cryptographic HMAC signature verification for DSP stream payloads.
    # TODO(M5): Add deep audio packet inspection for buffer overflow or polyglot payload sanitization.
    """
    if chunk.sample_rate <= 0 or chunk.sample_rate > 192000:
        raise InvalidAudioChunkException(
            f"Invalid sample rate {chunk.sample_rate} Hz (must be between 8000 and 192000 Hz)"
        )

    if not chunk.chunk_id or len(chunk.chunk_id.strip()) == 0:
        raise InvalidAudioChunkException("chunk_id must not be empty")

    if not chunk.timestamp:
        raise InvalidAudioChunkException("timestamp must not be empty")

    if isinstance(chunk.waveform, str):
        if len(chunk.waveform.strip()) == 0:
            raise InvalidAudioChunkException("waveform string must not be empty")
    elif isinstance(chunk.waveform, list):
        if len(chunk.waveform) == 0:
            raise InvalidAudioChunkException("waveform array must not be empty")
    else:
        raise InvalidAudioChunkException("waveform must be base64 string or float array")

    return True
