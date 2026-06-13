"""Generate synthetic score_history for forecast model training demos."""

from __future__ import annotations

import logging
import random
from datetime import date, timedelta

import numpy as np
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.score_history_repository import ScoreHistoryRepository
from app.services.score_snapshot_service import FORECAST_SKILLS

logger = logging.getLogger(__name__)
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _generate_skill_series(
    rng: random.Random,
    days: int,
    start_band: float,
) -> list[dict]:
    rows: list[dict] = []
    band = start_band
    for offset in range(days):
        dow = offset % 7
        season = 0.12 * np.sin(2 * np.pi * dow / 7)
        trend = 0.003 * offset
        noise = rng.uniform(-0.18, 0.18)
        band = max(4.0, min(8.5, band + trend / 30 + season / 12 + noise))
        session_min = max(5.0, rng.gauss(22, 8))
        correct_rate = max(0.35, min(0.98, (band / 9.0) + rng.uniform(-0.08, 0.08)))
        rows.append(
            {
                "y": round(band, 2),
                "session_min": round(session_min, 1),
                "correct_rate": round(correct_rate, 4),
            }
        )
    return rows


class SyntheticForecastDataService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ScoreHistoryRepository(db)

    async def ensure_synthetic_users(self, count: int) -> list[int]:
        ids: list[int] = []
        for i in range(count):
            email = f"forecast_synthetic_{i:04d}@linguaielts.local"
            result = await self._db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    email=email,
                    password_hash=_pwd.hash("SyntheticForecast1!"),
                    role="user",
                    is_active=True,
                    is_verified=True,
                    auth_provider="email",
                )
                self._db.add(user)
                await self._db.flush()
            ids.append(user.id)
        await self._db.commit()
        return ids

    async def seed_user(
        self,
        user_id: int,
        *,
        days: int = 75,
        start_band: float | None = None,
        seed: int | None = None,
    ) -> int:
        rng = random.Random(seed if seed is not None else user_id)
        start = start_band if start_band is not None else rng.uniform(5.0, 6.5)
        end = date.today()
        start_date = end - timedelta(days=days - 1)
        inserted = 0

        for skill_idx, skill in enumerate(FORECAST_SKILLS):
            skill_start = start + rng.uniform(-0.4, 0.4)
            series = _generate_skill_series(rng, days, skill_start)
            for offset, point in enumerate(series):
                ds = start_date + timedelta(days=offset)
                existing = await self._repo.get_by_user_skill_date(user_id, skill, ds)
                if existing:
                    continue
                await self._repo.upsert_daily(
                    user_id=user_id,
                    skill=skill,
                    ds=ds,
                    y=point["y"],
                    session_min=point["session_min"],
                    correct_rate=point["correct_rate"],
                )
                inserted += 1

            # overall = mean of skills that day (approximate)
            for offset in range(days):
                ds = start_date + timedelta(days=offset)
                bands = []
                sm = 0.0
                cr: list[float] = []
                for s in FORECAST_SKILLS:
                    row = await self._repo.get_by_user_skill_date(user_id, s, ds)
                    if row:
                        bands.append(row.y)
                        sm += row.session_min
                        cr.append(row.correct_rate)
                if bands:
                    existing = await self._repo.get_by_user_skill_date(user_id, "overall", ds)
                    if not existing:
                        await self._repo.upsert_daily(
                            user_id=user_id,
                            skill="overall",
                            ds=ds,
                            y=round(sum(bands) / len(bands), 2),
                            session_min=sm,
                            correct_rate=round(sum(cr) / len(cr), 4),
                        )
                        inserted += 1

        await self._db.commit()
        return inserted

    async def seed_many(
        self,
        num_users: int = 500,
        *,
        min_days: int = 60,
        max_days: int = 90,
        create_users: bool = True,
    ) -> dict:
        user_ids: list[int]
        if create_users:
            user_ids = await self.ensure_synthetic_users(num_users)
        else:
            result = await self._db.execute(select(User.id).limit(num_users))
            user_ids = [row[0] for row in result.all()]

        total_rows = 0
        for uid in user_ids:
            days = random.randint(min_days, max_days)
            total_rows += await self.seed_user(uid, days=days, seed=uid)

        logger.info("Seeded %d users, ~%d score_history rows", len(user_ids), total_rows)
        return {"users": len(user_ids), "rows_inserted": total_rows}
