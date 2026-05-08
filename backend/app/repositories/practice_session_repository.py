from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PracticeSession


class PracticeSessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, user_id: int, session_type: str, quiz_id: str | None) -> PracticeSession:
        row = PracticeSession(user_id=user_id, session_type=session_type, quiz_id=quiz_id, status="started")
        self._db.add(row)
        await self._db.flush()
        await self._db.refresh(row)
        return row

    async def get_by_id_for_user(self, session_id: int, user_id: int) -> PracticeSession | None:
        result = await self._db.execute(
            select(PracticeSession).where(PracticeSession.id == session_id, PracticeSession.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def mark_submitted(self, session: PracticeSession, score: float | None) -> PracticeSession:
        session.status = "submitted"
        session.score = score
        session.submitted_at = datetime.now(timezone.utc)
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        return session
