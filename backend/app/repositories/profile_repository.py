"""
app/repositories/profile_repository.py — LinguaIELTS
Thêm update cho target_band, exam_date, streak và XP.
"""

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limits import (
    DAILY_SPEAKING_EVAL_MAX,
    DAILY_WRITING_SUBMIT_MAX,
    MONTHLY_TUTOR_QUESTIONS_MAX,
)
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

        streak_before = profile.streak or 0
        xp_before = profile.xp or 0
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

        if (profile.streak or 0) != streak_before or (profile.xp or 0) != xp_before:
            from app.core.cache import invalidate_leaderboard_cache
            from app.core.leaderboard_redis import sync_user_xp

            sync_user_xp(user_id, profile.xp or 0)
            invalidate_leaderboard_cache()

        return profile

    async def add_xp(self, user_id: int, xp_amount: int) -> None:
        """Cộng XP (legacy method, dùng update_streak_and_xp thay thế)."""
        await self.update_streak_and_xp(user_id, xp_to_add=xp_amount)

    async def _get_or_create(self, user_id: int) -> UserProfile:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            profile = await self.create_empty(user_id)
        return profile

    def _reset_counters_if_period_changed(self, profile: UserProfile) -> None:
        today = date.today()
        last = profile.last_activity_date
        if last is None or last != today:
            profile.daily_writing_used = 0
            profile.daily_speaking_used = 0
        if last is None or last.month != today.month or last.year != today.year:
            profile.tutor_questions_used_month = 0

    async def ensure_writing_submit_allowed(self, user_id: int) -> UserProfile:
        profile = await self._get_or_create(user_id)
        self._reset_counters_if_period_changed(profile)
        if (profile.daily_writing_used or 0) >= DAILY_WRITING_SUBMIT_MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Đã đạt giới hạn {DAILY_WRITING_SUBMIT_MAX} bài Writing/n ngày. Thử lại vào ngày mai.",
            )
        return profile

    async def increment_writing_submit(self, user_id: int) -> None:
        profile = await self.ensure_writing_submit_allowed(user_id)
        profile.daily_writing_used = (profile.daily_writing_used or 0) + 1
        self._db.add(profile)
        await self._db.flush()

    async def ensure_speaking_eval_allowed(self, user_id: int) -> UserProfile:
        profile = await self._get_or_create(user_id)
        self._reset_counters_if_period_changed(profile)
        if (profile.daily_speaking_used or 0) >= DAILY_SPEAKING_EVAL_MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Đã đạt giới hạn {DAILY_SPEAKING_EVAL_MAX} lần đánh giá Speaking/ngày.",
            )
        return profile

    async def increment_speaking_eval(self, user_id: int) -> None:
        profile = await self.ensure_speaking_eval_allowed(user_id)
        profile.daily_speaking_used = (profile.daily_speaking_used or 0) + 1
        self._db.add(profile)
        await self._db.flush()

    async def ensure_tutor_chat_allowed(self, user_id: int) -> UserProfile:
        profile = await self._get_or_create(user_id)
        self._reset_counters_if_period_changed(profile)
        if (profile.tutor_questions_used_month or 0) >= MONTHLY_TUTOR_QUESTIONS_MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Đã đạt giới hạn {MONTHLY_TUTOR_QUESTIONS_MAX} câu hỏi AI/tháng.",
            )
        return profile

    async def increment_tutor_chat(self, user_id: int) -> None:
        profile = await self.ensure_tutor_chat_allowed(user_id)
        profile.tutor_questions_used_month = (profile.tutor_questions_used_month or 0) + 1
        self._db.add(profile)
        await self._db.flush()
