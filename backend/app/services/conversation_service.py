"""Conversation Practice — role-play sessions with AI + language feedback."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.openrouter_client import chat_completion, chat_completion_json, has_openrouter_keys
from app.data.conversation_seed import CONVERSATION_SEED
from app.repositories.conversation_repository import ConversationRepository
from app.services.speaking_ai_helpers import _call_language_cards, _normalize_grammar_analysis, _normalize_vocabulary_analysis

logger = logging.getLogger(__name__)

_TURN_ANALYSIS_SYSTEM = (
    "You are an IELTS Speaking coach reviewing ONE student utterance in a role-play.\n"
    "Return ONLY valid JSON:\n"
    '{"grammar_note":"<1 short tip in Vietnamese if error found, else empty string>",'
    '"vocab_tip":"<1 useful word/phrase suggestion in Vietnamese, else empty string>",'
    '"used_vocab":["<words from suggested vocabulary list that student used>"]}'
)

_END_FEEDBACK_SYSTEM = (
    "You are an IELTS Speaking coach. Summarize a completed role-play conversation.\n"
    "Return ONLY valid JSON in Vietnamese for feedback fields:\n"
    '{"summary":"<2-3 sentences overall feedback in Vietnamese>",'
    '"strengths":["<strength 1>","<strength 2>"],'
    '"improvements":["<area 1>","<area 2>"],'
    '"next_steps":["<actionable tip 1>","<actionable tip 2>"]}'
)

_HINT_SYSTEM = (
    "You help an English learner reply in a role-play conversation.\n"
    "Return ONLY valid JSON:\n"
    '{"hint_vi":"<1-2 sentences in Vietnamese explaining what to say next>",'
    '"example_reply":"<natural English reply, 1-3 sentences>",'
    '"key_phrases":["<useful phrase 1>","<useful phrase 2>"]}'
)


class ConversationService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ConversationRepository(db)
        self._db = db

    async def list_topics(self, level: str | None = None) -> list[dict]:
        topics = await self._repo.list_topics(level, active_only=True)
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "level": t.level,
                "icon_emoji": t.icon_emoji,
                "ai_role": t.ai_role,
                "user_role": t.user_role,
                "vocabulary": t.vocabulary or [],
            }
            for t in topics
        ]

    async def start_session(self, user_id: int, topic_id: int) -> dict:
        topic = await self._repo.get_topic(topic_id)
        if not topic or not topic.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        session = await self._repo.create_session(user_id, topic_id, topic.opening_line)
        await self._db.commit()

        return {
            "session_id": session.id,
            "topic_id": topic.id,
            "topic": topic.title,
            "level": topic.level,
            "ai_role": topic.ai_role,
            "user_role": topic.user_role,
            "opening_line": topic.opening_line,
            "vocabulary": topic.vocabulary or [],
        }

    async def process_turn(
        self,
        user_id: int,
        session_id: int,
        user_message: str,
        *,
        pronunciation: dict[str, Any] | None = None,
    ) -> dict:
        session = await self._repo.get_session_for_user(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already completed")

        topic = await self._repo.get_topic(session.topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        user_message = user_message.strip()
        if len(user_message) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message too short — please say at least a few words.",
            )

        history: list[dict] = list(session.history or [])
        user_turn: dict[str, Any] = {
            "role": "user",
            "content": user_message,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

        analysis, grammar_vocab = await asyncio.gather(
            _analyze_turn_light(user_message, topic.vocabulary or []),
            _analyze_grammar_vocab(topic.scenario, user_message),
        )
        user_turn["analysis"] = analysis
        user_turn["grammar"] = grammar_vocab.get("grammar_analysis")
        user_turn["vocabulary"] = grammar_vocab.get("vocabulary_analysis")
        if pronunciation:
            user_turn["pronunciation"] = pronunciation

        history.append(user_turn)

        ai_reply = await _call_roleplay_ai(topic, history)
        history.append({
            "role": "assistant",
            "content": ai_reply,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        await self._repo.update_session_history(session, history)
        await self._db.commit()

        turn_count = len([h for h in history if h.get("role") == "user"])
        return {
            "session_id": session_id,
            "ai_reply": ai_reply,
            "turn_count": turn_count,
            "analysis": analysis,
            "grammar": user_turn["grammar"],
            "vocabulary": user_turn["vocabulary"],
            "pronunciation": pronunciation,
        }

    async def end_session(self, user_id: int, session_id: int) -> dict:
        session = await self._repo.get_session_for_user(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        topic = await self._repo.get_topic(session.topic_id)
        history = list(session.history or [])
        user_turns = [h for h in history if h.get("role") == "user"]
        turn_count = len(user_turns)

        pron_scores = [
            h["pronunciation"]["total"]
            for h in user_turns
            if isinstance(h.get("pronunciation"), dict) and h["pronunciation"].get("total") is not None
        ]
        avg_pron = round(sum(pron_scores) / len(pron_scores), 1) if pron_scores else None

        grammar_scores = [
            h["grammar"]["score"]
            for h in user_turns
            if isinstance(h.get("grammar"), dict) and h["grammar"].get("score") is not None
        ]
        vocab_scores = [
            h["vocabulary"]["score"]
            for h in user_turns
            if isinstance(h.get("vocabulary"), dict) and h["vocabulary"].get("score") is not None
        ]
        avg_grammar = round(sum(grammar_scores) / len(grammar_scores), 1) if grammar_scores else None
        avg_vocab = round(sum(vocab_scores) / len(vocab_scores), 1) if vocab_scores else None

        transcript = "\n".join(f"Student: {h['content']}" for h in user_turns)
        summary = await _build_end_feedback(topic, transcript, turn_count)

        feedback = {
            **summary,
            "turn_count": turn_count,
            "scores": {
                "grammar": avg_grammar,
                "vocabulary": avg_vocab,
                "pronunciation": avg_pron,
            },
        }

        if session.status == "active":
            await self._repo.complete_session(session, feedback)
            await self._db.commit()

        return {
            "session_id": session_id,
            "turn_count": turn_count,
            "feedback": feedback,
            "message": "Great practice! You completed the conversation.",
        }

    async def seed_if_empty(self) -> bool:
        if await self._repo.count_topics() > 0:
            return False
        logger.info("Seeding conversation topics…")
        for order, data in enumerate(CONVERSATION_SEED, start=1):
            await self._repo.create_topic(order, data)
        await self._db.commit()
        logger.info("Conversation seed inserted (%d topics).", len(CONVERSATION_SEED))
        return True

    async def sync_seed(self) -> int:
        added = 0
        for order, data in enumerate(CONVERSATION_SEED, start=1):
            existing = await self._repo.get_topic_by_title(data["title"])
            if existing:
                continue
            await self._repo.create_topic(order, data)
            added += 1
        if added:
            await self._db.commit()
            logger.info("Conversation sync: +%d topics.", added)
        return added

    async def get_reply_hint(
        self, user_id: int, session_id: int, ai_message: str
    ) -> dict:
        session = await self._repo.get_session_for_user(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        topic = await self._repo.get_topic(session.topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        ai_message = ai_message.strip()
        if len(ai_message) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="AI message too short.",
            )

        return await _build_reply_hint(topic, ai_message)

    async def translate_message(self, text: str) -> dict:
        from app.services.translate_service import translate_text

        text = text.strip()
        if len(text) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Text too short to translate.",
            )
        translation = await translate_text(text, from_lang="en", to_lang="vi")
        return {"translation": translation or ""}


def _build_system_prompt(topic) -> str:
    return f"""You are {topic.ai_role}.
