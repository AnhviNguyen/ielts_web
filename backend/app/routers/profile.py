"""
app/routers/profile.py
───────────────────────
Profile endpoints: view and update the current user's profile.
All routes require a valid JWT bearer token.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas import ProfileResponse, ProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/user", tags=["Profile"])


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get the authenticated user's profile",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Return profile + basic user info for the authenticated user."""
    service = ProfileService(db)
    return await service.get_profile(current_user)


@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="Update the authenticated user's profile",
)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """
    Partially update profile fields.
    Only fields present (non-null) in the request body will be updated.
    """
    service = ProfileService(db)
    return await service.update_profile(current_user, payload)


@router.get(
    "/stats",
    summary="Get dashboard stats for the authenticated user",
)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return lightweight dashboard metrics:
    streak, xp, band_scores, and days_to_exam.
    """
    service = ProfileService(db)
    return await service.get_user_stats(current_user)
