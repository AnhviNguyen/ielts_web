"""
One-shot CLI to grant admin role to an existing user by email.

Usage (from backend/):
    python -m app.cli.promote_admin --email admin@example.com

Does not auto-promote at login/register — assign admin deliberately via this tool
or direct SQL: UPDATE users SET role='admin' WHERE email='...';
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import User

logger = logging.getLogger(__name__)


async def _promote(email: str) -> int:
    normalized = email.strip().lower()
    if not normalized:
        print("Email is required.", file=sys.stderr)
        return 1

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == normalized))
        user = result.scalar_one_or_none()
        if not user:
            print(f"No user found with email: {normalized}", file=sys.stderr)
            return 1
        if user.role == "admin":
            print(f"User {normalized} is already admin (id={user.id}).")
            return 0
        user.role = "admin"
        await db.commit()
        print(f"Promoted user id={user.id} ({normalized}) to admin.")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a user to admin by email.")
    parser.add_argument("--email", required=True, help="Registered user email")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_promote(args.email)))


if __name__ == "__main__":
    main()
