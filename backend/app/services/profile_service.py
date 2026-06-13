"""
app/services/profile_service.py — LinguaIELTS
Thêm get_user_stats để trả về streak, XP, band scores cho topbar.
"""

import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas import UserStatsResponse

logger = logging.getLogger(__name__)

# IELTS skills
IELTS_SKILLS = ["Reading", "Listening", "Writing", "Speaking", "Vocabulary"]


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self._profile_repo  = ProfileRepository(db)
        self._progress_repo = ProgressRepository(db)

    async def get_user_stats(self, user: User) -> UserStatsResponse:
        """Trả về streak, XP, band scores per skill và ngày còn đến thi."""
        profile  = await self._profile_repo.get_by_user_id(user.id)
        progress = await self._progress_repo.get_all_for_user(user.id)

        band_map: dict[str, float | None] = {s: None for s in IELTS_SKILLS}
        for p in progress:
            if p.subject in band_map:
                band_map[p.subject] = p.band_score

        days_to_exam: int | None = None
        if profile and profile.exam_date:
            delta = (profile.exam_date - date.today()).days
            days_to_exam = max(delta, 0)

        return UserStatsResponse(
            streak=profile.streak if profile else 0,
            xp=profile.xp if profile else 0,
            band_scores=band_map,
            days_to_exam=days_to_exam,
        )
