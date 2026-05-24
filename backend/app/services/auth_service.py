"""
app/services/auth_service.py
──────────────────────────────
Business logic for registration and login.
Orchestrates UserRepository + ProfileRepository and issues JWT tokens.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import admin_email_set, settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas import ForgotPasswordRequest, MessageResponse, ResetPasswordRequest, Token, UserCreate, UserLogin
from app.services.email_service import send_password_reset_email, smtp_configured

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._user_repo = UserRepository(db)
        self._profile_repo = ProfileRepository(db)
        self._refresh_repo = RefreshTokenRepository(db)
        self._reset_repo = PasswordResetRepository(db)

    async def register(self, payload: UserCreate) -> Token:
        """
        Register a new user:
        1. Check email is not taken
        2. Hash password
        3. Create user row
        4. Create empty profile (with optional full_name)
        5. Return JWT token so the user is immediately logged in
        """
        existing = await self._user_repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        try:
            hashed = hash_password(payload.password)
        except (ValueError, RuntimeError) as exc:
            logger.warning("Password hashing failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password format",
            ) from exc
        role = "admin" if payload.email.lower() in admin_email_set() else "user"
        user = await self._user_repo.create(email=payload.email, password_hash=hashed, role=role)
        await self._profile_repo.create_empty(user.id, full_name=payload.full_name)

        logger.info("New user registered: id=%s email=%s", user.id, user.email)

        return await self._issue_token_pair(user.id)

    async def login(self, payload: UserLogin) -> Token:
        """
        Authenticate a user:
        1. Look up by email
        2. Verify bcrypt password
        3. Return JWT token
        """
        user = await self._user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked",
            )
        if user.email.lower() in admin_email_set() and user.role != "admin":
            user.role = "admin"
            logger.info("Auto-promoted admin user: id=%s email=%s", user.id, user.email)

        logger.info("User logged in: id=%s", user.id)

        return await self._issue_token_pair(user.id)

    async def refresh(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh" or not payload.get("sub"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        hashed = hash_token(refresh_token)
        active = await self._refresh_repo.get_active(hashed)
        if not active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

        user_id = int(payload["sub"])
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is locked")
        if user.email.lower() in admin_email_set() and user.role != "admin":
            user.role = "admin"

        await self._refresh_repo.revoke(active)
        return await self._issue_token_pair(user_id)

    async def logout(self, refresh_token: str) -> None:
        hashed = hash_token(refresh_token)
        active = await self._refresh_repo.get_active(hashed)
        if active:
            await self._refresh_repo.revoke(active)

    async def forgot_password(self, payload: ForgotPasswordRequest) -> MessageResponse:
        """Always return generic message; send email if user exists."""
        generic = MessageResponse(
            message="Nếu email tồn tại, chúng tôi đã gửi liên kết đặt lại mật khẩu.",
        )
        user = await self._user_repo.get_by_email(payload.email)
        if not user:
            return generic

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS)
        await self._reset_repo.invalidate_user_tokens(user.id)
        await self._reset_repo.create(user.id, hash_token(raw_token), expires_at)

        reset_url = f"{settings.FRONTEND_ORIGIN.rstrip('/')}/reset-password?token={raw_token}"
        try:
            await send_password_reset_email(to_email=user.email, reset_url=reset_url)
        except Exception:
            if settings.DEBUG:
                logger.warning("Dev reset URL for %s: %s", user.email, reset_url)
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Không gửi được email. Vui lòng thử lại sau.",
                ) from None

        msg = generic.message
        if settings.DEBUG and not smtp_configured():
            msg = f"{msg} (Dev: kiểm tra log server để lấy link reset.)"
        return MessageResponse(message=msg)

    async def reset_password(self, payload: ResetPasswordRequest) -> MessageResponse:
        token_hash = hash_token(payload.token)
        row = await self._reset_repo.get_valid(token_hash)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token không hợp lệ hoặc đã hết hạn.",
            )
        user = await self._user_repo.get_by_id(row.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        try:
            new_hash = hash_password(payload.new_password)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu mới không hợp lệ.",
            ) from exc

        await self._user_repo.update_password_hash(user, new_hash)
        await self._reset_repo.mark_used(row)
        await self._refresh_repo.revoke_all_for_user(user.id)
        return MessageResponse(message="Đã đặt lại mật khẩu thành công. Vui lòng đăng nhập lại.")

    async def _issue_token_pair(self, user_id: int) -> Token:
        access_token = create_access_token(subject=user_id)
        raw_refresh = create_refresh_token(subject=user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._refresh_repo.create(user_id=user_id, token_hash=hash_token(raw_refresh), expires_at=expires_at)
        return Token(access_token=access_token, refresh_token=raw_refresh)
