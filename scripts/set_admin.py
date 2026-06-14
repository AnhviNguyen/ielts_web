#!/usr/bin/env python3
"""
Promote an existing user to admin by email.

Uses DATABASE_URL from the environment (same as the API).

Usage (from repo root):
    python scripts/set_admin.py your@email.com

On Railway (API service, with Postgres linked):
    railway run python scripts/set_admin.py your@email.com

Alternative (from backend/):
    python -m app.cli.promote_admin --email your@email.com
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow `import app` when run from repo root
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from sqlalchemy import func, select

from app.db.database import AsyncSessionLocal
from app.db.models import User


async def set_admin(email: str) -> int:
    normalized = email.strip().lower()
    if not normalized:
        print("Error: email is required.", file=sys.stderr)
        return 1

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(func.lower(User.email) == normalized)
            )
            user = result.scalar_one_or_none()
            if not user:
                print(f"Error: no user found with email {normalized}", file=sys.stderr)
                return 1
            if user.role == "admin":
                print(f"OK: {normalized} is already admin (id={user.id}).")
                return 0
            user.role = "admin"
            await db.commit()
            print(f"Success: promoted user id={user.id} ({normalized}) to admin.")
            return 0
        except Exception as exc:
            await db.rollback()
            print(f"Error: {exc}", file=sys.stderr)
            return 1


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_admin.py <email>", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(asyncio.run(set_admin(sys.argv[1])))


if __name__ == "__main__":
    main()
