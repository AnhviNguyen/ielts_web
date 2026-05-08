"""
app/repositories/profile_repository.py — LinguaIELTS
Thêm update cho target_band, exam_date.
"""

from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import UserProfile


class ProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_user_id(self, user_id: int) -> UserProfile | None:
        result = await self._db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_empty(self, user_id: int, full_name: str | None = None) -> UserProfile:
        profile = UserProfile(user_id=user_id, full_name=full_name)
        self._db.add(profile)
        await self._db.flush()
        await self._db.refresh(profile)
        return profile

    async def update(
        self,
        profile: UserProfile,
        full_name:   str | None,
        phone:       str | None,
        bio:         str | None,
        avatar_url:  str | None,
        target_band: float | None = None,
        exam_date:   date | None = None,
    ) -> UserProfile:
        if full_name   is not None: profile.full_name   = full_name
        if phone       is not None: profile.phone       = phone
        if bio         is not None: profile.bio         = bio
        if avatar_url  is not None: profile.avatar_url  = avatar_url
        if target_band is not None: profile.target_band = target_band
        if exam_date   is not None: profile.exam_date   = exam_date
        self._db.add(profile)
        await self._db.flush()
        await self._db.refresh(profile)
        return profile

    async def add_xp(self, user_id: int, xp_amount: int) -> None:
        """Cộng XP và cập nhật streak."""
        profile = await self.get_by_user_id(user_id)
        if profile:
            profile.xp = (profile.xp or 0) + xp_amount
            self._db.add(profile)
            await self._db.flush()
