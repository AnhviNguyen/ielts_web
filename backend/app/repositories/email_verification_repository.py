"""
app/repositories/email_verification_repository.py
──────────────────────────────────────────────────
CRUD for email OTP verification tokens.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EmailVerification


class EmailVerificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, user_id: int, code_hash: str, expires_at: datetime) -> EmailVerification:
        row = EmailVerification(user_id=user_id, code_hash=code_hash, expires_at=expires_at)
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return row

    async def get_latest_unused(self, user_id: int) -> EmailVerification | None:
        """Return the most recent unused (not expired, not used) OTP for a user."""
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(EmailVerification)
            .where(
                EmailVerification.user_id == user_id,
                EmailVerification.used_at.is_(None),
                EmailVerification.expires_at > now,
            )
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, row: EmailVerification) -> None:
        row.used_at = datetime.now(timezone.utc)
        self._db.add(row)
        await self._db.flush()

    async def invalidate_all_for_user(self, user_id: int) -> None:
        """Expire all existing OTPs for a user before issuing a new one."""
        await self._db.execute(
            delete(EmailVerification).where(EmailVerification.user_id == user_id)
        )
        await self._db.flush()
