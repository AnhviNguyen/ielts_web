"""
Translation Practice service — business logic + AI grading.
"""
from __future__ import annotations

import json
import logging
import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.openrouter_client import chat_completion_json, has_openrouter_keys
from app.data.translation_seed import TRANSLATION_SEED
from app.data.translation_seed_v2 import TRANSLATION_SEED_V2, TRANSLATION_EXTRA_TOPICS
from app.repositories.translation_repository import TranslationRepository

logger = logging.getLogger(__name__)

# Thứ tự chương trình IELTS từ thấp → cao (dùng khi seed DB mới)
_FULL_CURRICULUM_ORDER: list[str] = [
    "Band 5.0 — Khởi động",
    "Cấu trúc câu cơ bản",
    "Band 5.5 — Liên từ & Câu ghép",
    "Collocations & Từ vựng học thuật",
    "Band 6.0 — Câu phức & Mệnh đề",
    "Dịch đoạn văn Band 6.5",
    "Band 7.0 — Luận điểm & Phân tích",
    "Dịch đoạn văn Band 8.0",
    "Dịch Essay hoàn chỉnh",
]

_GRADING_SYSTEM = (
    "You are an expert IELTS Writing examiner grading Vietnamese-to-English translations.\n"
    "Grade on three criteria:\n"
    "1. Accuracy (5 pts): How faithfully the meaning is conveyed.\n"
    "2. Grammar (3 pts): Tense, articles, subject-verb agreement, word order.\n"
    "3. Vocabulary (2 pts): Appropriate word choice and collocations.\n\n"
    "IMPORTANT scoring rules:\n"
    "- Accept valid synonyms and paraphrases — the student's answer does NOT need to match "
    "the reference word-for-word if the meaning and structure are equivalent.\n"
    "- Reward natural English alternatives (e.g. 'rapidly' = 'quickly', 'due to' = 'because of').\n"
    "- Only deduct points for meaning errors, grammar mistakes, or unnatural phrasing.\n"
    "- If the answer is correct with different wording, score 8–10.\n\n"
    "Return ONLY valid JSON (no markdown) in this exact shape:\n"
    '{"score": <number 0-10>, '
    '"feedback": "<2-3 sentences of actionable feedback in Vietnamese>", '
    '"correction": "<corrected version of the student translation; if already perfect, repeat it>", '
    '"model_answer": "<ideal English translation of the Vietnamese sentence>"}'
)


