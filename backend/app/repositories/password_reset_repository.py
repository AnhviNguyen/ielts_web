"""Password reset token persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PasswordResetToken


class PasswordResetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, user_id: int, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        row = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return row

    async def get_valid(self, token_hash: str) -> PasswordResetToken | None:
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, row: PasswordResetToken) -> None:
        row.used_at = datetime.now(timezone.utc)
        self._db.add(row)
        await self._db.flush()

    async def invalidate_user_tokens(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
        )
        for row in result.scalars().all():
            row.used_at = now
            self._db.add(row)
        await self._db.flush()
