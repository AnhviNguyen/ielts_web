"""HttpOnly refresh cookie + double-submit CSRF for SPA auth."""

from __future__ import annotations

import secrets
from urllib.parse import urlparse

from fastapi import HTTPException, Request, Response, status
from starlette.responses import JSONResponse

from app.core.config import settings
from app.schemas import Token

REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
COOKIE_PATH = "/api"


def _secure() -> bool:
    return settings.auth_cookie_secure


def _cookie_flags() -> dict:
    return {
        "httponly": True,
        "secure": _secure(),
        "samesite": "lax",
        "path": COOKIE_PATH,
    }


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=max_age,
        **_cookie_flags(),
    )


def set_csrf_cookie(response: Response, csrf_token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=False,
        secure=_secure(),
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    response.delete_cookie(CSRF_COOKIE, path="/")


def read_refresh_token(request: Request, body_token: str | None = None) -> str | None:
    cookie_val = request.cookies.get(REFRESH_COOKIE)
    if cookie_val:
        return cookie_val
    if body_token:
        return body_token
    return None


def attach_auth_cookies(token: Token) -> JSONResponse:
    """Return JSON with access_token; refresh in httpOnly cookie when enabled."""
    if not settings.auth_httponly_refresh:
        return JSONResponse(content=token.model_dump())

    csrf = secrets.token_urlsafe(32)
    payload = {
        "access_token": token.access_token,
        "refresh_token": None,
        "token_type": token.token_type,
    }
    response = JSONResponse(content=payload)
    if token.refresh_token:
        set_refresh_cookie(response, token.refresh_token)
    set_csrf_cookie(response, csrf)
    return response


def _request_origin(request: Request) -> str | None:
    """Browser Origin, or scheme+host parsed from Referer."""
    origin = (request.headers.get("origin") or "").strip()
    if origin:
        return origin.rstrip("/")
    referer = (request.headers.get("referer") or "").strip()
    if not referer:
        return None
    parsed = urlparse(referer)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return None


def _origin_is_trusted(request: Request) -> bool:
    origin = _request_origin(request)
    if not origin:
        return False
    return origin in settings.csrf_trusted_origins


def validate_csrf(request: Request) -> None:
    """Double-submit: header must match csrf_token cookie."""
    if not settings.auth_httponly_refresh:
        return
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    path = request.url.path.rstrip("/") or "/"
    exempt_prefixes = (
        "/auth/login",
        "/auth/register",
        "/auth/refresh",            # refresh uses httpOnly cookie — no CSRF token needed
        "/auth/logout",             # logout is safe (revoke-only, no state change risk)
        "/auth/forgot-password",
        "/auth/reset-password",
        "/auth/google",             # Google OAuth — no session yet when exchanging code
        "/auth/verify-email",       # OTP verify — public, no session yet
        "/auth/resend-verification", # OTP resend — public, no session yet
        "/health",
        "/internal",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    )
    if any(path == p or path.startswith(p + "/") for p in exempt_prefixes):
        return

    if _origin_is_trusted(request):
        return

    header = request.headers.get(CSRF_HEADER)
    cookie = request.cookies.get(CSRF_COOKIE)
    if not header or not cookie or header != cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )
