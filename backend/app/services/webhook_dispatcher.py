import httpx
from typing import Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)

class WebhookDispatcher:
    """Dispatches webhooks to external SIEM/SOC systems."""

    @classmethod
    async def dispatch(cls, payload: Dict[str, Any], url: str = "http://localhost:8000/mock/webhook") -> None:
        """Sends an asynchronous webhook payload."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                logger.info(f"Dispatching webhook to {url}")
                # We don't await response validation strictly as this is fire-and-forget
                response = await client.post(url, json=payload)
                if response.status_code >= 400:
                    logger.warning(f"Webhook dispatch to {url} failed with status {response.status_code}")
                else:
                    logger.info(f"Webhook dispatch successful: {response.status_code}")
        except Exception as exc:
            logger.error(f"Failed to dispatch webhook: {exc}")