class TranslationService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = TranslationRepository(db)
        self._db = db

    # ── Public API ───────────────────────────────────────────────────────────

    async def list_steps_with_counts(self) -> list[dict]:
        steps = await self._repo.list_steps()
        result = []
        for step in steps:
            topics = await self._repo.list_topics_for_step(step.id)
            topic_count = len(topics)
            sentence_count = 0
            for t in topics:
                sentence_count += await self._repo.count_sentences_in_topic(t.id)
            result.append({
                "id": step.id,
                "order": step.order,
                "title": step.title,
                "description": step.description,
                "badge_label": step.badge_label,
                "badge_color": step.badge_color,
                "icon_emoji": step.icon_emoji,
                "topic_count": topic_count,
                "sentence_count": sentence_count,
            })
        return result

    async def list_topics_for_step(self, step_id: int, user_id: int) -> list[dict]:
        step = await self._repo.get_step(step_id)
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found")
        topics = await self._repo.list_topics_for_step(step_id)
        result = []
        for topic in topics:
            sentence_count = await self._repo.count_sentences_in_topic(topic.id)
            completed = await self._repo.count_completed_sentences(user_id, topic.id)
            result.append({
                "id": topic.id,
                "step_id": topic.step_id,
                "order": topic.order,
                "title": topic.title,
                "description": topic.description,
                "sentence_count": sentence_count,
                "completed_count": completed,
            })
        return result

    async def list_sentences_for_topic(self, topic_id: int, user_id: int) -> list[dict]:
        topic = await self._repo.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        sentences = await self._repo.list_sentences_for_topic(topic_id)
        result = []
        for sentence in sentences:
            attempt = await self._repo.get_user_attempt_for_sentence(user_id, sentence.id)
            result.append({
                "id": sentence.id,
                "order": sentence.order,
                "vietnamese": sentence.vietnamese,
                "hint_words": _build_hint_words(sentence.english),
                "explanation": sentence.explanation,
                "last_score": attempt.score if attempt else None,
                "last_attempt": attempt.user_translation if attempt else None,
            })
        return result

    async def check_translation(
        self, user_id: int, sentence_id: int, user_translation: str
    ) -> dict:
        sentence = await self._repo.get_sentence(sentence_id)
        if not sentence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sentence not found")

        user_translation = user_translation.strip()
        if len(user_translation) < 3:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Bản dịch quá ngắn — cần ít nhất 3 ký tự.",
            )

        score, feedback, correction, model_answer = await _grade_with_ai(
            sentence.vietnamese, sentence.english, user_translation
        )

        await self._repo.create_attempt(
            user_id=user_id,
            sentence_id=sentence_id,
            user_translation=user_translation,
            score=score,
            feedback=feedback,
            model_answer=model_answer,
        )
        await self._db.commit()

        return {
            "score": score,
            "feedback": feedback,
            "correction": correction,
            "model_answer": model_answer,
            "reference_english": sentence.english,
        }

    # ── Seed data ────────────────────────────────────────────────────────────

    async def seed_if_empty(self) -> bool:
        """Insert seed data only if translation_steps is empty. Returns True if seeded."""
        count = await self._repo.count_steps()
        if count > 0:
            return False

        logger.info("Seeding translation practice data…")
        curriculum = _build_full_curriculum()
        for step_order, step_data in enumerate(curriculum, start=1):
            await self._insert_step_tree(step_order, step_data)

        await self._db.commit()
        logger.info("Translation seed data inserted successfully.")
        return True

    async def sync_seed_content(self) -> dict[str, int]:
        """Idempotent merge: thêm bước/chủ đề/câu mới từ V2 vào DB hiện có."""
        stats = {"steps": 0, "topics": 0, "sentences": 0}

        step_lookup = _all_steps_by_title()
        next_order = await self._repo.max_step_order()

        for title in _FULL_CURRICULUM_ORDER:
            step_data = step_lookup.get(title)
            if not step_data:
                continue
            step = await self._repo.get_step_by_title(title)
            if not step:
                next_order += 1
                step = await self._insert_step_tree(next_order, step_data)
                stats["steps"] += 1
            else:
                added = await self._sync_topics_for_step(step, step_data)
                stats["topics"] += added["topics"]
                stats["sentences"] += added["sentences"]

        for step_title, extra_topics in TRANSLATION_EXTRA_TOPICS.items():
            step = await self._repo.get_step_by_title(step_title)
            if not step:
                continue
            for topic_data in extra_topics:
                added = await self._sync_single_topic(step.id, topic_data)
                stats["topics"] += added["topics"]
                stats["sentences"] += added["sentences"]

        if any(stats.values()):
            await self._db.commit()
            logger.info(
                "Translation sync: +%d steps, +%d topics, +%d sentences.",
                stats["steps"],
                stats["topics"],
                stats["sentences"],
            )
        return stats

    async def _insert_step_tree(self, step_order: int, step_data: dict):
        step = await self._repo.create_step(
            order=step_order,
            title=step_data["title"],
            description=step_data["description"],
            badge_label=step_data.get("badge_label"),
            badge_color=step_data.get("badge_color", "gray"),
            icon_emoji=step_data.get("icon_emoji", "📝"),
        )
        for topic_order, topic_data in enumerate(step_data["topics"], start=1):
            await self._insert_topic_tree(step.id, topic_order, topic_data)
        return step

    async def _insert_topic_tree(
        self, step_id: int, topic_order: int, topic_data: dict
    ) -> None:
        topic = await self._repo.create_topic(
            step_id=step_id,
            order=topic_order,
            title=topic_data["title"],
            description=topic_data.get("description", ""),
        )
        for sent_order, sent_data in enumerate(topic_data["sentences"], start=1):
            await self._repo.create_sentence(
                topic_id=topic.id,
                order=sent_order,
                vietnamese=sent_data["vi"],
                english=sent_data["en"],
                explanation=sent_data.get("explain"),
            )

    async def _sync_topics_for_step(self, step, step_data: dict) -> dict[str, int]:
        added = {"topics": 0, "sentences": 0}
        for topic_data in step_data["topics"]:
            result = await self._sync_single_topic(step.id, topic_data)
            added["topics"] += result["topics"]
            added["sentences"] += result["sentences"]
        return added

    async def _sync_single_topic(self, step_id: int, topic_data: dict) -> dict[str, int]:
        added = {"topics": 0, "sentences": 0}
        topic = await self._repo.get_topic_by_title(step_id, topic_data["title"])
        if not topic:
            topic_count = await self._repo.count_topics_in_step(step_id)
            topic = await self._repo.create_topic(
                step_id=step_id,
                order=topic_count + 1,
                title=topic_data["title"],
                description=topic_data.get("description", ""),
            )
            added["topics"] += 1

        for sent_data in topic_data["sentences"]:
            if await self._repo.sentence_exists(topic.id, sent_data["vi"]):
                continue
            sent_count = await self._repo.count_sentences_in_topic(topic.id)
            await self._repo.create_sentence(
                topic_id=topic.id,
                order=sent_count + 1,
                vietnamese=sent_data["vi"],
                english=sent_data["en"],
                explanation=sent_data.get("explain"),
            )
            added["sentences"] += 1
        return added


