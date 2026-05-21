"""
app/repositories/vocab_repository.py
─────────────────────────────────────
Single-responsibility data-access layer for Vocabulary.
All DB operations are here; no HTTP or business logic.
"""

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VocabTopic, VocabWord


class VocabRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Topics ────────────────────────────────────────────────────────────────

    async def list_topics_with_counts(self, user_id: int) -> list[tuple[VocabTopic, int]]:
        """Return every topic belonging to *user_id* paired with its word count."""
        topics_res = await self._db.execute(
            select(VocabTopic)
            .where(VocabTopic.user_id == user_id)
            .order_by(VocabTopic.sort_order, VocabTopic.created_at)
        )
        topics = topics_res.scalars().all()

        result: list[tuple[VocabTopic, int]] = []
        for topic in topics:
            count = await self._count_words(topic.id)
            result.append((topic, count))
        return result

    async def get_topic(self, topic_id: int, user_id: int) -> VocabTopic | None:
        res = await self._db.execute(
            select(VocabTopic).where(
                VocabTopic.id == topic_id,
                VocabTopic.user_id == user_id,
            )
        )
        return res.scalar_one_or_none()

    async def create_topic(self, user_id: int, name: str, sort_order: int = 0) -> VocabTopic:
        topic = VocabTopic(user_id=user_id, name=name, sort_order=sort_order)
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def update_topic(
        self,
        topic: VocabTopic,
        name: str | None = None,
        sort_order: int | None = None,
    ) -> VocabTopic:
        if name is not None:
            topic.name = name
        if sort_order is not None:
            topic.sort_order = sort_order
        self._db.add(topic)
        await self._db.flush()
        await self._db.refresh(topic)
        return topic

    async def delete_topic(self, topic: VocabTopic) -> None:
        await self._db.delete(topic)
        await self._db.flush()

    async def count_words_in_topic(self, topic_id: int) -> int:
        return await self._count_words(topic_id)

    async def count_topics(self, user_id: int) -> int:
        res = await self._db.execute(
            select(func.count()).select_from(VocabTopic).where(VocabTopic.user_id == user_id)
        )
        return res.scalar() or 0

    async def create_words_bulk(self, topic_id: int, rows: list[dict]) -> list[VocabWord]:
        created: list[VocabWord] = []
        for row in rows:
            word = VocabWord(topic_id=topic_id, **row)
            self._db.add(word)
            created.append(word)
        await self._db.flush()
        for w in created:
            await self._db.refresh(w)
        return created

    # ── Words ─────────────────────────────────────────────────────────────────

    async def list_words(self, topic_id: int) -> list[VocabWord]:
        res = await self._db.execute(
            select(VocabWord)
            .where(VocabWord.topic_id == topic_id)
            .order_by(VocabWord.created_at.desc())
        )
        return list(res.scalars().all())

    async def list_study_queue(self, topic_id: int, limit: int = 80) -> list[VocabWord]:
        """Words due for SRS review (new = no next_review, or past due)."""
        now = datetime.now(timezone.utc)
        res = await self._db.execute(
            select(VocabWord)
            .where(
                VocabWord.topic_id == topic_id,
                or_(
                    VocabWord.srs_next_review_at.is_(None),
                    VocabWord.srs_next_review_at <= now,
                ),
            )
            .order_by(VocabWord.srs_next_review_at.asc().nullsfirst(), VocabWord.id)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def count_due_words(self, topic_id: int) -> int:
        now = datetime.now(timezone.utc)
        res = await self._db.execute(
            select(func.count())
            .select_from(VocabWord)
            .where(
                VocabWord.topic_id == topic_id,
                or_(
                    VocabWord.srs_next_review_at.is_(None),
                    VocabWord.srs_next_review_at <= now,
                ),
            )
        )
        return res.scalar() or 0

    async def get_word(self, word_id: int, topic_id: int) -> VocabWord | None:
        res = await self._db.execute(
            select(VocabWord).where(
                VocabWord.id == word_id,
                VocabWord.topic_id == topic_id,
            )
        )
        return res.scalar_one_or_none()

    async def create_word(self, topic_id: int, data: dict) -> VocabWord:
        word = VocabWord(topic_id=topic_id, **data)
        self._db.add(word)
        await self._db.flush()
        await self._db.refresh(word)
        return word

    async def update_word(self, word: VocabWord, data: dict) -> VocabWord:
        for field, value in data.items():
            setattr(word, field, value)
        self._db.add(word)
        await self._db.flush()
        await self._db.refresh(word)
        return word

    async def delete_word(self, word: VocabWord) -> None:
        await self._db.delete(word)
        await self._db.flush()

    async def search_words(self, user_id: int, query: str, limit: int = 30) -> list[VocabWord]:
        """Full-text search across word and meaning_vi for a user's entire vocabulary."""
        q = f"%{query.lower()}%"
        res = await self._db.execute(
            select(VocabWord)
            .join(VocabTopic, VocabWord.topic_id == VocabTopic.id)
            .where(
                VocabTopic.user_id == user_id,
                or_(
                    func.lower(VocabWord.word).like(q),
                    func.lower(VocabWord.meaning_vi).like(q),
                    func.lower(VocabWord.example).like(q),
                ),
            )
            .order_by(VocabWord.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())

    async def get_user_stats(self, user_id: int) -> dict[str, int]:
        """Aggregate mastery counts across ALL topics for a user."""
        res = await self._db.execute(
            select(VocabWord.mastery, func.count().label("cnt"))
            .join(VocabTopic, VocabWord.topic_id == VocabTopic.id)
            .where(VocabTopic.user_id == user_id)
            .group_by(VocabWord.mastery)
        )
        stats: dict[str, int] = {"total": 0, "new": 0, "learning": 0, "mastered": 0}
        for mastery, cnt in res.all():
            if mastery in stats:
                stats[mastery] = cnt
            stats["total"] += cnt
        return stats

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _count_words(self, topic_id: int) -> int:
        res = await self._db.execute(
            select(func.count()).where(VocabWord.topic_id == topic_id)
        )
        return res.scalar() or 0
