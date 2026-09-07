import httpx
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.analysis import MLPrediction
from app.schemas.audio import DSPAudioChunk

logger = get_logger(__name__)


class MLClient:
    """HTTP client for the real M1 inference service.

    Mock inference is available only when MOCK_ML_SERVICE=True. In normal integration
    mode an unavailable ML service is treated as an error instead of silently
    generating a fake prediction.
    """

    def __init__(self, service_url: Optional[str] = None, timeout: Optional[float] = None):
        self.service_url = service_url or settings.ML_SERVICE_URL
        self.timeout = timeout or settings.ML_REQUEST_TIMEOUT_SECONDS
        self.force_mock = settings.MOCK_ML_SERVICE

    async def predict(self, chunk: DSPAudioChunk) -> MLPrediction:
        if self.force_mock:
            return self._generate_mock_prediction(chunk)

        if not self.service_url:
            raise RuntimeError("ML_SERVICE_URL is not configured")

        payload = {
            "chunk_id": chunk.chunk_id,
            "sample_rate": chunk.sample_rate,
            "quality": chunk.quality,
            "timestamp": chunk.timestamp,
            "waveform": chunk.waveform,
            "language": "English",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.service_url, json=payload)
        except httpx.HTTPError as exc:
            logger.error("ML service request failed: %s", exc)
            raise RuntimeError(f"ML service unreachable at {self.service_url}: {exc}") from exc

        if response.status_code != 200:
            body = response.text[:1000]
            raise RuntimeError(
                f"ML service returned HTTP {response.status_code}: {body}"
            )

        data = response.json()
        try:
            synthetic_probability = float(data["synthetic_probability"])
            confidence = float(data["confidence"])
            model_version = str(data["model_version"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid ML response contract: {data}") from exc

        if not 0.0 <= synthetic_probability <= 1.0:
            raise RuntimeError("ML synthetic_probability must be within [0, 1]")
        if not 0.0 <= confidence <= 1.0:
            raise RuntimeError("ML confidence must be within [0, 1]")
        if not model_version:
            raise RuntimeError("ML model_version is empty")

        return MLPrediction(
            synthetic_probability=synthetic_probability,
            confidence=confidence,
            model_version=model_version,
        )

    def _generate_mock_prediction(self, chunk: DSPAudioChunk) -> MLPrediction:
        chunk_id_lower = chunk.chunk_id.lower()
        if any(key in chunk_id_lower for key in ("spoof", "synthetic", "fake")):
            return MLPrediction(
                synthetic_probability=0.91,
                confidence=0.87,
                model_version="mock-v1",
            )
        return MLPrediction(
            synthetic_probability=0.08,
            confidence=0.92,
            model_version="mock-v1",
        )
