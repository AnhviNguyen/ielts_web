"""
app/repositories/history_repository.py
────────────────────────────────────────
Database operations for the History model.
Supports creating entries and paginated retrieval.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History, HistoryArchive


class HistoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        user_id: int,
        quiz_id: str | None,
        subject: str | None,
        score: int | None,
        total_questions: int | None,
        percentage: float | None,
        answers: Any | None,
        band_score: float | None = None,
        mode: str | None = None,
        duration_seconds: int | None = None,
        practice_session_id: int | None = None,
    ) -> History:
        """Persist a new practice attempt record."""
        entry = History(
            user_id=user_id,
            quiz_id=quiz_id,
            practice_session_id=practice_session_id,
            subject=subject,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            band_score=band_score,
            mode=mode,
            duration_seconds=duration_seconds,
            answers=answers,
        )
        self._db.add(entry)
        await self._db.flush()
        await self._db.refresh(entry)
        return entry

    def _user_filter(self, user_id: int, subject: str | None = None):
        stmt = select(History).where(History.user_id == user_id)
        if subject and subject.lower() not in ("all", ""):
            # DB stores "Reading", "Listening", … — match case-insensitively
            stmt = stmt.where(func.lower(History.subject) == subject.lower())
        return stmt

    async def get_paginated(
        self,
        user_id: int,
        page: int,
        page_size: int,
        subject: str | None = None,
    ) -> tuple[list[History], int]:
        """
        Return a page of history records and the total count (newest first).

        Returns:
            Tuple of (items, total_count).
        """
        offset = (page - 1) * page_size

        count_base = select(func.count()).select_from(History).where(History.user_id == user_id)
        if subject and subject.lower() not in ("all", ""):
            count_base = count_base.where(func.lower(History.subject) == subject.lower())
        count_result = await self._db.execute(count_base)
        total = count_result.scalar_one()

        data_result = await self._db.execute(
            self._user_filter(user_id, subject)
            .order_by(History.completed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(data_result.scalars().all())

        return items, total

    async def get_completed_quiz_ids(
        self,
        user_id: int,
        subject: str | None = None,
    ) -> list[str]:
        """Distinct quiz_id values the user has attempted (for hub completion badges)."""
        stmt = (
            select(History.quiz_id)
            .where(History.user_id == user_id, History.quiz_id.isnot(None))
            .distinct()
        )
        if subject and subject.lower() not in ("all", ""):
            stmt = stmt.where(func.lower(History.subject) == subject.lower())
        result = await self._db.execute(stmt)
        return [str(row[0]) for row in result.all() if row[0]]

    async def get_by_id_for_user(self, history_id: int, user_id: int) -> History | None:
        result = await self._db.execute(
            select(History).where(History.id == history_id, History.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def archive_completed_before(self, cutoff: datetime, *, batch_size: int = 500) -> int:
        """
        Move history rows older than cutoff into history_archive (batched).
        Returns number of rows archived in this run.
        """
        result = await self._db.execute(
            select(History)
            .where(History.completed_at < cutoff)
            .order_by(History.completed_at.asc())
            .limit(batch_size)
        )
        rows = list(result.scalars().all())
        if not rows:
            return 0

        for row in rows:
            self._db.add(
                HistoryArchive(
                    id=row.id,
                    user_id=row.user_id,
                    quiz_id=row.quiz_id,
                    practice_session_id=row.practice_session_id,
                    subject=row.subject,
                    score=row.score,
                    total_questions=row.total_questions,
                    percentage=row.percentage,
                    band_score=row.band_score,
                    mode=row.mode,
                    duration_seconds=row.duration_seconds,
                    answers=row.answers,
                    completed_at=row.completed_at,
                )
            )
            await self._db.delete(row)

        await self._db.flush()
        return len(rows)
