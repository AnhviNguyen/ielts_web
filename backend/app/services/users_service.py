from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.profile_repository import ProfileRepository
from app.schemas import UserMeResponse, UserMeUpdateRequest


class UsersService:
    def __init__(self, db: AsyncSession) -> None:
        self._profile_repo = ProfileRepository(db)

    async def get_me(self, user: User) -> UserMeResponse:
        profile = await self._profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return UserMeResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            full_name=profile.full_name,
            avatar_url=profile.avatar_url,
            phone=profile.phone,
            bio=profile.bio,
            target_band=profile.target_band,
            exam_date=profile.exam_date,
            streak=profile.streak,
            longest_streak=profile.longest_streak,
            streak_freeze_count=profile.streak_freeze_count,
            last_activity_date=profile.last_activity_date,
            xp=profile.xp,
            daily_writing_used=profile.daily_writing_used,
            daily_speaking_used=profile.daily_speaking_used,
            tutor_questions_used_month=profile.tutor_questions_used_month,
        )

    async def update_me(self, user: User, payload: UserMeUpdateRequest) -> UserMeResponse:
        profile = await self._profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        await self._profile_repo.update(
            profile=profile,
            full_name=payload.full_name,
            phone=payload.phone,
            bio=payload.bio,
            avatar_url=None,
            target_band=payload.target_band,
            exam_date=payload.exam_date,
        )
        return await self.get_me(user)
