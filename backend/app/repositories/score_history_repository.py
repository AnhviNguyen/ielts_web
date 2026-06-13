"""Database operations for score_history time-series."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScoreHistory


class ScoreHistoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_user_skill_date(
        self, user_id: int, skill: str, ds: date
    ) -> ScoreHistory | None:
        result = await self._db.execute(
            select(ScoreHistory).where(
                ScoreHistory.user_id == user_id,
                ScoreHistory.skill == skill,
                ScoreHistory.ds == ds,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_daily(
        self,
        user_id: int,
        skill: str,
        ds: date,
        y: float,
        session_min: float,
        correct_rate: float,
    ) -> ScoreHistory:
        row = await self.get_by_user_skill_date(user_id, skill, ds)
        if row:
            n = row.attempt_count + 1
            row.y = round((row.y * row.attempt_count + y) / n, 2)
            row.session_min = round(row.session_min + session_min, 2)
            row.correct_rate = round((row.correct_rate * row.attempt_count + correct_rate) / n, 4)
            row.attempt_count = n
            await self._db.flush()
            return row

        row = ScoreHistory(
            user_id=user_id,
            skill=skill,
            ds=ds,
            y=round(y, 2),
            session_min=round(session_min, 2),
            correct_rate=round(correct_rate, 4),
            attempt_count=1,
        )
        self._db.add(row)
        await self._db.flush()
        return row

    async def get_series(
        self, user_id: int, skill: str, *, lookback_days: int = 30
    ) -> list[ScoreHistory]:
        cutoff = date.today() - timedelta(days=lookback_days)
        result = await self._db.execute(
            select(ScoreHistory)
            .where(
                ScoreHistory.user_id == user_id,
                ScoreHistory.skill == skill,
                ScoreHistory.ds >= cutoff,
            )
            .order_by(ScoreHistory.ds.asc())
        )
        return list(result.scalars().all())

    async def count_days(self, user_id: int, skill: str) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(ScoreHistory)
            .where(ScoreHistory.user_id == user_id, ScoreHistory.skill == skill)
        )
        return int(result.scalar_one() or 0)

    async def list_skills(self, user_id: int) -> list[str]:
        result = await self._db.execute(
            select(ScoreHistory.skill)
            .where(ScoreHistory.user_id == user_id)
            .distinct()
            .order_by(ScoreHistory.skill.asc())
        )
        return [row[0] for row in result.all()]

    async def list_user_ids_with_data(self, *, min_days: int = 14) -> list[int]:
        subq = (
            select(
                ScoreHistory.user_id,
                ScoreHistory.skill,
                func.count().label("cnt"),
            )
            .group_by(ScoreHistory.user_id, ScoreHistory.skill)
            .having(func.count() >= min_days)
            .subquery()
        )
        result = await self._db.execute(select(subq.c.user_id).distinct())
        return [row[0] for row in result.all()]

    async def bulk_insert(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        objects = [ScoreHistory(**row) for row in rows]
        self._db.add_all(objects)
        await self._db.flush()
        return len(objects)
