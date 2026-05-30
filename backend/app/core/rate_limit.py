"""Rate limiting (slowapi) — shared limiter and 429 handler."""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

# Use Redis in production so limits apply across multiple API replicas.
_storage_uri = (
    settings.REDIS_URL
    if settings.ENVIRONMENT == "production" and settings.REDIS_URL
    else None
)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage_uri,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Quá nhiều yêu cầu. Vui lòng thử lại sau."},
    )
