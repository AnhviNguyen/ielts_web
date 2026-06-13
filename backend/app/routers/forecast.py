"""Score forecast API — JWT-scoped under /users/me/forecast."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas import (
    ForecastAlertsResponse,
    ForecastResponse,
    ForecastSkillListResponse,
    MessageResponse,
    NextWeekForecastResponse,
    ScoreIngestRequest,
)
from app.services.forecast_service import ForecastService
from app.services.next_week_forecast_service import NextWeekForecastService

router = APIRouter(prefix="/users/me/forecast", tags=["Forecast"])


def _check_enabled() -> None:
    if not settings.FORECAST_ENABLED:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Forecasting is disabled")


@router.post("/score", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def ingest_score(
    payload: ScoreIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    _check_enabled()
    await ForecastService(db).ingest_score(current_user.id, payload)
    return MessageResponse(message="Score snapshot recorded")


@router.get("", response_model=ForecastSkillListResponse)
async def list_forecast_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ForecastSkillListResponse:
    _check_enabled()
    skills = await ForecastService(db).list_skills(current_user.id)
    return ForecastSkillListResponse(skills=skills)


@router.get("/alerts", response_model=ForecastAlertsResponse)
async def get_forecast_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ForecastAlertsResponse:
    _check_enabled()
    return await ForecastService(db).get_alerts(current_user.id)


@router.get("/next-week", response_model=NextWeekForecastResponse)
async def get_next_week_forecast(
    notify: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NextWeekForecastResponse:
    _check_enabled()
    result = await NextWeekForecastService(db).get_next_week_forecast(
        current_user.id, notify=notify
    )
    await db.commit()
    return result


@router.get("/{skill}", response_model=ForecastResponse)
async def get_skill_forecast(
    skill: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ForecastResponse:
    _check_enabled()
    skill_norm = skill.strip().lower()
    return await ForecastService(db).get_forecast(current_user.id, skill_norm)


@router.post("/{skill}/retrain", response_model=MessageResponse)
async def retrain_skill_forecast(
    skill: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    _check_enabled()
    skill_norm = skill.strip().lower()
    ok = await ForecastService(db).train_skill(current_user.id, skill_norm, force=True)
    if not ok:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Not enough data to train (need {settings.FORECAST_MIN_DAYS}+ days)",
        )
    return MessageResponse(message="Model retrained")
