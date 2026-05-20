"""
app/repositories/profile_repository.py — LinguaIELTS
Thêm update cho target_band, exam_date, streak và XP.
"""

from datetime import date, timedelta
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

    async def update_streak_and_xp(self, user_id: int, xp_to_add: int = 0) -> UserProfile | None:
        """
        Cập nhật streak dựa trên last_activity_date và cộng XP.

        Rules:
        - last_activity = null  → streak = 1, last_activity = today
        - last_activity = today → không thay đổi streak (tránh double-count)
        - last_activity = yesterday → streak += 1
        - last_activity < yesterday → reset streak = 1 (streak bị gián đoạn)
        """
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return None

        today = date.today()

        if profile.last_activity_date is None:
            profile.streak = 1
        elif profile.last_activity_date == today:
            # Đã active hôm nay → chỉ cộng XP, không thay đổi streak
            pass
        elif profile.last_activity_date == today - timedelta(days=1):
            # Active ngày hôm qua → tăng streak
            profile.streak = (profile.streak or 0) + 1
        else:
            # Bỏ ngày → reset streak về 1
            profile.streak = 1

        # Cập nhật longest streak
        if (profile.streak or 0) > (profile.longest_streak or 0):
            profile.longest_streak = profile.streak

        profile.last_activity_date = today

        # Cộng XP
        if xp_to_add > 0:
            profile.xp = (profile.xp or 0) + xp_to_add

        self._db.add(profile)
        await self._db.flush()
        await self._db.refresh(profile)
        return profile

    async def add_xp(self, user_id: int, xp_amount: int) -> None:
        """Cộng XP (legacy method, dùng update_streak_and_xp thay thế)."""
        await self.update_streak_and_xp(user_id, xp_to_add=xp_amount)