# ── Pure helpers ─────────────────────────────────────────────────────────────

def _all_steps_by_title() -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for step in TRANSLATION_SEED + TRANSLATION_SEED_V2:
        lookup[step["title"]] = step
    return lookup


def _merge_extra_topics(step_data: dict) -> dict:
    """Gắn thêm chủ đề bổ sung vào bước (nếu có trong TRANSLATION_EXTRA_TOPICS)."""
    extras = TRANSLATION_EXTRA_TOPICS.get(step_data["title"], [])
    if not extras:
        return step_data
    merged = dict(step_data)
    merged["topics"] = list(step_data["topics"]) + list(extras)
    return merged


def _build_full_curriculum() -> list[dict]:
    """Chương trình đầy đủ theo thứ tự Band 5.0 → 8.0+ cho DB mới."""
    lookup = _all_steps_by_title()
    return [_merge_extra_topics(lookup[title]) for title in _FULL_CURRICULUM_ORDER if title in lookup]


def _build_hint_words(english: str) -> list[dict]:
    """Convert an English sentence into masked hint tokens."""
    tokens = english.split()
    hints = []
    for token in tokens:
        # Separate leading/trailing punctuation from the core word
        m = re.match(r'^([^a-zA-Z]*)([a-zA-Z\']+)([^a-zA-Z]*)$', token)
        if m:
            prefix, core, suffix = m.groups()
            masked = core[0] + '*' * (len(core) - 1) if len(core) > 1 else core
            hints.append({
                "raw": token,
                "masked": prefix + masked + suffix,
                "core": core,
            })
        else:
            hints.append({"raw": token, "masked": token, "core": token})
    return hints


async def _grade_with_ai(
    vietnamese: str, reference_english: str, user_translation: str
) -> tuple[float, str, str, str]:
    """Call OpenRouter to grade the translation. Returns (score, feedback, correction, model_answer)."""
    if not has_openrouter_keys():
        score, feedback, model_answer = _fallback_grade(reference_english, user_translation)
        return score, feedback, user_translation, model_answer

    user_prompt = (
        f"Vietnamese sentence: {vietnamese}\n"
        f"Reference answer (one valid translation, NOT the only correct answer): {reference_english}\n"
        f"Student's translation: {user_translation}\n\n"
        "Grade the student's translation. Accept synonyms and equivalent phrasing. Return JSON only."
    )
    messages = [
        {"role": "system", "content": _GRADING_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    try:
        data, _model = await chat_completion_json(
            messages,
            max_tokens=500,
            temperature=0.25,
            timeout=25.0,
            title="Translation Grader",
        )
        score = max(0.0, min(10.0, float(data.get("score", 5.0))))
        feedback = str(data.get("feedback", ""))
        correction = str(data.get("correction") or user_translation)
        model_answer = str(data.get("model_answer", reference_english))
        return score, feedback, correction, model_answer
    except Exception as exc:
        logger.warning("AI grading failed (%s); using fallback.", exc)
        score, feedback, model_answer = _fallback_grade(reference_english, user_translation)
        return score, feedback, user_translation, model_answer


def _fallback_grade(reference: str, user_translation: str) -> tuple[float, str, str]:
    """Simple word-overlap fallback when AI is unavailable."""
    ref_words = set(re.findall(r'[a-zA-Z]+', reference.lower()))
    usr_words = set(re.findall(r'[a-zA-Z]+', user_translation.lower()))
    if not ref_words:
        return 5.0, "Không thể chấm điểm tự động.", reference
    overlap = len(ref_words & usr_words) / len(ref_words)
    score = round(overlap * 10, 1)
    feedback = (
        "Bản dịch có độ trùng khớp từ vựng với đáp án mẫu. "
        "Hãy so sánh với đáp án mẫu để cải thiện ngữ pháp và diễn đạt."
    )
    return score, feedback, reference
