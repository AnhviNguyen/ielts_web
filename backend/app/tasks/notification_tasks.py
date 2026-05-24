"""Celery tasks for daily study reminders."""

from __future__ import annotations

import asyncio
import logging

from app.core.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.services.notification_service import send_daily_reminders_for_all

logger = logging.getLogger(__name__)


@celery_app.task(name="notifications.daily_reminders")
def daily_reminders() -> int:
    async def _run() -> int:
        async with AsyncSessionLocal() as db:
            count = await send_daily_reminders_for_all(db)
            await db.commit()
            return count

    try:
        count = asyncio.run(_run())
        logger.info("Daily reminders sent: %s", count)
        return count
    except Exception as exc:
        logger.exception("daily_reminders failed: %s", exc)
        raise
