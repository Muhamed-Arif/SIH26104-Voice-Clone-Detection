import asyncio
from typing import Dict, Any
from app.services.webhook_dispatcher import WebhookDispatcher
from app.core.logging import get_logger

logger = get_logger(__name__)

async def dispatch_high_risk_webhook(payload: Dict[str, Any]) -> None:
    """Background task to dispatch webhooks without blocking the main request."""
    logger.info(f"Background Task Started: Dispatching high risk webhook for session {payload.get('session_id')}")
    # Simulate network jitter or SIEM processing delay
    await asyncio.sleep(0.5)
    
    # Dispatch
    await WebhookDispatcher.dispatch(payload)
    logger.info("Background Task Completed: Webhook dispatched.")
