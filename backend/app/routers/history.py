"""
app/routers/history.py
───────────────────────
History endpoints: list practice attempts (paginated) and save new results.
All routes require a valid JWT bearer token.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db.models import User
from app.schemas import HistoryResponse, HistorySave, PaginatedHistory
from app.services.history_service import HistoryService
from app.services.practice_service import PracticeService

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


@router.get(
    "/completed-quiz-ids",
    summary="Distinct quiz/topic IDs the user has already attempted",
)
async def get_completed_quiz_ids(
    subject: str | None = Query(
        default=None,
        description="Filter by skill: reading, listening, writing, speaking (omit = all)",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = HistoryService(db)
    quiz_ids = await service.get_completed_quiz_ids(current_user, subject=subject)
    return {"quiz_ids": quiz_ids}


@router.post(
    "/save",
    response_model=HistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a practice result and update progress",
)
@limiter.limit("30/minute")
async def save_history(
    request: Request,
    payload: HistorySave,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    """
    Persist a practice attempt and atomically update the related subject progress.

    This is the key integration endpoint called after every learning session.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Direct history submission is disabled. Use the skill-specific submit "
            "endpoints so scores, bands, XP, and progress are computed server-side."
        ),
    )


@router.get(
    "/quiz/{quiz_id}",
    summary="Latest attempt for a quiz (Reading/Listening review)",
)
async def get_history_by_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await PracticeService(db).get_latest_history_by_quiz(current_user, quiz_id=quiz_id)


@router.get(
    "/sessions/{session_id}",
    summary="Practice session result with answer details",
)
async def get_history_by_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await PracticeService(db).get_session_result(current_user, session_id=session_id)
