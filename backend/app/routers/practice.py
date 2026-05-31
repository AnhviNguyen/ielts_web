from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db.models import User
from app.schemas import (
    PracticeCheckAnswerRequest,
    PracticeCheckAnswerResponse,
    PracticeSessionResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
)
from app.services.practice_service import PracticeService

router = APIRouter(prefix="/practice", tags=["Practice"])


@router.get("/reading/session", response_model=PracticeSessionResponse)
async def get_reading_session(
    quiz_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeSessionResponse:
    payload = await PracticeService(db).create_session(current_user, subject="reading", quiz_id=quiz_id)
    return PracticeSessionResponse(**payload)


@router.get("/listening/session", response_model=PracticeSessionResponse)
async def get_listening_session(
    quiz_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeSessionResponse:
    payload = await PracticeService(db).create_session(current_user, subject="listening", quiz_id=quiz_id)
    return PracticeSessionResponse(**payload)


@router.post("/reading/submit", response_model=PracticeSubmitResponse)
async def submit_reading(
    request: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeSubmitResponse:
    payload = await PracticeService(db).submit(
        current_user,
        subject="reading",
        session_id=request.session_id,
        answers=request.answers,
        duration_seconds=request.duration_seconds,
    )
    return PracticeSubmitResponse(**payload)


@router.post("/listening/submit", response_model=PracticeSubmitResponse)
async def submit_listening(
    request: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeSubmitResponse:
    payload = await PracticeService(db).submit(
        current_user,
        subject="listening",
        session_id=request.session_id,
        answers=request.answers,
        duration_seconds=request.duration_seconds,
    )
    return PracticeSubmitResponse(**payload)


@limiter.limit("60/minute")
@router.post("/check-answer", response_model=PracticeCheckAnswerResponse)
async def check_answer(
    request: Request,
    body: PracticeCheckAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeCheckAnswerResponse:
    """Practice mode — grade one answer server-side and return explanation."""
    payload = await PracticeService(db).check_answer(
        current_user,
        session_id=body.session_id,
        question_id=body.question_id,
        user_answer=body.user_answer,
    )
    return PracticeCheckAnswerResponse(**payload)
