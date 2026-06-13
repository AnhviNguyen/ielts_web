"""CLI: seed synthetic score_history for forecast pipeline."""

from __future__ import annotations

import argparse
import asyncio
import logging

from app.db.database import AsyncSessionLocal
from app.services.synthetic_forecast_data_service import SyntheticForecastDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _main(args: argparse.Namespace) -> None:
    async with AsyncSessionLocal() as db:
        svc = SyntheticForecastDataService(db)
        if args.user_id:
            rows = await svc.seed_user(args.user_id, days=args.days, seed=args.user_id)
            logger.info("Seeded user_id=%s rows=%d", args.user_id, rows)
            return
        result = await svc.seed_many(
            num_users=args.users,
            min_days=args.min_days,
            max_days=args.max_days,
            create_users=not args.no_create_users,
        )
        logger.info("Done: %s", result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed score_history synthetic data")
    parser.add_argument("--users", type=int, default=500, help="Number of synthetic users")
    parser.add_argument("--user-id", type=int, default=None, help="Seed single existing user")
    parser.add_argument("--days", type=int, default=75, help="Days for single user")
    parser.add_argument("--min-days", type=int, default=60)
    parser.add_argument("--max-days", type=int, default=90)
    parser.add_argument("--no-create-users", action="store_true")
    args = parser.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
