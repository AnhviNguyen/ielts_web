"""
app/core/dependencies.py
─────────────────────────
FastAPI dependency functions injected into protected routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.db.database import AsyncSession, get_db
from app.db.models import User
from sqlalchemy import select

# Bearer token extractor (required)
_bearer = HTTPBearer(auto_error=True)
# Bearer token extractor (optional — for public endpoints that benefit from auth context)
_bearer_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the JWT bearer token and return the authenticated User ORM object.

    Raises:
        401 – token missing / invalid / expired
        404 – user no longer exists in DB
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is locked")

    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require an active authenticated admin user."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Như get_current_user nhưng không raise lỗi nếu không có token.
    Dùng cho public endpoints có thể benefit từ user context (vd: leaderboard).
    """
    if not credentials:
        return None
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user and not user.is_active:
        return None
    return user
