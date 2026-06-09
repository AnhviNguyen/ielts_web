"""
app/repositories/progress_repository.py
─────────────────────────────────────────
Database operations for the Progress model.
Uses INSERT … ON CONFLICT DO UPDATE (upsert) for idempotent progress updates.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Progress


class ProgressRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all_for_user(self, user_id: int) -> list[Progress]:
        """Return every progress record belonging to the user."""
        result = await self._db.execute(
            select(Progress)
            .where(Progress.user_id == user_id)
            .order_by(Progress.subject)
        )
        return list(result.scalars().all())

    async def get_by_subject(self, user_id: int, subject: str) -> Progress | None:
        """Fetch a single progress record for a specific subject."""
        result = await self._db.execute(
            select(Progress).where(
                Progress.user_id == user_id, Progress.subject == subject
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: int,
        subject: str,
        total_questions: int,
        completed_questions: int,
        percentage: float,
        band_score: float | None = None,
    ) -> Progress:
        """Insert or update progress record in a DB-agnostic way."""
        progress = await self.get_by_subject(user_id=user_id, subject=subject)
        if progress is None:
            progress = Progress(
                user_id=user_id,
                subject=subject,
                total_questions=total_questions,
                completed_questions=completed_questions,
                percentage=percentage,
                band_score=band_score,
            )
            self._db.add(progress)
            await self._db.flush()
            await self._db.refresh(progress)
            return progress

        progress.total_questions = total_questions
        progress.completed_questions = completed_questions
        progress.percentage = percentage
        if band_score is not None:
            progress.band_score = band_score
        self._db.add(progress)
        await self._db.flush()
        await self._db.refresh(progress)
        return progress
