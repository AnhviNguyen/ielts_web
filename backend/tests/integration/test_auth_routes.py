import pytest
import asyncio
import hashlib
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import User, EmailVerification, RefreshToken
from app.core.security import create_access_token, hash_token, hash_password

pytestmark = pytest.mark.integration


def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


@patch("app.services.auth_service.send_verification_email", new_callable=AsyncMock)
async def test_auth_register_success(mock_send_email, client, db_session):
    """Test successful user registration."""
    payload = {
        "email": "newrouteruser@example.com",
        "password": "Password123!",
        "full_name": "Router User",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newrouteruser@example.com"
    assert data["needs_verification"] is True

    # Verify database entry
    stmt = select(User).where(User.email == "newrouteruser@example.com")
    res = await db_session.execute(stmt)
    user = res.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is False
    mock_send_email.assert_called_once()


async def test_auth_register_duplicate_email(client, make_user):
    """Test register returns 400 when email already exists."""
    await make_user(email="duplicate@example.com")
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Duplicate User",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already registered"


async def test_auth_register_invalid_email(client):
    """Test register returns 422 for invalid email formats."""
    payload = {
        "email": "invalid-email-format",
        "password": "Password123!",
        "full_name": "Invalid User",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("app.services.auth_service.send_verification_email", new_callable=AsyncMock)
async def test_auth_verify_email_flow(mock_send_email, client, db_session, make_user):
    """Test email verification with valid OTP code."""
    user = await make_user(email="otpuser@example.com", is_verified=False)
    await db_session.flush()

    # Create verification code manually
    verification = EmailVerification(
        user_id=user.id,
        code_hash=_hash_otp("123456"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db_session.add(verification)
    await db_session.commit()

    payload = {
        "email": "otpuser@example.com",
        "code": "123456",
    }
    response = await client.post("/auth/verify-email", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

    # Verify user is verified now
    await db_session.refresh(user)
    assert user.is_verified is True


async def test_auth_verify_email_wrong_otp(client, db_session, make_user):
    """Test verification returns 400 for incorrect OTP."""
    user = await make_user(email="otpuser2@example.com", is_verified=False)
    await db_session.flush()

    verification = EmailVerification(
        user_id=user.id,
        code_hash=_hash_otp("111111"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db_session.add(verification)
    await db_session.commit()

    payload = {
        "email": "otpuser2@example.com",
        "code": "222222",
    }
    response = await client.post("/auth/verify-email", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Mã xác minh không đúng hoặc đã hết hạn."


@patch("app.services.auth_service.send_verification_email", new_callable=AsyncMock)
async def test_auth_resend_verification_success(mock_send_email, client, db_session, make_user):
    """Test resending verification email OTP."""
    user = await make_user(email="resend@example.com", is_verified=False)
    await db_session.commit()

    payload = {"email": "resend@example.com"}
    response = await client.post("/auth/resend-verification", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Nếu email tồn tại và chưa xác minh, chúng tôi đã gửi mã mới."
    mock_send_email.assert_called_once()


async def test_auth_login_success(client, db_session, make_user):
    """Test login with valid credentials."""
    pwd_hash = hash_password("Password123!")
    user = await make_user(email="loginuser@example.com", password_hash=pwd_hash, is_verified=True)
    await db_session.commit()

    payload = {
        "email": "loginuser@example.com",
        "password": "Password123!",
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_auth_login_unverified(client, db_session, make_user):
    """Test login on unverified account raises 403."""
    pwd_hash = hash_password("Password123!")
    user = await make_user(email="unverified@example.com", password_hash=pwd_hash, is_verified=False)
    await db_session.commit()

    payload = {
        "email": "unverified@example.com",
        "password": "Password123!",
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "email_not_verified" in response.json()["detail"]


async def test_auth_login_locked(client, db_session, make_user):
    """Test login on locked account raises 403."""
    pwd_hash = hash_password("Password123!")
    user = await make_user(email="locked@example.com", password_hash=pwd_hash, is_verified=True)
    user.is_active = False
    user.locked_at = datetime.now(timezone.utc)
    user.lock_reason = "Spamming"
    db_session.add(user)
    await db_session.commit()

    payload = {
        "email": "locked@example.com",
        "password": "Password123!",
    }
    response = await client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Account is locked" in response.json()["detail"]


async def test_auth_refresh_token(client, db_session, make_user):
    """Test refresh token rotation."""
    user = await make_user(email="refresh@example.com", is_verified=True)
    await db_session.flush()

    from app.core.security import create_refresh_token
    raw_refresh = create_refresh_token(subject=user.id)
    hashed = hash_token(raw_refresh)

    refresh_token_db = RefreshToken(
        user_id=user.id,
        token_hash=hashed,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(refresh_token_db)
    await db_session.commit()

    # Sleep to avoid identical JWT generation when refresh generates the next token
    await asyncio.sleep(1.0)

    payload = {
        "refresh_token": raw_refresh,
    }
    response = await client.post("/auth/refresh", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


async def test_auth_logout(client, db_session, make_user):
    """Test logout revokes the refresh token."""
    user = await make_user(email="logout@example.com", is_verified=True)
    await db_session.flush()

    from app.core.security import create_refresh_token
    raw_refresh = create_refresh_token(subject=user.id)
    hashed = hash_token(raw_refresh)

    refresh_token_db = RefreshToken(
        user_id=user.id,
        token_hash=hashed,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(refresh_token_db)
    await db_session.commit()

    payload = {
        "refresh_token": raw_refresh,
    }
    response = await client.post("/auth/logout", json=payload)
    assert response.status_code == status.HTTP_200_OK

    # Check database to ensure token is deleted/revoked
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed)
    res = await db_session.execute(stmt)
    token_row = res.scalar_one_or_none()
    assert token_row is None or token_row.revoked is True


@patch("app.services.auth_service.send_password_reset_email", new_callable=AsyncMock)
async def test_auth_forgot_password(mock_send_email, client, db_session, make_user):
    """Test forgot password request."""
    user = await make_user(email="forgot@example.com", is_verified=True)
    await db_session.commit()

    payload = {"email": "forgot@example.com"}
    response = await client.post("/auth/forgot-password", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert "liên kết đặt lại mật khẩu" in response.json()["message"]
    mock_send_email.assert_called_once()
