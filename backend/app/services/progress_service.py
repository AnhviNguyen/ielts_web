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
from app.schemas import ProgressResponse

logger = logging.getLogger(__name__)


class ProgressService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ProgressRepository(db)

    async def get_progress(self, user: User) -> list[ProgressResponse]:
        """Return all progress records for the authenticated user."""
        records = await self._repo.get_all_for_user(user.id)
        return [ProgressResponse.model_validate(r) for r in records]
