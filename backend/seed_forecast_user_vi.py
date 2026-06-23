"""Seed forecast demo data for an existing user (keeps password unchanged)."""

from __future__ import annotations

import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.db.database import AsyncSessionLocal
from app.db.models import ForecastModelMeta, History, Progress, ScoreHistory, User, UserProfile
from app.repositories.profile_repository import ProfileRepository
from app.repositories.score_history_repository import ScoreHistoryRepository
from app.services.score_snapshot_service import FORECAST_SKILLS

EMAIL = "nguyenngocanhvi852002@gmail.com"
DAYS = 45
START_BAND = 5.0
END_BAND = 6.8
SKILL_ROTATION = ("Reading", "Listening", "Writing", "Speaking")
SKILL_OFFSETS = {"reading": 0.15, "listening": -0.05, "writing": -0.2, "speaking": 0.1}


def _band_for_day(offset: int, skill: str, rng: random.Random) -> float:
    """Clear upward trend 5.0 → ~6.8 with small per-skill spread."""
    progress = offset / max(DAYS - 1, 1)
    base = START_BAND + (END_BAND - START_BAND) * progress
    return round(min(8.5, max(4.5, base + SKILL_OFFSETS.get(skill, 0) + rng.uniform(-0.12, 0.12))), 2)


async def _seed_score_history(db, user_id: int, rng: random.Random) -> int:
    repo = ScoreHistoryRepository(db)
    today = date.today()
    start_date = today - timedelta(days=DAYS - 1)
    inserted = 0

    for offset in range(DAYS):
        ds = start_date + timedelta(days=offset)
        day_bands: list[float] = []
        for skill in FORECAST_SKILLS:
            y = _band_for_day(offset, skill, rng)
            session_min = round(max(10.0, rng.gauss(25, 6)), 1)
            correct_rate = round(max(0.4, min(0.95, y / 9.0 + rng.uniform(-0.06, 0.06))), 4)
            await repo.upsert_daily(
                user_id=user_id,
                skill=skill,
                ds=ds,
                y=y,
                session_min=session_min,
                correct_rate=correct_rate,
            )
            day_bands.append(y)
            inserted += 1

        overall_y = round(sum(day_bands) / len(day_bands), 2)
        await repo.upsert_daily(
            user_id=user_id,
            skill="overall",
            ds=ds,
            y=overall_y,
            session_min=round(sum(max(10.0, rng.gauss(25, 6)) for _ in FORECAST_SKILLS), 1),
            correct_rate=round(sum(day_bands) / len(day_bands) / 9.0, 4),
        )
        inserted += 1

    await db.commit()
    return inserted


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == EMAIL))
        user = result.scalar_one_or_none()
        if not user:
            raise SystemExit(f"User not found: {EMAIL}")

        await db.execute(delete(History).where(History.user_id == user.id))
        await db.execute(delete(ScoreHistory).where(ScoreHistory.user_id == user.id))
        await db.execute(delete(ForecastModelMeta).where(ForecastModelMeta.user_id == user.id))
        await db.execute(delete(Progress).where(Progress.user_id == user.id))

        profile_repo = ProfileRepository(db)
        profile = await profile_repo.get_by_user_id(user.id)
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            await db.flush()

        today = date.today()
        profile.streak = min(DAYS, 21)
        profile.longest_streak = DAYS
        profile.last_activity_date = today
        profile.xp = DAYS * 15
        profile.target_band = 7.0
        profile.placement_status = "completed"
        profile.initial_reading_band = 5.5
        profile.initial_listening_band = 5.0
        profile.initial_writing_band = 5.0
        profile.initial_speaking_band = 5.5
        profile.initial_overall_band = 5.25
        profile.placement_completed_at = datetime.now(timezone.utc) - timedelta(days=DAYS)
        await db.commit()

        rng = random.Random(user.id)
        score_rows = await _seed_score_history(db, user.id, rng)

        start_date = today - timedelta(days=DAYS - 1)
        history_count = 0
        progress_totals: dict[str, dict[str, float | int]] = {}

        async with AsyncSessionLocal() as db2:
            for offset in range(DAYS):
                ds = start_date + timedelta(days=offset)
                attempts = 2 if offset % 2 == 0 else 1
                for attempt in range(attempts):
                    subject = SKILL_ROTATION[(offset + attempt) % len(SKILL_ROTATION)]
                    skill_key = subject.lower()
                    band = _band_for_day(offset, skill_key, rng)
                    pct = round((band / 9.0) * 100, 1)
                    completed = datetime(
                        ds.year,
                        ds.month,
                        ds.day,
                        9 + attempt * 4,
                        rng.randint(0, 59),
                        tzinfo=timezone.utc,
                    )
                    db2.add(
                        History(
                            user_id=user.id,
                            quiz_id=f"seed-{subject.lower()}-{ds.isoformat()}-{attempt}",
                            subject=subject,
                            score=int(pct / 10),
                            total_questions=40,
                            percentage=pct,
                            band_score=band,
                            mode="practice",
                            duration_seconds=rng.randint(900, 3600),
                            completed_at=completed,
                        )
                    )
                    history_count += 1
                    bucket = progress_totals.setdefault(subject, {"completed": 0, "bands": []})
                    bucket["completed"] = int(bucket["completed"]) + 1
                    bucket["bands"].append(band)

            for subject, stats in progress_totals.items():
                bands = stats["bands"]
                avg_band = round(sum(bands) / len(bands), 1)
                completed = int(stats["completed"])
                db2.add(
                    Progress(
                        user_id=user.id,
                        subject=subject,
                        total_questions=completed * 40,
                        completed_questions=completed * 40,
                        percentage=round((avg_band / 9.0) * 100, 1),
                        band_score=avg_band,
                    )
                )

            await db2.commit()

        print(
            f"OK user_id={user.id} email={EMAIL} days={DAYS} "
            f"score_history_rows={score_rows} history_attempts={history_count}"
        )


if __name__ == "__main__":
    asyncio.run(main())
