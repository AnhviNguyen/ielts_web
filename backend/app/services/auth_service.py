"""
app/services/auth_service.py
──────────────────────────────
Business logic for registration, login, Google OAuth, and email verification.
Orchestrates UserRepository + ProfileRepository and issues JWT tokens.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.password_policy import assert_password_strength
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    MessageResponse,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    VerifyEmailRequest,
)
from app.services.email_service import email_configured, send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
# connect 10s, read/write 15s — fail fast instead of hanging until nginx 499
_GOOGLE_HTTP_TIMEOUT = httpx.Timeout(15.0, connect=10.0)
_GOOGLE_DB_TIMEOUT_SEC = 15.0


async def _fetch_google_user_info(payload: GoogleAuthRequest) -> dict[str, str]:
    """Exchange authorization code for Google access token, then fetch user profile."""
    try:
        async with httpx.AsyncClient(timeout=_GOOGLE_HTTP_TIMEOUT) as client:
            token_resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "code": payload.code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": payload.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                google_err = token_resp.json() if token_resp.headers.get("content-type", "").startswith("application/json") else {}
                google_err_code = google_err.get("error", "")
                logger.warning("Google token exchange failed (%s): %s", token_resp.status_code, token_resp.text)
                if google_err_code == "redirect_uri_mismatch":
                    detail = "Redirect URI không khớp. Kiểm tra cấu hình Google Cloud Console."
                elif google_err_code == "invalid_grant":
                    detail = "Mã Google đã hết hạn hoặc đã được dùng. Vui lòng thử lại."
                elif google_err_code == "invalid_client":
                    detail = "Cấu hình Google OAuth không đúng (client_id/secret)."
                else:
                    detail = f"Không thể xác thực với Google ({google_err_code or token_resp.status_code}). Vui lòng thử lại."
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=detail,
                )

            google_access = token_resp.json().get("access_token")
            if not google_access:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google token invalid.")

            info_resp = await client.get(
                _GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {google_access}"},
            )
    except httpx.TimeoutException as exc:
        logger.warning("Google OAuth HTTP request timed out: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Google xác thực quá lâu. Vui lòng thử lại.",
        ) from exc

    if info_resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không lấy được thông tin Google.")

    return info_resp.json()


def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._user_repo = UserRepository(db)
        self._profile_repo = ProfileRepository(db)
        self._refresh_repo = RefreshTokenRepository(db)
        self._reset_repo = PasswordResetRepository(db)
        self._verify_repo = EmailVerificationRepository(db)

    async def register(self, payload: UserCreate) -> RegisterResponse:
        """
        Register a new user with email verification:
        1. Check email is not taken
        2. Hash password
        3. Create unverified user row + empty profile
        4. Generate & send 6-digit OTP
        5. Return needs_verification response
        """
        existing = await self._user_repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        assert_password_strength(payload.password)

        try:
            hashed = hash_password(payload.password)
        except (ValueError, RuntimeError) as exc:
            logger.warning("Password hashing failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password format",
            ) from exc

        is_verified = not settings.REQUIRE_EMAIL_VERIFICATION
        user = await self._user_repo.create(
            email=payload.email,
            password_hash=hashed,
            role="user",
            is_verified=is_verified,
            auth_provider="email",
        )
        await self._profile_repo.create_empty(user.id, full_name=payload.full_name)
        if settings.REQUIRE_EMAIL_VERIFICATION:
            await self._send_otp(user.id, user.email)
            message = "Mã xác minh đã được gửi đến email của bạn."
        else:
            message = "Đăng ký tài khoản thành công."

        logger.info(
            "New user registered: id=%s email=%s verified=%s",
            user.id,
            user.email,
            is_verified,
        )
        return RegisterResponse(
            email=user.email,
            needs_verification=settings.REQUIRE_EMAIL_VERIFICATION,
            message=message,
        )

    async def verify_email_otp(self, payload: VerifyEmailRequest) -> Token:
        """Validate the 6-digit OTP and issue a token pair on success."""
        user = await self._user_repo.get_by_email(payload.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã xác minh không hợp lệ.")

        row = await self._verify_repo.get_latest_unused(user.id)
        if not row or row.code_hash != _hash_otp(payload.code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã xác minh không đúng hoặc đã hết hạn.")

        await self._verify_repo.mark_used(row)
        await self._user_repo.mark_verified(user)

        logger.info("Email verified for user id=%s", user.id)
        return await self._issue_token_pair(user.id)

    async def resend_verification(self, payload: ResendVerificationRequest) -> MessageResponse:
        """Re-send the verification OTP (always returns generic message)."""
        generic = MessageResponse(message="Nếu email tồn tại và chưa xác minh, chúng tôi đã gửi mã mới.")
        user = await self._user_repo.get_by_email(payload.email)
        if not user or user.is_verified:
            return generic

        await self._send_otp(user.id, user.email)
        return generic

    async def google_auth(self, payload: GoogleAuthRequest) -> Token:
        """
        Exchange a Google authorization code for user info,
        then find or create the user and issue a token pair.
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured on this server.",
            )

        info = await _fetch_google_user_info(payload)
        google_id: str = info.get("id", "")
        email: str = info.get("email", "")
        full_name: str = info.get("name", "")
        avatar_url: str = info.get("picture", "")

        if not google_id or not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google trả về thông tin không đầy đủ.")

        async def _persist_and_issue_token() -> Token:
            user = await self._user_repo.get_by_google_id(google_id)
            if not user:
                user = await self._user_repo.get_by_email(email)
                if user:
                    await self._user_repo.update_google_id(user, google_id)
                    if not user.is_verified:
                        await self._user_repo.mark_verified(user)
                    await self._update_profile_from_google(user.id, full_name, avatar_url)
                else:
                    placeholder_hash = hash_password(secrets.token_urlsafe(32))
                    user = await self._user_repo.create(
                        email=email,
                        password_hash=placeholder_hash,
                        google_id=google_id,
                        is_verified=True,
                        auth_provider="google",
                    )
                    await self._profile_repo.create_empty(
                        user.id,
                        full_name=full_name,
                        avatar_url=avatar_url,
                    )
            else:
                await self._update_profile_from_google(user.id, full_name, avatar_url)

            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa.")

            logger.info("Google OAuth login: user id=%s email=%s", user.id, user.email)
            return await self._issue_token_pair(user.id)

        try:
            return await asyncio.wait_for(_persist_and_issue_token(), timeout=_GOOGLE_DB_TIMEOUT_SEC)
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database request timed out",
            ) from exc

    # ── Existing methods (unchanged) ─────────────────────────────────────────

    async def login(self, payload: UserLogin) -> Token:
        user = await self._user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is locked")

        if not user.is_verified and settings.REQUIRE_EMAIL_VERIFICATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="email_not_verified",
                headers={"X-Email": user.email},
            )

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
        if settings.DEBUG and not email_configured():
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

        assert_password_strength(payload.new_password)

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

    async def _update_profile_from_google(
        self, user_id: int, google_name: str, google_avatar: str
    ) -> None:
        """Enrich user profile with Google data only when local fields are missing."""
        profile = await self._profile_repo.get_by_user_id(user_id)
        if not profile:
            await self._profile_repo.create_empty(
                user_id, full_name=google_name, avatar_url=google_avatar
            )
            return
        # Only update fields that are still empty — don't overwrite user's own edits
        new_name   = google_name   if google_name   and not profile.full_name   else None
        new_avatar = google_avatar if google_avatar and not profile.avatar_url  else None
        if new_name is not None or new_avatar is not None:
            await self._profile_repo.update(
                profile,
                full_name=new_name,
                phone=None,
                bio=None,
                avatar_url=new_avatar,
            )

    async def _send_otp(self, user_id: int, email: str) -> None:
        """Generate a 6-digit OTP, store its hash, and email the raw code."""
        await self._verify_repo.invalidate_all_for_user(user_id)
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFY_EXPIRE_MINUTES)
        await self._verify_repo.create(user_id=user_id, code_hash=_hash_otp(code), expires_at=expires_at)
        try:
            await send_verification_email(to_email=email, code=code)
        except Exception:
            if settings.DEBUG:
                logger.warning("Dev OTP for %s: %s", email, code)
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Không gửi được email xác minh. Vui lòng thử lại.",
                ) from None

    async def _issue_token_pair(self, user_id: int) -> Token:
        access_token = create_access_token(subject=user_id)
        raw_refresh = create_refresh_token(subject=user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._refresh_repo.create(user_id=user_id, token_hash=hash_token(raw_refresh), expires_at=expires_at)
        return Token(access_token=access_token, refresh_token=raw_refresh)
