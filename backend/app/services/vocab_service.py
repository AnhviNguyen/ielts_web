"""
app/services/vocab_service.py
──────────────────────────────
Business logic for Vocabulary CRUD.
Owns ownership checks, validation, and orchestration.
Does NOT touch HTTP or the database directly.
"""

from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.models import User, VocabTopic, VocabWord
from app.core.xp import xp_from_duration
from app.repositories.history_repository import HistoryRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.vocab_repository import VocabRepository
from app.data.vocab_starter_pack import STARTER_TOPICS
from app.schemas import (
    VocabBootstrapResponse,
    VocabReadingPassageResponse,
    VocabReviewRequest,
    VocabStudyModesResponse,
    VocabSessionCompleteResponse,
    VocabStudyQueueResponse,
    VocabTopicDetailResponse,
    VocabTopicResponse,
    VocabWordCreate,
    VocabWordResponse,
    VocabWordUpdate,
)
from app.services.vocab_srs import sm2_apply
from app.services.vocab_reading_ai import generate_reading_passage as ai_reading_passage
from app.services.vocab_study_modes import VOCAB_STUDY_MODES


class VocabService:
    def __init__(self, repo: VocabRepository) -> None:
        self._repo = repo

    # ── Topics ────────────────────────────────────────────────────────────────

    @staticmethod
    def list_study_modes() -> VocabStudyModesResponse:
        return VocabStudyModesResponse(modes=VOCAB_STUDY_MODES)

    async def list_topics(self, user_id: int) -> list[VocabTopicResponse]:
        if await self._repo.count_topics(user_id) == 0:
            await self.bootstrap_starter_pack(user_id)
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

    async def get_topic_detail(self, topic_id: int, user_id: int) -> VocabTopicDetailResponse:
        topic = await self._require_owned_topic(topic_id, user_id)
        words = await self._repo.list_words(topic_id)
        count = len(words)
        return VocabTopicDetailResponse(
            topic=VocabTopicResponse(
                id=topic.id,
                user_id=topic.user_id,
                name=topic.name,
                sort_order=topic.sort_order,
                created_at=topic.created_at,
                word_count=count,
            ),
            words=[VocabWordResponse.model_validate(w) for w in words],
        )

    async def bootstrap_starter_pack(self, user_id: int) -> VocabBootstrapResponse:
        """Create sample topics/words when user has none (idempotent)."""
        if await self._repo.count_topics(user_id) > 0:
            return VocabBootstrapResponse(
                created=False,
                topics_created=0,
                words_created=0,
                message="User already has topics",
            )
        topics_created = 0
        words_created = 0
        for pack in STARTER_TOPICS:
            topic = await self._repo.create_topic(user_id, pack["name"], sort_order=topics_created)
            topics_created += 1
            rows = [
                {
                    "word": w["word"],
                    "phonetic": w.get("phonetic"),
                    "word_type": w.get("word_type"),
                    "meaning_en": w.get("meaning_en"),
                    "meaning_vi": w.get("meaning_vi"),
                    "example": w.get("example"),
                    "example_vi": w.get("example_vi"),
                    "mastery": "new",
                    "source_type": "manual",
                }
                for w in pack.get("words", [])
            ]
            await self._repo.create_words_bulk(topic.id, rows)
            words_created += len(rows)
        return VocabBootstrapResponse(
            created=True,
            topics_created=topics_created,
            words_created=words_created,
            message="Starter vocabulary pack created",
        )

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

    async def list_words(self, topic_id: int, user_id: int) -> list[VocabWordResponse]:
        await self._require_owned_topic(topic_id, user_id)
        words = await self._repo.list_words(topic_id)
        return [VocabWordResponse.model_validate(w) for w in words]

    async def create_word(
        self,
        topic_id: int,
        user_id: int,
        data: VocabWordCreate,
    ) -> VocabWordResponse:
        await self._require_owned_topic(topic_id, user_id)
        word_data = data.model_dump(exclude_none=True)
        word_data.setdefault("source_type", "manual")
        word = await self._repo.create_word(topic_id, word_data)
        return VocabWordResponse.model_validate(word)

    async def update_word(
        self,
        topic_id: int,
        word_id: int,
        user_id: int,
        data: VocabWordUpdate,
    ) -> VocabWordResponse:
        await self._require_owned_topic(topic_id, user_id)
        word = await self._require_word(word_id, topic_id)
        updated = await self._repo.update_word(word, data.model_dump(exclude_none=True))
        return VocabWordResponse.model_validate(updated)

    async def delete_word(self, topic_id: int, word_id: int, user_id: int) -> None:
        await self._require_owned_topic(topic_id, user_id)
        word = await self._require_word(word_id, topic_id)
        await self._repo.delete_word(word)

    async def search_words(self, user_id: int, query: str) -> list[VocabWordResponse]:
        query = query.strip()
        if len(query) < 1:
            return []
        words = await self._repo.search_words(user_id, query)
        return [VocabWordResponse.model_validate(w) for w in words]

    async def get_stats(self, user_id: int) -> dict[str, int]:
        return await self._repo.get_user_stats(user_id)

    async def get_study_queue(self, topic_id: int, user_id: int) -> VocabStudyQueueResponse:
        topic = await self._require_owned_topic(topic_id, user_id)
        words = await self._repo.list_study_queue(topic_id)
        due = await self._repo.count_due_words(topic_id)
        count = len(words)
        return VocabStudyQueueResponse(
            topic=VocabTopicResponse(
                id=topic.id,
                user_id=topic.user_id,
                name=topic.name,
                sort_order=topic.sort_order,
                created_at=topic.created_at,
                word_count=count,
            ),
            due_count=due,
            words=[VocabWordResponse.model_validate(w) for w in words],
        )

    async def record_review(
        self, topic_id: int, word_id: int, user_id: int, quality: int
    ) -> VocabWordResponse:
        await self._require_owned_topic(topic_id, user_id)
        word = await self._require_word(word_id, topic_id)
        patch = sm2_apply(
            quality=quality,
            srs_ease=word.srs_ease,
            srs_interval_days=word.srs_interval_days,
            srs_repetitions=word.srs_repetitions,
        )
        updated = await self._repo.update_word(word, patch)
        return VocabWordResponse.model_validate(updated)

    async def generate_reading_passage(
        self, topic_id: int, user_id: int, word_ids: list[int]
    ) -> VocabReadingPassageResponse:
        await self._require_owned_topic(topic_id, user_id)
        rows = []
        for wid in word_ids[:8]:
            w = await self._require_word(wid, topic_id)
            rows.append({
                "word": w.word,
                "meaning_vi": w.meaning_vi or "",
                "meaning_en": w.meaning_en or "",
                "word_id": w.id,
            })
        raw = await ai_reading_passage(rows)
        return VocabReadingPassageResponse(
            paragraphs=raw.get("paragraphs") or [],
            answers=raw.get("answers") or {},
            source=raw.get("source", "ai"),
            word_ids=[r["word_id"] for r in rows],
            comprehension_questions=raw.get("comprehension_questions") or [],
        )

    async def build_mcq_options(self, topic_id: int, user_id: int, word_id: int) -> dict:
        """4-option MCQ using sibling words in topic (no AI required)."""
        await self._require_owned_topic(topic_id, user_id)
        target = await self._require_word(word_id, topic_id)
        all_words = await self._repo.list_words(topic_id)
        distractors = [
            w.meaning_vi for w in all_words
            if w.id != word_id and w.meaning_vi and w.meaning_vi != target.meaning_vi
        ]
        import random
        random.shuffle(distractors)
        options = [{"text": target.meaning_vi, "correct": True}]
        for d in distractors[:3]:
            options.append({"text": d, "correct": False})
        while len(options) < 4:
            options.append({"text": f"(nghĩa khác {len(options)})", "correct": False})
        random.shuffle(options)
        return {"question_id": word_id, "options": options}

    async def complete_study_session(
        self,
        user_id: int,
        topic_id: int,
        duration_seconds: int,
        words_reviewed: int,
    ) -> VocabSessionCompleteResponse:
        """
        Ghi nhận phiên ôn từ vựng: history + progress + streak/XP (10 phút = 1 XP).
        """
        topic = await self._require_owned_topic(topic_id, user_id)
        words = max(0, int(words_reviewed))
        duration = max(0, int(duration_seconds))
        if words < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="words_reviewed must be at least 1",
            )

        db = self._repo._db
        from app.services.badge_service import BadgeService

        badge_svc = BadgeService(db)
        user_rs = await db.execute(select(User).where(User.id == user_id))
        user_row = user_rs.scalar_one_or_none()
        before_unlocked = (
            await badge_svc.get_unlocked_ids(user_row) if user_row else set()
        )

        history_repo = HistoryRepository(db)
        progress_repo = ProgressRepository(db)
        profile_repo = ProfileRepository(db)

        pct = round(min(100.0, (words / max(words, 1)) * 100), 2)
        await history_repo.create(
            user_id=user_id,
            quiz_id=f"vocab:{topic_id}",
            subject="Vocabulary",
            score=words,
            total_questions=words,
            percentage=pct,
            band_score=None,
            mode="vocab",
            duration_seconds=duration,
            answers={"topic_id": topic_id, "topic_name": topic.name},
        )

        existing = await progress_repo.get_by_subject(user_id, "Vocabulary")
        if existing:
            new_total = max(existing.total_questions, words)
            new_completed = min(existing.completed_questions + words, new_total)
        else:
            new_total = words
            new_completed = words
        new_pct = round((new_completed / max(new_total, 1)) * 100, 2)
        await progress_repo.upsert(
            user_id=user_id,
            subject="Vocabulary",
            total_questions=new_total,
            completed_questions=new_completed,
            percentage=min(new_pct, 100.0),
        )

        xp_earned = xp_from_duration(duration)
        profile = await profile_repo.update_streak_and_xp(user_id, xp_to_add=xp_earned)
        from app.core.cache import invalidate_leaderboard_cache

        invalidate_leaderboard_cache()

        from app.services.adaptive_study_service import AdaptiveStudyService

        await AdaptiveStudyService(db).record_activity(
            user_id,
            subject="Vocabulary",
            percentage=pct,
        )

        new_badges = []
        if user_row:
            new_badges = await badge_svc.detect_new_badges(user_row, before_unlocked)

        return VocabSessionCompleteResponse(
            xp_earned=xp_earned,
            total_xp=profile.xp if profile else 0,
            words_reviewed=words,
            duration_seconds=duration,
            new_badges=new_badges,
        )

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
