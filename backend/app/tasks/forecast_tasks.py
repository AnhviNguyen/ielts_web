"""Celery tasks: score forecast ingest + daily retrain."""

from __future__ import annotations

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.repositories.score_history_repository import ScoreHistoryRepository
from app.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


@celery_app.task(name="forecast.ingest_and_train")
def ingest_and_train_task(user_id: int, skill: str) -> bool:
    """Retrain forecast model for one user/skill after new score data."""

    async def _run() -> bool:
        if not settings.FORECAST_ENABLED:
            return False
        async with AsyncSessionLocal() as db:
            svc = ForecastService(db)
            ok = await svc.train_skill(user_id, skill)
            await db.commit()
            return ok

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("forecast.ingest_and_train failed user=%s skill=%s: %s", user_id, skill, exc)
        raise


@celery_app.task(name="forecast.next_week_scan")
def next_week_scan_task() -> dict:
    """Weekly beat: predict next-week bands and notify learners not improving."""

    async def _run() -> dict:
        if not (settings.FORECAST_ENABLED and settings.NEXT_WEEK_ENABLED):
            return {"scanned": 0, "notified": 0}
        from app.services.next_week_forecast_service import NextWeekForecastService

        scanned = 0
        notified = 0
        async with AsyncSessionLocal() as db:
            repo = ScoreHistoryRepository(db)
            min_days = settings.NEXT_WEEK_MIN_WEEKS * 7
            user_ids = await repo.list_user_ids_with_data(min_days=min_days)
            svc = NextWeekForecastService(db)
            for uid in user_ids:
                try:
                    result = await svc.get_next_week_forecast(uid, notify=True)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("next_week_scan skip user=%s: %s", uid, exc)
                    continue
                scanned += 1
                if not result.cold_start and not result.improving:
                    notified += 1
            await db.commit()
        logger.info("forecast.next_week_scan scanned=%d notified=%d", scanned, notified)
        return {"scanned": scanned, "notified": notified}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("forecast.next_week_scan failed: %s", exc)
        raise


@celery_app.task(name="forecast.retrain_all")
def retrain_all_task() -> dict:
    """Daily beat: retrain all user/skill pairs with enough history."""

    async def _run() -> dict:
        if not settings.FORECAST_ENABLED:
            return {"trained": 0, "skipped": 0}
        trained = 0
        skipped = 0
        async with AsyncSessionLocal() as db:
            repo = ScoreHistoryRepository(db)
            user_ids = await repo.list_user_ids_with_data(min_days=settings.FORECAST_MIN_DAYS)
            svc = ForecastService(db)
            for uid in user_ids:
                skills = await repo.list_skills(uid)
                for skill in skills:
                    if await svc.train_skill(uid, skill):
                        trained += 1
                    else:
                        skipped += 1
            await db.commit()
        logger.info("forecast.retrain_all trained=%d skipped=%d", trained, skipped)
        return {"trained": trained, "skipped": skipped}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("forecast.retrain_all failed: %s", exc)
        raise
