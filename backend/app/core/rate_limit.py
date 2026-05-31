"""Rate limiting (slowapi) shared limiter and 429 handler."""

from ipaddress import ip_address, ip_network

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

# Use Redis in production so limits apply across multiple API replicas.
_storage_uri = (
    settings.REDIS_URL
    if settings.ENVIRONMENT == "production" and settings.REDIS_URL
    else None
)

_TRUSTED_PROXY_NETS = (
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
)


def _client_ip(request: Request) -> str:
    peer = request.client.host if request.client else ""
    try:
        peer_ip = ip_address(peer)
    except ValueError:
        return peer or "unknown"

    if any(peer_ip in net for net in _TRUSTED_PROXY_NETS):
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",", 1)[0].strip()
        if first:
            try:
                return str(ip_address(first))
            except ValueError:
                pass
    return str(peer_ip)


limiter = Limiter(
    key_func=_client_ip,
    storage_uri=_storage_uri,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Qua nhieu yeu cau. Vui long thu lai sau."},
    )
