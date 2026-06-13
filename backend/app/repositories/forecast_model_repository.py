"""Database operations for forecast_model_meta."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ForecastModelMeta


class ForecastModelRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, user_id: int, skill: str) -> ForecastModelMeta | None:
        result = await self._db.execute(
            select(ForecastModelMeta).where(
                ForecastModelMeta.user_id == user_id,
                ForecastModelMeta.skill == skill,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: int,
        skill: str,
        *,
        trainer: str,
        mae: float | None,
        rmse: float | None,
        sample_count: int,
        model_path: str | None,
        is_active: bool = True,
    ) -> ForecastModelMeta:
        row = await self.get(user_id, skill)
        now = datetime.now(timezone.utc)
        if row:
            row.trainer = trainer
            row.mae = mae
            row.rmse = rmse
            row.sample_count = sample_count
            row.model_path = model_path
            row.is_active = is_active
            row.trained_at = now
        else:
            row = ForecastModelMeta(
                user_id=user_id,
                skill=skill,
                trainer=trainer,
                mae=mae,
                rmse=rmse,
                sample_count=sample_count,
                model_path=model_path,
                is_active=is_active,
                trained_at=now,
            )
            self._db.add(row)
        await self._db.flush()
        return row
