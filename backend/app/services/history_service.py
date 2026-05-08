"""
app/services/history_service.py
─────────────────────────────────
Business logic for saving practice results and updating progress.
Orchestrates HistoryRepository + ProgressRepository in a single transaction.
"""

import logging
import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.history_repository import HistoryRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas import HistoryResponse, HistorySave, PaginatedHistory

logger = logging.getLogger(__name__)


class HistoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._history_repo = HistoryRepository(db)
        self._progress_repo = ProgressRepository(db)

    async def save_practice_result(self, user: User, payload: HistorySave) -> HistoryResponse:
        """
        Persist a practice attempt and atomically update the subject progress:
        1. Insert history record
        2. Fetch existing progress (if any) for this subject
        3. Increment completed_questions by attempt score (capped at total)
        4. Upsert progress with recalculated percentage
        """
        # 1. Save history entry
        entry = await self._history_repo.create(
            user_id=user.id,
            quiz_id=payload.quiz_id,
            subject=payload.subject,
            score=payload.score,
            total_questions=payload.total_questions,
            percentage=payload.percentage,
            answers=payload.answers,
        )

        # 2. Update subject progress
        existing = await self._progress_repo.get_by_subject(user.id, payload.subject)

        if existing:
            new_total = max(existing.total_questions, payload.total_questions)
            new_completed = min(existing.completed_questions + payload.score, new_total)
        else:
            new_total = payload.total_questions
            new_completed = payload.score

        new_pct = round((new_completed / max(new_total, 1)) * 100, 2)
        new_pct = min(new_pct, 100.0)

        await self._progress_repo.upsert(
            user_id=user.id,
            subject=payload.subject,
            total_questions=new_total,
            completed_questions=new_completed,
            percentage=new_pct,
        )

        logger.info(
            "Practice attempt saved: user_id=%s subject=%s score=%s/%s pct=%.1f%%",
            user.id,
            payload.subject,
            payload.score,
            payload.total_questions,
            payload.percentage,
        )

        return HistoryResponse.model_validate(entry)

    async def get_history(
        self, user: User, page: int, page_size: int
    ) -> PaginatedHistory:
        """Return a paginated list of the user's practice attempts."""
        items, total = await self._history_repo.get_paginated(user.id, page, page_size)
        total_pages = math.ceil(total / page_size) if total else 1

        return PaginatedHistory(
            items=[HistoryResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
