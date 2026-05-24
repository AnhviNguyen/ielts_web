"""Ephemeral daily counters (Redis) when not stored on UserProfile."""

from datetime import date

from fastapi import HTTPException, status

from app.core.cache import cache
from app.core.limits import DAILY_WRITING_CHAT_MAX


def _writing_chat_key(user_id: int) -> str:
    return f"usage:writing_chat:{user_id}:{date.today().isoformat()}"


def check_and_increment_writing_chat(user_id: int) -> None:
    key = _writing_chat_key(user_id)
    current = cache.get(key) or 0
    try:
        current = int(current)
    except (TypeError, ValueError):
        current = 0
    if current >= DAILY_WRITING_CHAT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Đã đạt giới hạn {DAILY_WRITING_CHAT_MAX} tin nhắn Writing coach/ngày.",
        )
    cache.set(key, current + 1, ttl=86_400)
