"""Conversation Practice repository."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ConversationSession, ConversationTopic


class ConversationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def count_topics(self) -> int:
        result = await self._db.execute(select(func.count()).select_from(ConversationTopic))
        return result.scalar_one()

    async def list_topics(self, level: str | None = None) -> list[ConversationTopic]:
        q = select(ConversationTopic).order_by(ConversationTopic.order)
        if level:
            q = q.where(ConversationTopic.level == level)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def get_topic(self, topic_id: int) -> ConversationTopic | None:
        result = await self._db.execute(
            select(ConversationTopic).where(ConversationTopic.id == topic_id)
        )
        return result.scalar_one_or_none()

    async def get_topic_by_title(self, title: str) -> ConversationTopic | None:
        result = await self._db.execute(
            select(ConversationTopic).where(ConversationTopic.title == title)
        )
        return result.scalar_one_or_none()

    async def create_topic(self, order: int, data: dict) -> ConversationTopic:
        topic = ConversationTopic(
            order=order,
            title=data["title"],
            description=data.get("description", ""),
            level=data.get("level", "beginner"),
            icon_emoji=data.get("icon_emoji", "💬"),
            ai_role=data["ai_role"],
            user_role=data["user_role"],
            scenario=data["scenario"],
            opening_line=data["opening_line"],
            vocabulary=data.get("vocabulary", []),
        )
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def get_session(self, session_id: int) -> ConversationSession | None:
        result = await self._db.execute(
            select(ConversationSession).where(ConversationSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_for_user(self, session_id: int, user_id: int) -> ConversationSession | None:
        result = await self._db.execute(
            select(ConversationSession).where(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_session(
        self, user_id: int, topic_id: int, opening_line: str
    ) -> ConversationSession:
        session = ConversationSession(
            user_id=user_id,
            topic_id=topic_id,
            history=[{"role": "assistant", "content": opening_line}],
            status="active",
        )
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        return session

    async def update_session_history(
        self, session: ConversationSession, history: list[dict]
    ) -> None:
        session.history = history
        await self._db.flush()

    async def complete_session(
        self, session: ConversationSession, feedback: dict
    ) -> None:
        session.status = "completed"
        session.feedback = feedback
        session.completed_at = datetime.now(timezone.utc)
        await self._db.flush()