The user is {topic.user_role}.
Scenario: {topic.scenario}

Rules:
- Stay strictly in character at all times.
- Keep replies short (2-3 sentences max) — this is a spoken conversation practice.
- If the user makes a grammar mistake, continue naturally but subtly use the correct form in your reply.
- Speak in English only. Do NOT switch to Vietnamese.
- Do NOT break character to explain grammar unless the user explicitly asks.
- End with a question or prompt to keep the conversation going when appropriate."""


def _history_to_messages(history: list[dict]) -> list[dict]:
    return [
        {"role": h["role"], "content": h["content"]}
        for h in history
        if h.get("role") in ("user", "assistant") and h.get("content")
    ]


async def _call_roleplay_ai(topic, history: list[dict]) -> str:
    if not has_openrouter_keys():
        return "That's interesting! Could you tell me more about that?"

    messages = [{"role": "system", "content": _build_system_prompt(topic)}]
    messages.extend(_history_to_messages(history))

    try:
        content, _model = await chat_completion(
            messages,
            max_tokens=256,
            temperature=0.7,
            timeout=30.0,
            title="Conversation Role-play",
        )
        return content.strip() or "I see — please go on."
    except Exception as exc:
        logger.warning("Role-play AI failed: %s", exc)
        return "Thanks for sharing! What would you like to do next?"


async def _analyze_turn_light(text: str, vocabulary: list[str]) -> dict:
    if not has_openrouter_keys() or not text.strip():
        return {"grammar_note": "", "vocab_tip": "", "used_vocab": []}

    vocab_str = ", ".join(vocabulary[:12]) if vocabulary else "(none)"
    user_prompt = (
        f"Student said: \"{text}\"\n"
        f"Suggested vocabulary for this scenario: {vocab_str}\n"
        "Return JSON only."
    )
    try:
        data, _ = await chat_completion_json(
            [
                {"role": "system", "content": _TURN_ANALYSIS_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=200,
            temperature=0.2,
            timeout=20.0,
            title="Conversation Turn Analysis",
        )
        return {
            "grammar_note": str(data.get("grammar_note", "")),
            "vocab_tip": str(data.get("vocab_tip", "")),
            "used_vocab": list(data.get("used_vocab") or []),
        }
    except Exception as exc:
        logger.warning("Turn analysis failed: %s", exc)
        return {"grammar_note": "", "vocab_tip": "", "used_vocab": []}


async def _analyze_grammar_vocab(scenario: str, text: str) -> dict:
    if not text.strip():
        return {"grammar_analysis": {"score": 0, "errors": []}, "vocabulary_analysis": {"score": 0, "weak_words": [], "strong_words": [], "replacements": []}}
    try:
        raw = await _call_language_cards(scenario, text)
        return {
            "grammar_analysis": _normalize_grammar_analysis(raw.get("grammar_analysis")),
            "vocabulary_analysis": _normalize_vocabulary_analysis(raw.get("vocabulary_analysis")),
        }
    except Exception as exc:
        logger.warning("Grammar/vocab analysis failed: %s", exc)
        return {
            "grammar_analysis": {"score": 0, "errors": []},
            "vocabulary_analysis": {"score": 0, "weak_words": [], "strong_words": [], "replacements": []},
        }


async def _build_reply_hint(topic, ai_message: str) -> dict:
    fallback = {
        "hint_vi": "Hãy trả lời tự nhiên bằng tiếng Anh, giữ đúng vai trong tình huống.",
        "example_reply": "Sure, I'd like to know more about that.",
        "key_phrases": [],
    }
    if not has_openrouter_keys():
        return fallback

    vocab_str = ", ".join((topic.vocabulary or [])[:10])
    user_prompt = (
        f"Scenario: {topic.title}\n"
        f"Student role: {topic.user_role}\n"
        f"AI role: {topic.ai_role}\n"
        f"Context: {topic.scenario}\n"
        f"Suggested vocabulary: {vocab_str or '(none)'}\n"
        f"AI just said: \"{ai_message}\"\n\n"
        "Suggest how the student should reply next."
    )
    try:
        data, _ = await chat_completion_json(
            [
                {"role": "system", "content": _HINT_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.4,
            timeout=25.0,
            title="Conversation Hint",
        )
        return {
            "hint_vi": str(data.get("hint_vi") or fallback["hint_vi"]),
            "example_reply": str(data.get("example_reply") or fallback["example_reply"]),
            "key_phrases": list(data.get("key_phrases") or []),
        }
    except Exception as exc:
        logger.warning("Reply hint failed: %s", exc)
        return fallback


async def _build_end_feedback(topic, transcript: str, turn_count: int) -> dict:
    fallback = {
        "summary": f"Bạn đã hoàn thành {turn_count} lượt hội thoại trong chủ đề «{topic.title}». Hãy luyện tập thêm để tự tin hơn!",
        "strengths": ["Tham gia đủ số lượt trao đổi"],
        "improvements": ["Mở rộng câu trả lời dài hơn 2-3 câu"],
        "next_steps": ["Thử lại scenario ở level cao hơn", "Ghi âm và nghe lại phát âm của bạn"],
    }
    if not has_openrouter_keys() or not transcript.strip():
        return fallback

    user_prompt = (
        f"Scenario: {topic.title} — {topic.scenario}\n"
        f"Student turns ({turn_count}):\n{transcript}\n\n"
        "Write feedback in Vietnamese."
    )
    try:
        data, _ = await chat_completion_json(
            [
                {"role": "system", "content": _END_FEEDBACK_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.3,
            timeout=30.0,
            title="Conversation End Feedback",
        )
        return {
            "summary": str(data.get("summary") or fallback["summary"]),
            "strengths": list(data.get("strengths") or fallback["strengths"]),
            "improvements": list(data.get("improvements") or fallback["improvements"]),
            "next_steps": list(data.get("next_steps") or fallback["next_steps"]),
        }
    except Exception as exc:
        logger.warning("End feedback failed: %s", exc)
        return fallback


async def score_pronunciation_from_wav(wav_path: str) -> dict[str, Any]:
    """Run pronunciation model on wav file (blocking → thread)."""
    from app.services.speaking_audio_utils import load_audio_16k, run_pronunciation

    def _run() -> dict[str, Any]:
        audio = load_audio_16k(wav_path)
        result = run_pronunciation(audio)
        if result.get("_silent"):
            return {"accuracy": 0.0, "fluency": 0.0, "prosodic": 0.0, "total": 0.0, "silent": True}
        total = float(result.get("total", 0.0))
        return {
            "accuracy": round(float(result.get("accuracy", 0.0)), 1),
            "fluency": round(float(result.get("fluency", 0.0)), 1),
            "prosodic": round(float(result.get("prosodic", 0.0)), 1),
            "total": round(total, 1),
        }

    return await asyncio.to_thread(_run)
