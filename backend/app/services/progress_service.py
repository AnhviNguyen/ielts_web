"""
app/services/progress_service.py
──────────────────────────────────
Business logic for learning progress management.
Delegates persistence to ProgressRepository; handles percentage calculation.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.progress_repository import ProgressRepository
from app.schemas import ProgressResponse, ProgressUpdateRequest

logger = logging.getLogger(__name__)


class ProgressService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ProgressRepository(db)

    async def get_progress(self, user: User) -> list[ProgressResponse]:
        """Return all progress records for the authenticated user."""
        records = await self._repo.get_all_for_user(user.id)
        return [ProgressResponse.model_validate(r) for r in records]

    async def update_progress(
        self, user: User, payload: ProgressUpdateRequest
    ) -> ProgressResponse:
        """
        Upsert a progress record:
        - Recalculates percentage = completed / total * 100
        - Clamps between 0 and 100
        """
        total = max(payload.total_questions, 1)  # avoid division by zero
        completed = min(payload.completed_questions, total)
        percentage = round((completed / total) * 100, 2)

        progress = await self._repo.upsert(
            user_id=user.id,
            subject=payload.subject,
            total_questions=total,
            completed_questions=completed,
            percentage=percentage,
        )

        logger.info(
            "Progress updated user_id=%s subject=%s pct=%.1f%%",
            user.id,
            payload.subject,
            percentage,
        )

        return ProgressResponse.model_validate(progress)
