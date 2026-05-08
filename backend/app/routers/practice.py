from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas import PracticeSessionResponse, PracticeSubmitRequest, PracticeSubmitResponse
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
        current_user, subject="reading", session_id=request.session_id, answers=request.answers
    )
    return PracticeSubmitResponse(**payload)


@router.post("/listening/submit", response_model=PracticeSubmitResponse)
async def submit_listening(
    request: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeSubmitResponse:
    payload = await PracticeService(db).submit(
        current_user, subject="listening", session_id=request.session_id, answers=request.answers
    )
    return PracticeSubmitResponse(**payload)


@router.get("/history")
async def practice_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await PracticeService(db).get_history(current_user, page=page, page_size=page_size)


@router.get("/history/{session_id}")
async def practice_history_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await PracticeService(db).get_session_result(current_user, session_id=session_id)
