"""
Redis sorted-set leaderboard for all-time XP (O(log N) top-N and rank).
Falls back to PostgreSQL when Redis is unavailable or ZSET is empty.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.db.models import UserProfile

logger = logging.getLogger(__name__)

XP_ZSET_KEY = "leaderboard:xp:all"


def sync_user_xp(user_id: int, xp: int) -> None:
    """Upsert user XP into the all-time ZSET."""
    try:
        cache.zadd(XP_ZSET_KEY, {str(user_id): float(xp)})
    except Exception as exc:
        logger.debug("leaderboard ZSET sync skipped user=%s: %s", user_id, exc)


def get_top(top_n: int) -> list[tuple[int, int]]:
    """Return [(user_id, xp), ...] highest XP first."""
    rows = cache.zrevrange_with_scores(XP_ZSET_KEY, 0, max(top_n - 1, 0))
    return [(int(uid), int(score)) for uid, score in rows]


def get_rank(user_id: int) -> int | None:
    """1-based rank, or None if user not in ZSET."""
    rank = cache.zrevrank(XP_ZSET_KEY, str(user_id))
    return int(rank) + 1 if rank is not None else None


def zset_size() -> int:
    return cache.zcard(XP_ZSET_KEY)


def is_ready() -> bool:
    return cache.ping() and zset_size() > 0


async def rebuild_from_db(db: AsyncSession) -> int:
    """Full rebuild from user_profiles.xp — used on startup/cron when ZSET empty."""
    if not cache.ping():
        return 0

    result = await db.execute(
        select(UserProfile.user_id, UserProfile.xp).where(UserProfile.xp.isnot(None))
    )
    rows = result.all()
    mapping = {str(uid): float(xp or 0) for uid, xp in rows}
    if mapping:
        cache.zadd_replace(XP_ZSET_KEY, mapping)
    else:
        cache.delete(XP_ZSET_KEY)
    logger.info("Leaderboard ZSET rebuilt: %d users", len(mapping))
    return len(mapping)
