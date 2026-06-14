"""
tests/integration/services/test_auth_service.py
─────────────────────────────────────────────────
Integration tests for AuthService.
Covers registration, login, verification, password reset, and Google OAuth.
Mocks external requests (httpx) and email sending (send_*_email).
"""

import pytest
import secrets
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.models import User, UserProfile, EmailVerification, RefreshToken, PasswordResetToken
from app.services.auth_service import AuthService
from app.schemas import (
    UserCreate,
    VerifyEmailRequest,
    ResendVerificationRequest,
    UserLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GoogleAuthRequest,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def auth_service(db_session):
    return AuthService(db_session)


# ---------------------------------------------------------------------------
# AS-01 & AS-02: Register
# ---------------------------------------------------------------------------

@patch("app.services.auth_service.send_verification_email", new_callable=AsyncMock)
async def test_as01_register_new_user_success(mock_send_email, auth_service, db_session):
    """
    AS-01: Đăng ký user mới với email hợp lệ -> Tạo user, profile (unverified) và gửi OTP.
    """
    payload = UserCreate(
        email="newuser@example.com",
        password="Password123!",
        full_name="New User",
    )

    resp = await auth_service.register(payload)
    assert resp.email == "newuser@example.com"

    # Verify user created in DB
    stmt = select(User).options(selectinload(User.profile)).where(User.email == "newuser@example.com")
    res = await db_session.execute(stmt)
    user = res.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is False
    assert user.auth_provider == "email"

    # Verify profile created
    assert user.profile is not None
    assert user.profile.full_name == "New User"

    # Verify OTP email sent
    mock_send_email.assert_called_once()
    called_email = mock_send_email.call_args[1]["to_email"]
    called_code = mock_send_email.call_args[1]["code"]
    assert called_email == "newuser@example.com"
    assert len(called_code) == 6


async def test_as02_register_email_already_exists(auth_service, make_user):
    """
    AS-02: Đăng ký với email đã tồn tại -> Raise 400.
    """
    await make_user(email="existing@example.com")

    payload = UserCreate(
        email="existing@example.com",
        password="Password123!",
        full_name="Duplicate User",
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register(payload)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Email already registered"


# ---------------------------------------------------------------------------
# OTP Verification
# ---------------------------------------------------------------------------

@patch("app.services.auth_service.send_verification_email", new_callable=AsyncMock)
async def test_as_verify_email_otp_success(mock_send_email, auth_service, db_session, make_user):
    """
    Verify OTP with correct code -> Marks verified and issues tokens.
    """
    user = await make_user(email="otp@example.com", is_verified=False)
    await auth_service._send_otp(user.id, user.email)

    # Fetch the generated OTP from DB
    stmt = select(EmailVerification).where(EmailVerification.user_id == user.id)
    res = await db_session.execute(stmt)
    otp_row = res.scalars().all()[-1]
    
    # We must patch or find the raw code since it is hashed. Let's retrieve code from the mock call
    mock_send_email.assert_called_once()
    raw_code = mock_send_email.call_args[1]["code"]

    payload = VerifyEmailRequest(email="otp@example.com", code=raw_code)
    token = await auth_service.verify_email_otp(payload)
    
    assert token.access_token is not None
    assert token.refresh_token is not None

    # Check user is verified
    await db_session.refresh(user)
    assert user.is_verified is True


# ---------------------------------------------------------------------------
# AS-03 to AS-06: Login
# ---------------------------------------------------------------------------

async def test_as03_login_success(auth_service, make_user):
    """
    AS-03: Login đúng email + password -> Trả về access + refresh token.
    """
    from app.core.security import hash_password
    hashed = hash_password("Password123!")
    user = await make_user(email="login@example.com", password_hash=hashed, is_verified=True)

    payload = UserLogin(email="login@example.com", password="Password123!")
    token = await auth_service.login(payload)
    assert token.access_token is not None
    assert token.refresh_token is not None


async def test_as04_login_wrong_password(auth_service, make_user):
    """
    AS-04: Login sai password -> Raise 401.
    """
    from app.core.security import hash_password
    hashed = hash_password("Password123!")
    await make_user(email="wrongpass@example.com", password_hash=hashed, is_verified=True)

    payload = UserLogin(email="wrongpass@example.com", password="IncorrectPassword")
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login(payload)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password" in exc_info.value.detail


async def test_as05_login_unverified_email(auth_service, make_user):
    """
    AS-05: Login user chưa verify email -> Raise 403 with email_not_verified.
    """
    from app.core.security import hash_password
    hashed = hash_password("Password123!")
    await make_user(email="unverified@example.com", password_hash=hashed, is_verified=False)

    payload = UserLogin(email="unverified@example.com", password="Password123!")
    with patch.object(settings, "REQUIRE_EMAIL_VERIFICATION", True):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(payload)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "email_not_verified"
        assert exc_info.value.headers.get("X-Email") == "unverified@example.com"


async def test_as06_login_locked_user(auth_service, make_user):
    """
    AS-06: Login user bị khóa -> Raise 403.
    """
    from app.core.security import hash_password
    hashed = hash_password("Password123!")
    user = await make_user(email="locked@example.com", password_hash=hashed, is_verified=True)
    user.is_active = False
    
    payload = UserLogin(email="locked@example.com", password="Password123!")
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login(payload)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Account is locked" in exc_info.value.detail


# ---------------------------------------------------------------------------
# AS-07 to AS-10: Token Refresh & Logout
# ---------------------------------------------------------------------------

async def test_as07_refresh_token_success(auth_service, make_user, db_session):
    """
    AS-07: Refresh token hợp lệ -> revokes old and issues new access + refresh token.
    """
    user = await make_user(email="refresh@example.com")
    tokens = await auth_service._issue_token_pair(user.id)

    await asyncio.sleep(1.0)
    new_tokens = await auth_service.refresh(tokens.refresh_token)
    assert new_tokens.access_token is not None
    assert new_tokens.refresh_token is not None
    assert new_tokens.refresh_token != tokens.refresh_token

    from app.core.security import hash_token
    old_hashed = hash_token(tokens.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == old_hashed)
    res = await db_session.execute(stmt)
    old_token_row = res.scalar_one()
    assert old_token_row.revoked is True


async def test_as08_refresh_token_revoked(auth_service, make_user, db_session):
    """
    AS-08: Refresh token đã bị revoke -> Raise 401.
    """
    user = await make_user(email="revoked@example.com")
    tokens = await auth_service._issue_token_pair(user.id)

    from app.core.security import hash_token
    old_hashed = hash_token(tokens.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == old_hashed)
    res = await db_session.execute(stmt)
    row = res.scalar_one()
    row.revoked = True
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.refresh(tokens.refresh_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired or revoked" in exc_info.value.detail


async def test_as09_refresh_token_expired(auth_service, make_user, db_session):
    """
    AS-09: Refresh token hết hạn -> Raise 401.
    """
    user = await make_user(email="expiredtoken@example.com")
    tokens = await auth_service._issue_token_pair(user.id)

    from app.core.security import hash_token
    hashed = hash_token(tokens.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed)
    res = await db_session.execute(stmt)
    row = res.scalar_one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.refresh(tokens.refresh_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired or revoked" in exc_info.value.detail


async def test_as10_logout_revokes_refresh_token(auth_service, make_user, db_session):
    """
    AS-10: Logout -> refresh token bị revoke.
    """
    user = await make_user(email="logout@example.com")
    tokens = await auth_service._issue_token_pair(user.id)

    await auth_service.logout(tokens.refresh_token)

    from app.core.security import hash_token
    hashed = hash_token(tokens.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed)
    res = await db_session.execute(stmt)
    row = res.scalar_one()
    assert row.revoked is True


# ---------------------------------------------------------------------------
# AS-11 & AS-12: Google OAuth
# ---------------------------------------------------------------------------

@patch("app.services.auth_service.settings")
async def test_as11_google_auth_new_user(mock_settings, auth_service, db_session):
    """
    AS-11: Google OAuth với google_id mới -> Tạo user + profile tự động, set verified=True.
    """
    mock_settings.GOOGLE_CLIENT_ID = "fake_client_id"
    mock_settings.GOOGLE_CLIENT_SECRET = "fake_client_secret"
    mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "google_access_token"}

    mock_info_resp = MagicMock()
    mock_info_resp.status_code = 200
    mock_info_resp.json.return_value = {
        "id": "google_user_12345",
        "email": "newgoogle@example.com",
        "name": "Google User",
        "picture": "http://avatar.url",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_token_resp):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_info_resp):
            payload = GoogleAuthRequest(code="google_auth_code", redirect_uri="http://localhost/callback")
            token = await auth_service.google_auth(payload)

            assert token.access_token is not None
            assert token.refresh_token is not None

            stmt = select(User).options(selectinload(User.profile)).where(User.google_id == "google_user_12345")
            res = await db_session.execute(stmt)
            user = res.scalar_one_or_none()
            assert user is not None
            assert user.email == "newgoogle@example.com"
            assert user.is_verified is True
            assert user.auth_provider == "google"

            assert user.profile is not None
            assert user.profile.full_name == "Google User"
            assert user.profile.avatar_url == "http://avatar.url"


@patch("app.services.auth_service.settings")
async def test_as12_google_auth_existing_email_links_google_id(mock_settings, auth_service, db_session, make_user):
    """
    AS-12: Google OAuth với email đã tồn tại -> Liên kết google_id với email có sẵn.
    """
    mock_settings.GOOGLE_CLIENT_ID = "fake_client_id"
    mock_settings.GOOGLE_CLIENT_SECRET = "fake_client_secret"
    mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

    existing_user = await make_user(email="link@example.com", is_verified=False, auth_provider="email")

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "google_access_token"}

    mock_info_resp = MagicMock()
    mock_info_resp.status_code = 200
    mock_info_resp.json.return_value = {
        "id": "google_user_67890",
        "email": "link@example.com",
        "name": "Google Linked Name",
        "picture": "http://avatar.url/linked",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_token_resp):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_info_resp):
            payload = GoogleAuthRequest(code="google_auth_code", redirect_uri="http://localhost/callback")
            token = await auth_service.google_auth(payload)

            assert token.access_token is not None
            assert token.refresh_token is not None

            # Eagerly load user with profile to avoid lazy load issues
            stmt = select(User).options(selectinload(User.profile)).where(User.id == existing_user.id)
            res = await db_session.execute(stmt)
            linked_user = res.scalar_one()

            assert linked_user.google_id == "google_user_67890"
            assert linked_user.is_verified is True

            assert linked_user.profile is not None
            assert linked_user.profile.full_name == "Google Linked Name"
            assert linked_user.profile.avatar_url == "http://avatar.url/linked"
