"""
app/repositories/history_repository.py
────────────────────────────────────────
Database operations for the History model.
Supports creating entries and paginated retrieval.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History


class HistoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        user_id: int,
        quiz_id: str,
        subject: str,
        score: int,
        total_questions: int,
        percentage: float,
        answers: Any | None,
    ) -> History:
        """Persist a new practice attempt record."""
        entry = History(
            user_id=user_id,
            quiz_id=quiz_id,
            subject=subject,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            answers=answers,
        )
        self._db.add(entry)
        await self._db.flush()
        await self._db.refresh(entry)
        return entry

    async def get_paginated(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[History], int]:
        """
        Return a page of history records and the total count.

        Returns:
            Tuple of (items, total_count).
        """
        offset = (page - 1) * page_size

        # Total count query
        count_result = await self._db.execute(
            select(func.count()).where(History.user_id == user_id)
        )
        total = count_result.scalar_one()

        # Paginated data query (newest first)
        data_result = await self._db.execute(
            select(History)
            .where(History.user_id == user_id)
            .order_by(History.completed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(data_result.scalars().all())

        return items, total
