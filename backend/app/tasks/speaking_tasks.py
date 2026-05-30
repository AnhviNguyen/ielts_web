"""Celery tasks for speaking evaluation."""

from __future__ import annotations

import asyncio

from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="speaking.evaluate")
def evaluate_speaking_task(self, payload: dict):
    try:
        return asyncio.run(_run_async(payload))
    except Exception as exc:
        self.retry(exc=exc, countdown=5, max_retries=2)


async def _run_async(payload: dict) -> dict:
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.db.models import User
    from app.services.speaking_eval_service import evaluate_speaking_core

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User).where(User.id == payload["user_id"]))
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError("User not found")
            data = await evaluate_speaking_core(
                db=db,
                current_user=user,
                tmp_path=payload["tmp_path"],
                suffix=payload["suffix"],
                question_text=payload.get("question_text") or "",
                session_id=payload.get("session_id"),
                quiz_id=payload.get("quiz_id"),
                question_id=payload.get("question_id"),
                attempt_id=payload.get("attempt_id"),
                answer_duration_seconds=payload.get("answer_duration_seconds"),
                persist_result=bool(payload.get("persist_result")),
            )
            await db.commit()
            return data
        except Exception:
            await db.rollback()
            raise
