"""Bind Celery task IDs to user IDs (Redis) so poll endpoints cannot leak results."""

from __future__ import annotations

from app.core.cache import cache
from app.core.config import settings

_OWNER_PREFIX = "celery_task_owner:"
_DEFAULT_TTL = 3600


def register_task_owner(task_id: str, user_id: int, ttl: int = _DEFAULT_TTL) -> None:
    cache.set(f"{_OWNER_PREFIX}{task_id}", user_id, ttl=ttl)


def verify_task_owner(task_id: str, user_id: int) -> bool:
    owner = cache.get(f"{_OWNER_PREFIX}{task_id}")
    if owner is None:
        # Redis down or expired — deny in production; allow in dev for local Celery without Redis
        return settings.ENVIRONMENT != "production"
    try:
        return int(owner) == int(user_id)
    except (TypeError, ValueError):
        return False
