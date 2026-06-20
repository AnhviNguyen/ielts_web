"""
app/routers/auth.py
────────────────────
Auth endpoints: register, login, refresh, logout,
email verification, Google OAuth.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth_cookies import (
    attach_auth_cookies,
    clear_auth_cookies,
    read_refresh_token,
)
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.schemas import (
    AuthLogoutRequest,
    AuthRefreshRequest,
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
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

_AUTH_DB_TIMEOUT_SEC = 15.0


async def _with_db_timeout(coro):
    """Bound auth DB work so hung connections fail fast instead of nginx 499."""
    try:
        return await asyncio.wait_for(coro, timeout=_AUTH_DB_TIMEOUT_SEC)
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database request timed out",
        ) from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error",
        ) from exc


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (requires email verification)",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    service = AuthService(db)
    return await service.register(payload)


@router.post(
    "/verify-email",
    response_model=Token,
    summary="Verify email OTP and receive a token pair",
)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    service = AuthService(db)
    token = await service.verify_email_otp(payload)
    return attach_auth_cookies(token)


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Re-send the email verification OTP",
)
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    return await service.resend_verification(payload)


@router.post(
    "/google",
    response_model=Token,
    summary="Exchange Google authorization code for a token pair",
)
@limiter.limit("10/minute")
async def google_auth(
    request: Request,
    payload: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    service = AuthService(db)
    token = await service.google_auth(payload)
    return attach_auth_cookies(token)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive a JWT token",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    service = AuthService(db)
    token = await _with_db_timeout(service.login(payload))
    return attach_auth_cookies(token)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rotate refresh token and issue a new token pair",
)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    payload: AuthRefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    body_token = payload.refresh_token if payload else None
    refresh_token = read_refresh_token(request, body_token)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    service = AuthService(db)
    token = await _with_db_timeout(service.refresh(refresh_token))
    return attach_auth_cookies(token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke a refresh token",
)
async def logout(
    request: Request,
    payload: AuthLogoutRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    body_token = payload.refresh_token if payload else None
    refresh_token = read_refresh_token(request, body_token)
    service = AuthService(db)
    if refresh_token:
        await service.logout(refresh_token)
    response = JSONResponse(content={"message": "Logged out successfully"})
    clear_auth_cookies(response)
    return response


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset email",
)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    return await service.forgot_password(payload)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token from email",
)
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    return await service.reset_password(payload)
