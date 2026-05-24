"""Celery tasks: archive old history rows to history_archive."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.repositories.history_repository import HistoryRepository

logger = logging.getLogger(__name__)


@celery_app.task(name="history.archive_old")
def archive_old_history_task() -> int:
    """Move history older than HISTORY_ARCHIVE_AFTER_DAYS into history_archive."""

    async def _run() -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.HISTORY_ARCHIVE_AFTER_DAYS)
        total = 0
        async with AsyncSessionLocal() as db:
            repo = HistoryRepository(db)
            while True:
                moved = await repo.archive_completed_before(cutoff, batch_size=500)
                if moved == 0:
                    break
                total += moved
                await db.commit()
        return total

    try:
        count = asyncio.run(_run())
        logger.info("history.archive_old archived %d rows", count)
        return count
    except Exception as exc:
        logger.exception("history.archive_old failed: %s", exc)
        raise
