import httpx
import random
from typing import Any, Dict, Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.analysis import MLPrediction
from app.schemas.audio import DSPAudioChunk

logger = get_logger(__name__)


class MLClient:
    """Client for external ML inference service (Member 1) with local mock fallback."""

    def __init__(self, service_url: Optional[str] = None, timeout: Optional[float] = None):
        self.service_url = service_url or settings.ML_SERVICE_URL
        self.timeout = timeout or settings.ML_REQUEST_TIMEOUT_SECONDS
        self.force_mock = settings.MOCK_ML_SERVICE

    async def predict(self, chunk: DSPAudioChunk) -> MLPrediction:
        """Invokes the remote ML service or falls back to local mock prediction."""
        if not self.force_mock and self.service_url:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.service_url,
                        json={
                            "chunk_id": chunk.chunk_id,
                            "sample_rate": chunk.sample_rate,
                            "quality": chunk.quality,
                            "timestamp": chunk.timestamp,
                            "waveform": chunk.waveform,
                        },
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return MLPrediction(
                            synthetic_probability=float(data.get("synthetic_probability", 0.5)),
                            confidence=float(data.get("confidence", 0.8)),
                            model_version=str(data.get("model_version", "v0.3")),
                        )
                    else:
                        logger.warning(
                            f"ML service returned non-200 status {response.status_code}. Falling back to mock."
                        )
            except Exception as exc:
                logger.warning(
                    f"ML service unreachable at {self.service_url} ({exc}). Using mock fallback."
                )

        return self._generate_mock_prediction(chunk)

    def _generate_mock_prediction(self, chunk: DSPAudioChunk) -> MLPrediction:
        """Generates deterministic/heuristic mock predictions for testing."""
        chunk_id_lower = chunk.chunk_id.lower()
        quality_lower = chunk.quality.lower()

        # Heuristic determination based on chunk ID or quality hints for testing
        if "spoof" in chunk_id_lower or "synthetic" in chunk_id_lower or "fake" in chunk_id_lower:
            return MLPrediction(
                synthetic_probability=0.91,
                confidence=0.87,
                model_version="v0.3",
            )
        elif "clean" in chunk_id_lower or "genuine" in chunk_id_lower or "human" in chunk_id_lower:
            return MLPrediction(
                synthetic_probability=0.08,
                confidence=0.92,
                model_version="v0.3",
            )
        elif "ambiguous" in chunk_id_lower or "medium" in chunk_id_lower:
            return MLPrediction(
                synthetic_probability=0.52,
                confidence=0.74,
                model_version="v0.3",
            )
        elif "degraded" in quality_lower:
            return MLPrediction(
                synthetic_probability=0.65,
                confidence=0.55,
                model_version="v0.3",
            )
        else:
            # Default contract benchmark prediction
            return MLPrediction(
                synthetic_probability=0.91,
                confidence=0.87,
                model_version="v0.3",
            )
