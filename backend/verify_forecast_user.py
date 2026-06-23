"""Verify forecast training/prediction for seeded user."""

from __future__ import annotations

import asyncio
import sys

from app.db.database import AsyncSessionLocal
from app.services.forecast_service import ForecastService
from app.services.next_week_forecast_service import NextWeekForecastService
from app.services.score_snapshot_service import FORECAST_SKILLS


async def main() -> None:
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    async with AsyncSessionLocal() as db:
        fs = ForecastService(db)
        for skill in list(FORECAST_SKILLS) + ["overall"]:
            ok = await fs.train_skill(user_id, skill, force=True)
            fc = await fs.get_forecast(user_id, skill)
            pred = fc.forecast[-1].yhat if fc.forecast else None
            print(
                f"{skill}: trained={ok} trainer={fc.trainer} "
                f"days={fc.sample_days} pred_day14={pred}"
            )
        nw = NextWeekForecastService(db)
        resp = await nw.get_next_week_forecast(user_id, notify=False)
        print(
            f"next_week cold_start={resp.cold_start} "
            f"current={resp.overall.current} predicted={resp.overall.predicted} "
            f"status={resp.overall.status}"
        )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
