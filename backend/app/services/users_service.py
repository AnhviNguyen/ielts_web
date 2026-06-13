from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models import User
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas import ChangePasswordRequest, UserAISettingsResponse, UserAISettingsUpdateRequest, UserMeResponse, UserMeUpdateRequest


class UsersService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._profile_repo = ProfileRepository(db)
        self._user_repo = UserRepository(db)

    async def get_me(self, user: User) -> UserMeResponse:
        profile = await self._profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return UserMeResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            locked_at=user.locked_at,
            lock_reason=user.lock_reason,
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
            placement_status=profile.placement_status,
            initial_band_source=profile.initial_band_source,
            initial_reading_band=profile.initial_reading_band,
            initial_listening_band=profile.initial_listening_band,
            initial_writing_band=profile.initial_writing_band,
            initial_speaking_band=profile.initial_speaking_band,
            initial_overall_band=profile.initial_overall_band,
            placement_completed_at=profile.placement_completed_at,
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

    async def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if payload.current_password == payload.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu mới phải khác mật khẩu hiện tại.",
            )
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không đúng.",
            )
        try:
            new_hash = hash_password(payload.new_password)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu mới không hợp lệ.",
            ) from exc
        await self._user_repo.update_password_hash(user, new_hash)

    async def get_ai_settings(self, user: User) -> UserAISettingsResponse:
        from app.core.user_ai_secrets import decrypt_api_key, mask_api_key

        profile = await self._profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        provider = (profile.ai_provider or "system").strip().lower()
        if provider in ("gemini", "openai", "grok"):
            return UserAISettingsResponse(provider="openrouter", has_key=False, api_key_masked=None)
        if provider not in ("system", "openrouter"):
            provider = "system"
        has_key = bool(profile.ai_api_key_encrypted) and provider == "openrouter"
        masked = None
        if has_key:
            try:
                masked = mask_api_key(decrypt_api_key(profile.ai_api_key_encrypted))
            except ValueError:
                has_key = False
        return UserAISettingsResponse(provider=provider, has_key=has_key, api_key_masked=masked)

    async def update_ai_settings(self, user: User, payload: UserAISettingsUpdateRequest) -> UserAISettingsResponse:
        from app.core.user_ai_client import VALID_PROVIDERS

        profile = await self._profile_repo.get_by_user_id(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

        provider = payload.provider.strip().lower()
        if provider not in VALID_PROVIDERS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nhà cung cấp AI không hợp lệ.")

        if provider == "system":
            await self._profile_repo.update_ai_settings(profile, provider="system", clear_key=True)
        elif provider == "openrouter":
            if payload.api_key is not None:
                key = payload.api_key.strip()
                if not key:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Vui lòng nhập OpenRouter API key.",
                    )
                if not key.startswith("sk-or"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="OpenRouter API key thường bắt đầu bằng sk-or-…",
                    )
                if len(key) < 12:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key quá ngắn.")
                await self._profile_repo.update_ai_settings(profile, provider="openrouter", api_key=key)
            elif profile.ai_api_key_encrypted and profile.ai_provider == "openrouter":
                pass
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Vui lòng nhập OpenRouter API key.",
                )

        await self._db.commit()
        return await self.get_ai_settings(user)
