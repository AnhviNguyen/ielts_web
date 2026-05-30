"""Writing submit + AI band evaluation."""

from __future__ import annotations

import json
import logging
import re

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.xp import xp_from_duration
from app.db.models import User
from app.repositories.profile_repository import ProfileRepository
from app.schemas import HistorySave, WritingSubmitRequest, WritingSubmitResponse
from app.services.history_service import HistoryService
from app.services.mock_data_service import MockDataService

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_EVAL_SYSTEM = (
    "You are an expert IELTS Writing examiner. Score the essay using IELTS Task 1 or Task 2 criteria. "
    "Respond with ONLY valid JSON (no markdown) using this schema:\n"
    '{"overall_band": number, "task_achievement": number, "coherence_cohesion": number, '
    '"lexical_resource": number, "grammar_accuracy": number, '
    '"word_count_comment": string, "strengths": [string], "improvements": [string], "summary": string}\n'
    "Bands are 0-9 in 0.5 steps. Be strict but fair."
)


class WritingService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._profile_repo = ProfileRepository(db)
        self._history = HistoryService(db)
        self._mock = MockDataService.default()

    async def submit(
        self,
        user: User,
        payload: WritingSubmitRequest,
    ) -> WritingSubmitResponse:
        await self._profile_repo.ensure_writing_submit_allowed(user.id)

        essay = (payload.essay_text or "").strip()
        if len(essay.split()) < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bài viết quá ngắn (tối thiểu ~20 từ).",
            )

        prompt_text = payload.prompt_text or ""
        if not prompt_text and payload.topic_id:
            raw = self._mock.get_writing_topic_detail(payload.topic_id)
            if raw and raw.get("code") == 0:
                data = raw.get("data") or {}
                q0 = (data.get("questions") or [{}])[0]
                prompt_text = q0.get("content_writing") or q0.get("title") or data.get("title") or ""

        evaluation = await self._evaluate_essay(
            task_type=payload.task_type,
            prompt_text=prompt_text,
            essay_text=essay,
            word_count=payload.word_count,
        )

        band = float(evaluation.get("overall_band") or 0)
        band = max(0.0, min(9.0, round(band * 2) / 2))
        duration = payload.duration_seconds or 0
        quiz_id = str(payload.topic_id)

        from app.services.badge_service import BadgeService

        before_unlocked = await BadgeService(self._db).get_unlocked_ids(user)

        history_payload = HistorySave(
            quiz_id=quiz_id,
            subject="Writing",
            score=int(round(band * 10)),
            total_questions=90,
            percentage=round((band / 9) * 100, 2),
            band_score=band,
            mode="practice",
            duration_seconds=duration,
            answers={
                "topic_id": payload.topic_id,
                "task_type": payload.task_type,
                "essay_text": essay,
                "word_count": payload.word_count,
                "evaluation": evaluation,
            },
        )
        history_row = await self._history.save_practice_result(user, history_payload)
        await self._profile_repo.increment_writing_submit(user.id)

        xp_earned = xp_from_duration(duration)
        new_badges = await BadgeService(self._db).detect_new_badges(user, before_unlocked)
        return WritingSubmitResponse(
            history_id=history_row.id,
            band_score=band,
            xp_earned=xp_earned,
            evaluation=evaluation,
            message="Đã lưu bài Writing và chấm điểm AI.",
            new_badges=new_badges,
        )

    async def _evaluate_essay(
        self,
        *,
        task_type: int,
        prompt_text: str,
        essay_text: str,
        word_count: int,
    ) -> dict:
        if not settings.OPENROUTER_API_KEY:
            return _fallback_evaluation(task_type, word_count)

        user_prompt = (
            f"Task type: {'Task 1' if task_type == 1 else 'Task 2'}\n"
            f"Minimum words: {150 if task_type == 1 else 250}\n"
            f"Student word count: {word_count}\n\n"
            f"TASK PROMPT:\n{prompt_text[:4000]}\n\n"
            f"STUDENT ESSAY:\n{essay_text[:12000]}"
        )
        payload = {
            "model": settings.OPENROUTER_FAST_MODEL,
            "messages": [
                {"role": "system", "content": _EVAL_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.FRONTEND_ORIGIN,
            "X-Title": "LinguaIELTS Writing Eval",
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
                resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = _parse_json(content)
            if parsed:
                return parsed
        except Exception as exc:
            logger.warning("Writing AI evaluation failed: %s", exc)

        return _fallback_evaluation(task_type, word_count)


def _parse_json(text: str) -> dict | None:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _fallback_evaluation(task_type: int, word_count: int) -> dict:
    min_w = 150 if task_type == 1 else 250
    wc_ratio = min(1.0, word_count / max(min_w, 1))
    band = round(5.0 + wc_ratio * 1.5, 1)
    band = min(6.5, band)
    return {
        "overall_band": band,
        "task_achievement": band,
        "coherence_cohesion": band,
        "lexical_resource": band - 0.5,
        "grammar_accuracy": band - 0.5,
        "word_count_comment": f"~{word_count} từ (mục tiêu {min_w}+).",
        "strengths": ["Bài đã được lưu thành công."],
        "improvements": ["Bật OPENROUTER_API_KEY để nhận phản hồi AI chi tiết."],
        "summary": "Chấm điểm ước lượng (AI không khả dụng).",
        "llm_generated": False,
    }
