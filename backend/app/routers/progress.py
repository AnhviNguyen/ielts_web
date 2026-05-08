"""
app/routers/progress.py
────────────────────────
Progress endpoints: retrieve and update learning progress.
All routes require a valid JWT bearer token.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas import ProgressResponse, ProgressUpdateRequest
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get(
    "",
    response_model=list[ProgressResponse],
    summary="Get all subject progress records for the current user",
)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProgressResponse]:
    """Return every progress row for the authenticated user, ordered by subject."""
    service = ProgressService(db)
    return await service.get_progress(current_user)


@router.post(
    "/update",
    response_model=ProgressResponse,
    summary="Manually update (upsert) a subject progress record",
)
async def update_progress(
    payload: ProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgressResponse:
    """
    Insert or update a progress record for a given subject.
    Percentage is recalculated server-side.
    """
    service = ProgressService(db)
    return await service.update_progress(current_user, payload)
