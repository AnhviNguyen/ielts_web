"""
app/services/profile_service.py — LinguaIELTS
Thêm get_user_stats để trả về streak, XP, band scores cho topbar.
"""

import logging
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas import ProfileResponse, ProfileUpdate, UserStatsResponse

logger = logging.getLogger(__name__)

# IELTS skills
IELTS_SKILLS = ["Reading", "Listening", "Writing", "Speaking", "Vocabulary"]


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self._profile_repo  = ProfileRepository(db)
        self._progress_repo = ProgressRepository(db)

    async def get_profile(self, user: User) -> ProfileResponse:
        profile = await self._profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return self._to_response(profile, user)

    async def update_profile(self, user: User, payload: ProfileUpdate) -> ProfileResponse:
        profile = await self._profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        updated = await self._profile_repo.update(
            profile=profile,
            full_name=payload.full_name,
            phone=payload.phone,
            bio=payload.bio,
            avatar_url=payload.avatar_url,
            target_band=payload.target_band,
            exam_date=payload.exam_date,
        )
        logger.info("Profile updated for user_id=%s", user.id)
        return self._to_response(updated, user)

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

    @staticmethod
    def _to_response(profile, user: User) -> ProfileResponse:
        return ProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            full_name=profile.full_name,
            avatar_url=profile.avatar_url,
            phone=profile.phone,
            bio=profile.bio,
            target_band=profile.target_band,
            exam_date=profile.exam_date,
            streak=profile.streak,
            xp=profile.xp,
            updated_at=profile.updated_at,
            email=user.email,
            created_at=user.created_at,
        )
