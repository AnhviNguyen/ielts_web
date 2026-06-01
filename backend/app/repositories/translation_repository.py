"""
Translation Practice repository — pure data access layer.
"""
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    TranslationStep,
    TranslationTopic,
    TranslationSentence,
    TranslationAttempt,
)


class TranslationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Steps ────────────────────────────────────────────────────────────────

    async def list_steps(self, *, active_only: bool = False) -> list[TranslationStep]:
        stmt = select(TranslationStep).order_by(TranslationStep.order)
        if active_only:
            stmt = stmt.where(TranslationStep.is_active.is_(True))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_step(self, step_id: int) -> TranslationStep | None:
        result = await self._db.execute(
            select(TranslationStep)
            .where(TranslationStep.id == step_id)
            .options(selectinload(TranslationStep.topics))
        )
        return result.scalar_one_or_none()

    async def count_steps(self) -> int:
        result = await self._db.execute(select(func.count()).select_from(TranslationStep))
        return result.scalar_one()

    async def get_step_by_title(self, title: str) -> TranslationStep | None:
        result = await self._db.execute(
            select(TranslationStep).where(TranslationStep.title == title)
        )
        return result.scalar_one_or_none()

    async def max_step_order(self) -> int:
        result = await self._db.execute(select(func.max(TranslationStep.order)))
        value = result.scalar_one()
        return value or 0

    # ── Topics ───────────────────────────────────────────────────────────────

    async def list_topics_for_step(
        self, step_id: int, *, active_only: bool = False
    ) -> list[TranslationTopic]:
        stmt = (
            select(TranslationTopic)
            .where(TranslationTopic.step_id == step_id)
            .order_by(TranslationTopic.order)
        )
        if active_only:
            stmt = stmt.where(TranslationTopic.is_active.is_(True))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_topic(self, topic_id: int) -> TranslationTopic | None:
        result = await self._db.execute(
            select(TranslationTopic).where(TranslationTopic.id == topic_id)
        )
        return result.scalar_one_or_none()

    async def get_topic_by_title(self, step_id: int, title: str) -> TranslationTopic | None:
        result = await self._db.execute(
            select(TranslationTopic).where(
                TranslationTopic.step_id == step_id,
                TranslationTopic.title == title,
            )
        )
        return result.scalar_one_or_none()

    async def count_topics_in_step(self, step_id: int) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(TranslationTopic)
            .where(TranslationTopic.step_id == step_id)
        )
        return result.scalar_one()

    async def count_sentences_in_topic(self, topic_id: int, *, active_only: bool = False) -> int:
        stmt = (
            select(func.count())
            .select_from(TranslationSentence)
            .where(TranslationSentence.topic_id == topic_id)
        )
        if active_only:
            stmt = stmt.where(TranslationSentence.is_active.is_(True))
        result = await self._db.execute(stmt)
        return result.scalar_one()

    # ── Sentences ────────────────────────────────────────────────────────────

    async def list_sentences_for_topic(
        self, topic_id: int, *, active_only: bool = False
    ) -> list[TranslationSentence]:
        stmt = (
            select(TranslationSentence)
            .where(TranslationSentence.topic_id == topic_id)
            .order_by(TranslationSentence.order)
        )
        if active_only:
            stmt = stmt.where(TranslationSentence.is_active.is_(True))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_sentence(self, sentence_id: int) -> TranslationSentence | None:
        result = await self._db.execute(
            select(TranslationSentence).where(TranslationSentence.id == sentence_id)
        )
        return result.scalar_one_or_none()

    async def sentence_exists(self, topic_id: int, vietnamese: str) -> bool:
        result = await self._db.execute(
            select(func.count())
            .select_from(TranslationSentence)
            .where(
                TranslationSentence.topic_id == topic_id,
                TranslationSentence.vietnamese == vietnamese,
            )
        )
        return result.scalar_one() > 0

    # ── Attempts ─────────────────────────────────────────────────────────────

    async def create_attempt(
        self,
        user_id: int,
        sentence_id: int,
        user_translation: str,
        score: float | None,
        feedback: str | None,
        model_answer: str | None,
    ) -> TranslationAttempt:
        attempt = TranslationAttempt(
            user_id=user_id,
            sentence_id=sentence_id,
            user_translation=user_translation,
            score=score,
            feedback=feedback,
            model_answer=model_answer,
        )
        self._db.add(attempt)
        await self._db.flush()
        await self._db.refresh(attempt)
        return attempt

    async def get_user_attempt_for_sentence(
        self, user_id: int, sentence_id: int
    ) -> TranslationAttempt | None:
        """Return the latest attempt for a (user, sentence) pair."""
        result = await self._db.execute(
            select(TranslationAttempt)
            .where(
                TranslationAttempt.user_id == user_id,
                TranslationAttempt.sentence_id == sentence_id,
            )
            .order_by(TranslationAttempt.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_completed_sentences(self, user_id: int, topic_id: int) -> int:
        """How many distinct sentences in this topic the user has attempted."""
        subq = (
            select(TranslationSentence.id)
            .where(TranslationSentence.topic_id == topic_id)
            .scalar_subquery()
        )
        result = await self._db.execute(
            select(func.count(func.distinct(TranslationAttempt.sentence_id)))
            .where(
                TranslationAttempt.user_id == user_id,
                TranslationAttempt.sentence_id.in_(subq),
            )
        )
        return result.scalar_one()

    # ── Seed helpers ─────────────────────────────────────────────────────────

    async def create_step(
        self,
        order: int,
        title: str,
        description: str,
        badge_label: str | None,
        badge_color: str,
        icon_emoji: str,
    ) -> TranslationStep:
        step = TranslationStep(
            order=order,
            title=title,
            description=description,
            badge_label=badge_label,
            badge_color=badge_color,
            icon_emoji=icon_emoji,
        )
        self._db.add(step)
        await self._db.flush()
        await self._db.refresh(step)
        return step

    async def create_topic(
        self, step_id: int, order: int, title: str, description: str
    ) -> TranslationTopic:
        topic = TranslationTopic(
            step_id=step_id, order=order, title=title, description=description
        )
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def create_sentence(
        self,
        topic_id: int,
        order: int,
        vietnamese: str,
        english: str,
        explanation: str | None,
    ) -> TranslationSentence:
        sentence = TranslationSentence(
            topic_id=topic_id,
            order=order,
            vietnamese=vietnamese,
            english=english,
            explanation=explanation,
        )
        self._db.add(sentence)
        await self._db.flush()
        return sentence
