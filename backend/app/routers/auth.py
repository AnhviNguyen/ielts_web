"""
app/routers/auth.py
────────────────────
Auth endpoints: register and login.
No JWT required — these are public routes.
"""

from fastapi import APIRouter, Depends, Request, status
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
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    service = AuthService(db)
    token = await service.register(payload)
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
    token = await service.login(payload)
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
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    service = AuthService(db)
    token = await service.refresh(refresh_token)
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
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email token (mock in local dev)",
)
async def verify_email(_: VerifyEmailRequest) -> MessageResponse:
    return MessageResponse(message="Email verified (mock)")


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
