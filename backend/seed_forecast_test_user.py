"""Seed forecast test user: anhvi@gmail.com with 16 days practice + score history."""

from __future__ import annotations

import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.db.models import ForecastModelMeta, History, ScoreHistory, User, UserProfile
from app.repositories.profile_repository import ProfileRepository
from app.services.synthetic_forecast_data_service import SyntheticForecastDataService

EMAIL = "anhvi@gmail.com"
PASSWORD = "Anhvi@123"
FULL_NAME = "Anh Vi"
DAYS = 16

SKILL_ROTATION = ("Reading", "Listening", "Writing", "Speaking")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == EMAIL))
        user = result.scalar_one_or_none()

        if user:
            await db.execute(delete(History).where(History.user_id == user.id))
            await db.execute(delete(ScoreHistory).where(ScoreHistory.user_id == user.id))
            await db.execute(delete(ForecastModelMeta).where(ForecastModelMeta.user_id == user.id))
            user.password_hash = hash_password(PASSWORD)
            user.is_active = True
            user.is_verified = True
            user.role = "user"
        else:
            user = User(
                email=EMAIL,
                password_hash=hash_password(PASSWORD),
                role="user",
                is_active=True,
                is_verified=True,
                auth_provider="email",
            )
            db.add(user)
            await db.flush()

        profile_repo = ProfileRepository(db)
        profile = await profile_repo.get_by_user_id(user.id)
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            await db.flush()

        today = date.today()
        profile.full_name = FULL_NAME
        profile.streak = DAYS
        profile.longest_streak = DAYS
        profile.last_activity_date = today
        profile.xp = DAYS * 12
        profile.target_band = 7.0
        profile.placement_status = "completed"
        profile.initial_reading_band = 6.0
        profile.initial_listening_band = 5.5
        profile.initial_writing_band = 5.0
        profile.initial_speaking_band = 5.5
        profile.initial_overall_band = 5.5
        profile.placement_completed_at = datetime.now(timezone.utc) - timedelta(days=DAYS)

        await db.commit()

        score_rows = await SyntheticForecastDataService(db).seed_user(
            user.id,
            days=DAYS,
            start_band=5.5,
            seed=20260613,
        )

        rng = random.Random(20260613)
        start_date = today - timedelta(days=DAYS - 1)
        history_count = 0
        async with AsyncSessionLocal() as db2:
            for offset in range(DAYS):
                ds = start_date + timedelta(days=offset)
                attempts = 2 if offset % 2 == 0 else 1
                for attempt in range(attempts):
                    subject = SKILL_ROTATION[(offset + attempt) % len(SKILL_ROTATION)]
                    band = round(min(8.0, max(4.5, 5.0 + offset * 0.06 + rng.uniform(-0.15, 0.25))), 1)
                    pct = round((band / 9.0) * 100, 1)
                    completed = datetime(
                        ds.year,
                        ds.month,
                        ds.day,
                        10 + attempt * 3,
                        30,
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
                            duration_seconds=rng.randint(900, 2700),
                            completed_at=completed,
                        )
                    )
                    history_count += 1
            await db2.commit()

        print(
            f"OK user_id={user.id} email={EMAIL} password={PASSWORD} "
            f"streak={DAYS} score_history_rows={score_rows} history_attempts={history_count}"
        )


if __name__ == "__main__":
    asyncio.run(main())
