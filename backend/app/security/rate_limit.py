import time
from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.core.cache import cache

async def check_rate_limit(request: Request) -> None:
    """Rate limiter using simulated Redis cache."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # We use a simple counter with expiration for the rate limit window
    window_seconds = 60
    max_requests = settings.RATE_LIMIT_PER_MINUTE
    cache_key = f"rate_limit:{client_ip}"
    
    current_count = await cache.get(cache_key)
    
    if current_count is None:
        await cache.set(cache_key, 1, expire=window_seconds)
    else:
        if current_count >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {max_requests} requests per minute.",
            )
        await cache.incr(cache_key)
