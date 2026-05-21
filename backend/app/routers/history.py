"""
app/routers/history.py
───────────────────────
History endpoints: list practice attempts (paginated) and save new results.
All routes require a valid JWT bearer token.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas import HistoryResponse, HistorySave, PaginatedHistory
from app.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "",
    response_model=PaginatedHistory,
    summary="List practice attempts (paginated)",
)
async def get_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=15, ge=1, le=100, description="Items per page"),
    subject: str | None = Query(
        default=None,
        description="Filter by skill: reading, listening, writing, speaking (omit = all)",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedHistory:
    """Return a paginated list of the authenticated user's practice attempts, newest first."""
    service = HistoryService(db)
    return await service.get_history(
        current_user, page=page, page_size=page_size, subject=subject
    )


@router.post(
    "/save",
    response_model=HistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a practice result and update progress",
)
async def save_history(
    payload: HistorySave,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    """
    Persist a practice attempt and atomically update the related subject progress.

    This is the key integration endpoint called after every learning session.
    """
    service = HistoryService(db)
    return await service.save_practice_result(current_user, payload)
