"""Redis cache with graceful fallback when Redis is unavailable."""

import json
from typing import Any, Optional

import redis as redis_lib

from app.core.config import settings


class CacheClient:
    """Redis wrapper. Fails fast when Redis is down (no multi-second hangs per call)."""

    def __init__(self) -> None:
        self._client: redis_lib.Redis | None = None
        self._disabled = False

    def _get(self) -> redis_lib.Redis:
        if self._disabled:
            raise ConnectionError("redis unavailable")
        if self._client is None:
            self._client = redis_lib.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.4,
                socket_timeout=0.4,
            )
        return self._client

    def _mark_disabled(self) -> None:
        self._disabled = True
        self._client = None

    def get(self, key: str) -> Optional[Any]:
        if self._disabled:
            return None
        try:
            value = self._get().get(key)
            return json.loads(value) if value else None
        except Exception:
            self._mark_disabled()
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if self._disabled:
            return
        try:
            self._get().setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            self._mark_disabled()

    def delete(self, key: str) -> None:
        try:
            self._get().delete(key)
        except Exception:
            pass

    def zadd(self, key: str, mapping: dict[str, float]) -> None:
        try:
            self._get().zadd(key, mapping)
        except Exception:
            pass

    def zadd_replace(self, key: str, mapping: dict[str, float]) -> None:
        """Replace entire sorted set (atomic pipeline)."""
        try:
            client = self._get()
            pipe = client.pipeline()
            pipe.delete(key)
            if mapping:
                pipe.zadd(key, mapping)
            pipe.execute()
        except Exception:
            pass

    def zrevrange_with_scores(self, key: str, start: int, end: int) -> list[tuple[str, float]]:
        try:
            return self._get().zrevrange(key, start, end, withscores=True)
        except Exception:
            return []

    def zrevrank(self, key: str, member: str) -> int | None:
        try:
            return self._get().zrevrank(key, member)
        except Exception:
            return None

    def zcard(self, key: str) -> int:
        try:
            return int(self._get().zcard(key) or 0)
        except Exception:
            return 0

    def ping(self) -> bool:
        try:
            return bool(self._get().ping())
        except Exception:
            return False


cache = CacheClient()


def invalidate_leaderboard_cache() -> None:
    for top in (10, 50):
        cache.delete(f"leaderboard:top{top}")
