"""Placement onboarding API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas import (
    PlacementFinalizeResponse,
    PlacementFullExamFinalizeRequest,
    PlacementManualRequest,
    PlacementSessionResponse,
    PlacementStageResponse,
    PlacementStageSubmitRequest,
    PlacementStageSubmitResponse,
    PlacementStatusResponse,
)
from app.services.placement_service import PlacementService

router = APIRouter(prefix="/placement", tags=["Placement"])


@router.get("/status", response_model=PlacementStatusResponse)
async def get_placement_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementStatusResponse:
    return await PlacementService(db).status(current_user)


@router.post("/manual", response_model=PlacementFinalizeResponse)
async def submit_manual_placement(
    body: PlacementManualRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementFinalizeResponse:
    return await PlacementService(db).submit_manual(current_user, body)


@router.post("/full-exam/finalize", response_model=PlacementFinalizeResponse)
async def finalize_full_exam_placement(
    body: PlacementFullExamFinalizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementFinalizeResponse:
    return await PlacementService(db).finalize_full_exam(current_user, body)


@router.post("/sessions", response_model=PlacementSessionResponse)
async def create_placement_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementSessionResponse:
    return await PlacementService(db).create_session(current_user)


@router.get("/sessions/current", response_model=PlacementSessionResponse | None)
async def get_current_placement_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementSessionResponse | None:
    return await PlacementService(db).current_session(current_user)


@router.get("/sessions/{session_id}/stage/{stage}", response_model=PlacementStageResponse)
async def get_placement_stage(
    session_id: int,
    stage: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementStageResponse:
    return await PlacementService(db).get_stage(current_user, session_id, stage)


@router.post("/sessions/{session_id}/stage/{stage}/submit", response_model=PlacementStageSubmitResponse)
async def submit_placement_stage(
    session_id: int,
    stage: str,
    body: PlacementStageSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementStageSubmitResponse:
    return await PlacementService(db).submit_stage(current_user, session_id, stage, body)


@router.post("/sessions/{session_id}/finalize", response_model=PlacementFinalizeResponse)
async def finalize_placement_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlacementFinalizeResponse:
    return await PlacementService(db).finalize(current_user, session_id)
