"""Celery tasks for shadowing video processing."""

from __future__ import annotations

import asyncio

from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="shadowing.process")
def process_video_task(
    self,
    url: str,
    level: str | None = None,
    translate: bool = False,
    user_id: int | None = None,
):
    try:
        return asyncio.run(_run_async(url, level, translate, user_id))
    except Exception as exc:
        self.retry(exc=exc, countdown=10, max_retries=1)


async def _run_async(
    url: str,
    level: str | None,
    translate: bool,
    user_id: int | None,
) -> dict:
    from app.db.database import AsyncSessionLocal
    from app.repositories.shadowing_repository import ShadowingRepository
    from app.services.shadowing_service import ShadowingService

    async with AsyncSessionLocal() as db:
        try:
            svc = ShadowingService(ShadowingRepository(db))
            data = await svc.process_url(
                url,
                level=level or "Intermediate",
                translate=translate,
                user_id=user_id,
            )
            await db.commit()
            return data
        except Exception:
            await db.rollback()
            raise
