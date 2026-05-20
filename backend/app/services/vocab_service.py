"""
app/services/vocab_service.py
──────────────────────────────
Business logic for Vocabulary CRUD.
Owns ownership checks, validation, and orchestration.
Does NOT touch HTTP or the database directly.
"""

from fastapi import HTTPException, status

from app.db.models import VocabTopic, VocabWord
from app.repositories.vocab_repository import VocabRepository
from app.schemas import (
    VocabTopicResponse,
    VocabWordCreate,
    VocabWordUpdate,
)


class VocabService:
    def __init__(self, repo: VocabRepository) -> None:
        self._repo = repo

    # ── Topics ────────────────────────────────────────────────────────────────

    async def list_topics(self, user_id: int) -> list[VocabTopicResponse]:
        pairs = await self._repo.list_topics_with_counts(user_id)
        return [
            VocabTopicResponse(
                id=t.id,
                user_id=t.user_id,
                name=t.name,
                sort_order=t.sort_order,
                created_at=t.created_at,
                word_count=count,
            )
            for t, count in pairs
        ]

    async def create_topic(self, user_id: int, name: str) -> VocabTopicResponse:
        name = name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Topic name cannot be empty")
        topic = await self._repo.create_topic(user_id, name)
        return VocabTopicResponse(
            id=topic.id, user_id=topic.user_id, name=topic.name,
            sort_order=topic.sort_order, created_at=topic.created_at, word_count=0,
        )

    async def update_topic(
        self,
        topic_id: int,
        user_id: int,
        name: str | None,
        sort_order: int | None,
    ) -> VocabTopicResponse:
        topic = await self._require_owned_topic(topic_id, user_id)
        if name is not None:
            name = name.strip()
            if not name:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Topic name cannot be empty")
        topic = await self._repo.update_topic(topic, name=name, sort_order=sort_order)
        count = await self._repo.count_words_in_topic(topic.id)
        return VocabTopicResponse(
            id=topic.id, user_id=topic.user_id, name=topic.name,
            sort_order=topic.sort_order, created_at=topic.created_at, word_count=count,
        )

    async def delete_topic(self, topic_id: int, user_id: int) -> None:
        topic = await self._require_owned_topic(topic_id, user_id)
        await self._repo.delete_topic(topic)

    # ── Words ─────────────────────────────────────────────────────────────────

    async def list_words(self, topic_id: int, user_id: int) -> list[VocabWord]:
        await self._require_owned_topic(topic_id, user_id)
        return await self._repo.list_words(topic_id)

    async def create_word(
        self,
        topic_id: int,
        user_id: int,
        data: VocabWordCreate,
    ) -> VocabWord:
        await self._require_owned_topic(topic_id, user_id)
        word_data = data.model_dump(exclude_none=True)
        word_data.setdefault("source_type", "manual")
        return await self._repo.create_word(topic_id, word_data)

    async def update_word(
        self,
        topic_id: int,
        word_id: int,
        user_id: int,
        data: VocabWordUpdate,
    ) -> VocabWord:
        await self._require_owned_topic(topic_id, user_id)
        word = await self._require_word(word_id, topic_id)
        return await self._repo.update_word(word, data.model_dump(exclude_none=True))

    async def delete_word(self, topic_id: int, word_id: int, user_id: int) -> None:
        await self._require_owned_topic(topic_id, user_id)
        word = await self._require_word(word_id, topic_id)
        await self._repo.delete_word(word)

    async def search_words(self, user_id: int, query: str) -> list[VocabWord]:
        query = query.strip()
        if len(query) < 1:
            return []
        return await self._repo.search_words(user_id, query)

    async def get_stats(self, user_id: int) -> dict[str, int]:
        return await self._repo.get_user_stats(user_id)

    # ── Private guard helpers ─────────────────────────────────────────────────

    async def _require_owned_topic(self, topic_id: int, user_id: int) -> VocabTopic:
        topic = await self._repo.get_topic(topic_id, user_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        return topic

    async def _require_word(self, word_id: int, topic_id: int) -> VocabWord:
        word = await self._repo.get_word(word_id, topic_id)
        if not word:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
        return word
