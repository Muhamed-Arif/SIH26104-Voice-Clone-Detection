import time
from typing import Optional, Any, Dict
from app.core.logging import get_logger

logger = get_logger(__name__)

class MockRedisCache:
    """A simulated Redis cache for local development.
    In production, this should be replaced with an async Redis client.
    """
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            entry = self._store[key]
            if entry.get("expires_at") and entry["expires_at"] < time.time():
                del self._store[key]
                return None
            return entry.get("value")
        return None

    async def set(self, key: str, value: Any, expire: int = None) -> None:
        expires_at = time.time() + expire if expire else None
        self._store[key] = {"value": value, "expires_at": expires_at}

    async def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    async def incr(self, key: str) -> int:
        current = await self.get(key)
        if current is None:
            await self.set(key, 1)
            return 1
        new_val = int(current) + 1
        entry = self._store[key]
        entry["value"] = new_val
        self._store[key] = entry
        return new_val

    async def expire(self, key: str, seconds: int) -> None:
        if key in self._store:
            self._store[key]["expires_at"] = time.time() + seconds

# Global cache instance
cache = MockRedisCache()
