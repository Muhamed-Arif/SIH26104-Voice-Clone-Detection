import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status
from app.core.config import settings

# In-memory sliding window request tracker: ip -> list of timestamps
_request_records: Dict[str, List[float]] = defaultdict(list)


async def check_rate_limit(request: Request) -> None:
    """In-memory sliding window rate limiter.
    
    # TODO(M5): Replace in-memory sliding window with distributed Redis token bucket.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    window_seconds = 60.0
    max_requests = settings.RATE_LIMIT_PER_MINUTE

    # Prune expired timestamps
    records = _request_records[client_ip]
    _request_records[client_ip] = [ts for ts in records if now - ts < window_seconds]

    if len(_request_records[client_ip]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {max_requests} requests per minute.",
        )

    _request_records[client_ip].append(now)
