"""Ingest practice results into daily score_history aggregates."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.score_history_repository import ScoreHistoryRepository

logger = logging.getLogger(__name__)

FORECAST_SKILLS = ("reading", "listening", "writing", "speaking")
ALL_SKILLS = (*FORECAST_SKILLS, "overall")


def normalize_skill(subject: str | None) -> str:
    raw = (subject or "reading").strip().lower()
    if raw in FORECAST_SKILLS:
        return raw
    if raw in ("read", "reading"):
        return "reading"
    if raw in ("listen", "listening"):
        return "listening"
    if raw in ("write", "writing"):
        return "writing"
    if raw in ("speak", "speaking", "conversation"):
        return "speaking"
    return raw if raw in ALL_SKILLS else "reading"


def resolve_band(band_score: float | None, percentage: float | None) -> float:
    if band_score is not None:
        return max(0.0, min(9.0, float(band_score)))
    if percentage is not None:
        return max(0.0, min(9.0, round((float(percentage) / 100.0) * 9.0, 1)))
    return 5.0


def resolve_correct_rate(percentage: float | None, band_score: float | None) -> float:
    if percentage is not None:
        return max(0.0, min(1.0, float(percentage) / 100.0))
    if band_score is not None:
        return max(0.0, min(1.0, float(band_score) / 9.0))
    return 0.5


class ScoreSnapshotService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ScoreHistoryRepository(db)
        self._db = db

    async def ingest_from_practice(
        self,
        user_id: int,
        *,
        subject: str | None,
        band_score: float | None,
        percentage: float | None,
        duration_seconds: int | None,
        completed_at: datetime | None = None,
    ) -> None:
        skill = normalize_skill(subject)
        if skill not in FORECAST_SKILLS:
            return

        when = completed_at or datetime.now(timezone.utc)
        ds = when.date() if hasattr(when, "date") else date.today()
        y = resolve_band(band_score, percentage)
        session_min = max(0.0, (duration_seconds or 0) / 60.0)
        correct_rate = resolve_correct_rate(percentage, band_score)

        await self._repo.upsert_daily(
            user_id=user_id,
            skill=skill,
            ds=ds,
            y=y,
            session_min=session_min,
            correct_rate=correct_rate,
        )
        await self._recompute_overall(user_id, ds)

    async def _recompute_overall(self, user_id: int, ds: date) -> None:
        bands: list[float] = []
        session_min = 0.0
        correct_rates: list[float] = []
        for skill in FORECAST_SKILLS:
            row = await self._repo.get_by_user_skill_date(user_id, skill, ds)
            if row:
                bands.append(row.y)
                session_min += row.session_min
                correct_rates.append(row.correct_rate)
        if not bands:
            return
        await self._repo.upsert_daily(
            user_id=user_id,
            skill="overall",
            ds=ds,
            y=round(sum(bands) / len(bands), 2),
            session_min=session_min,
            correct_rate=round(sum(correct_rates) / len(correct_rates), 4),
        )
