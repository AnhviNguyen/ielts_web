"""
app/routers/auth.py
────────────────────
Auth endpoints: register and login.
No JWT required — these are public routes.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import (
    AuthLogoutRequest,
    AuthRefreshRequest,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Create a new user account.

    - Hashes password with bcrypt
    - Creates an empty profile row
    - Returns a JWT token (user is immediately authenticated)
    """
    service = AuthService(db)
    return await service.register(payload)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive a JWT token",
)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Authenticate with email + password.

    Returns a JWT bearer token valid for 7 days.
    """
    service = AuthService(db)
    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rotate refresh token and issue a new token pair",
)
async def refresh(payload: AuthRefreshRequest, db: AsyncSession = Depends(get_db)) -> Token:
    service = AuthService(db)
    return await service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke a refresh token",
)
async def logout(payload: AuthLogoutRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    service = AuthService(db)
    await service.logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email token (mock in local dev)",
)
async def verify_email(_: VerifyEmailRequest) -> MessageResponse:
    return MessageResponse(message="Email verified (mock)")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Create reset password request (mock in local dev)",
)
async def forgot_password(_: ForgotPasswordRequest) -> MessageResponse:
    return MessageResponse(message="Password reset email sent (mock)")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token (mock in local dev)",
)
async def reset_password(_: ResetPasswordRequest) -> MessageResponse:
    return MessageResponse(message="Password reset successful (mock)")
