import base64
import numpy as np


def generate_synthetic_audio_payload(chunk_id: str = "chunk-synthetic-001") -> dict:
    """Generates a mock base64 audio chunk payload mimicking DSP output."""
    # Synthetic sine wave (16kHz, 100ms)
    t = np.linspace(0, 0.1, 1600, endpoint=False)
    sig = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    b64_str = base64.b64encode(sig.tobytes()).decode("utf-8")

    return {
        "waveform": b64_str,
        "sample_rate": 16000,
        "chunk_id": chunk_id,
        "quality": "HIGH",
        "timestamp": "2026-09-05T22:00:00Z",
    }


def generate_genuine_audio_payload(chunk_id: str = "chunk-genuine-001") -> dict:
    """Generates a mock genuine voice chunk payload."""
    t = np.linspace(0, 0.1, 1600, endpoint=False)
    sig = (np.sin(2 * np.pi * 220 * t) * 32767).astype(np.int16)
    b64_str = base64.b64encode(sig.tobytes()).decode("utf-8")

    return {
        "waveform": b64_str,
        "sample_rate": 16000,
        "chunk_id": chunk_id,
        "quality": "HIGH",
        "timestamp": "2026-09-05T22:00:00Z",
    }
