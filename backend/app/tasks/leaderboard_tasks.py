"""Celery task: rebuild all-time leaderboard ZSET from PostgreSQL."""

from __future__ import annotations

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.leaderboard_redis import rebuild_from_db
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="leaderboard.rebuild_zset")
def rebuild_leaderboard_zset_task() -> int:
    """Sync Redis ZSET from user_profiles.xp (cron / manual)."""

    async def _run() -> int:
        async with AsyncSessionLocal() as db:
            return await rebuild_from_db(db)

    try:
        count = asyncio.run(_run())
        logger.info("leaderboard.rebuild_zset completed: %d users", count)
        return count
    except Exception as exc:
        logger.exception("leaderboard.rebuild_zset failed: %s", exc)
        raise
