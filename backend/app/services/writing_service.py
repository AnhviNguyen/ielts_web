"""Writing submit + AI band evaluation."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user_ai_client import (
    UserAISettings,
    ai_chat_completion_json,
    has_user_ai_available,
    load_user_ai,
)
from app.core.xp import xp_from_duration
from app.db.models import User
from app.repositories.profile_repository import ProfileRepository
from app.schemas import HistorySave, WritingSubmitRequest, WritingSubmitResponse
from app.services.history_service import HistoryService
from app.services.mock_data_service import MockDataService

logger = logging.getLogger(__name__)

_EVAL_SYSTEM = (
    "You are an expert IELTS Writing examiner. Score the essay using official IELTS Task 1 or Task 2 criteria. "
    "Write all feedback text in Vietnamese (keep quoted essay excerpts in English). "
    "Respond with ONLY valid JSON (no markdown) using this schema:\n"
    "{"
    '"overall_band": number, '
    '"task_achievement": number, '
    '"coherence_cohesion": number, '
    '"lexical_resource": number, '
    '"grammar_accuracy": number, '
    '"task_relevance": "fully_on_topic|partially_on_topic|off_topic|unrelated", '
    '"word_count_comment": string, '
    '"strengths": [string], '
    '"improvements": [string], '
    '"summary": string, '
    '"grammar": {'
    '"band": number, '
    '"errors": [{"original": string, "correction": string, "rule": string, "severity": "minor|major"}], '
    '"tips": [string]'
    "}, "
    '"vocabulary": {'
    '"band": number, '
    '"weak_words": [{"word": string, "better": string, "reason": string}], '
    '"upgrades": [string], '
    '"tips": [string]'
    "}, "
    '"paragraph_allocation": {'
    '"structure_ok": boolean, '
    '"sections": [{"name": string, "recommended_words": string, "your_words": number, "feedback": string}], '
    '"tips": [string]'
    "}, "
    '"model_paragraph": {'
    '"focus": string, '
    '"weak_excerpt": string, '
    '"improved_text": string, '
    '"explanation": string, '
    '"expected_band_gain": string'
    "}"
    "}\n"
    "CRITICAL RULES:\n"
    "1. Read TASK PROMPT first. The essay MUST address that exact task (topic, question, chart/report type).\n"
    "2. task_relevance: fully_on_topic = directly answers the prompt; partially_on_topic = vague or incomplete; "
    "off_topic = wrong angle; unrelated = completely different subject.\n"
    "3. If unrelated or off_topic: task_achievement <= 3.0, overall_band <= 4.0 (do NOT reward grammar/vocabulary).\n"
    "4. If partially_on_topic: task_achievement <= 5.0.\n"
    "5. Bands 0-9 in 0.5 steps; be strict but fair; list up to 5 grammar errors and 5 weak words.\n"
    "6. paragraph_allocation must cover intro/body/conclusion (Task 2) or overview/details (Task 1).\n"
    "7. model_paragraph must rewrite one weak paragraph from the student's essay that relates to the TASK PROMPT; "
    "if essay is off_topic/unrelated, explain that in model_paragraph.explanation instead of inventing a high-band sample."
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
                prompt_text = (
                    q0.get("content_writing")
                    or q0.get("title")
                    or data.get("title")
                    or data.get("prompt_text")
                    or ""
                )

        ai = load_user_ai(await self._profile_repo.get_by_user_id(user.id))
        if not has_user_ai_available(ai):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chưa cấu hình OpenRouter API key trong Profile.",
            )

        evaluation = await self._evaluate_essay(
            task_type=payload.task_type,
            prompt_text=prompt_text,
            essay_text=essay,
            word_count=payload.word_count,
            ai=ai,
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

    async def get_result(self, user: User, history_id: int) -> dict:
        from app.repositories.history_repository import HistoryRepository

        row = await HistoryRepository(self._db).get_by_id_for_user(history_id, user.id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài Writing.")
        if (row.subject or "").lower() != "writing":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không phải bài Writing.")

        answers = row.answers if isinstance(row.answers, dict) else {}
        evaluation = answers.get("evaluation") if isinstance(answers.get("evaluation"), dict) else {}
        topic_title = ""
        if row.quiz_id:
            try:
                title = self._mock.get_writing_topic_detail(int(row.quiz_id))
                if title and title.get("code") == 0:
                    data = title.get("data") or {}
                    q0 = (data.get("questions") or [{}])[0]
                    topic_title = q0.get("title") or data.get("title") or ""
            except (TypeError, ValueError):
                pass

        return {
            "history_id": row.id,
            "band_score": row.band_score,
            "topic_id": answers.get("topic_id"),
            "task_type": answers.get("task_type"),
            "word_count": answers.get("word_count"),
            "essay_text": answers.get("essay_text") or "",
            "evaluation": evaluation,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            "duration_seconds": row.duration_seconds,
            "title": topic_title or "IELTS Writing",
        }

    async def _evaluate_essay(
        self,
        *,
        task_type: int,
        prompt_text: str,
        essay_text: str,
        word_count: int,
        ai: UserAISettings | None = None,
    ) -> dict:
        if not prompt_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không tìm thấy đề bài — không thể chấm AI.",
            )

        user_prompt = (
            f"Task type: {'Task 1' if task_type == 1 else 'Task 2'}\n"
            f"Minimum words: {150 if task_type == 1 else 250}\n"
            f"Student word count: {word_count}\n\n"
            f"=== TASK PROMPT (read this carefully before scoring) ===\n"
            f"{prompt_text[:6000]}\n\n"
            f"=== STUDENT ESSAY (check if it answers the TASK PROMPT above) ===\n"
            f"{essay_text[:12000]}"
        )
        messages = [
            {"role": "system", "content": _EVAL_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]
        try:
            parsed, _model = await ai_chat_completion_json(
                messages,
                ai=ai,
                max_tokens=2800,
                temperature=0.2,
                timeout=90.0,
                title="LinguaIELTS Writing Eval",
            )
            if parsed:
                return _normalize_evaluation(parsed, task_type, word_count, llm_generated=True)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Writing AI evaluation failed: %s", exc)
            raise HTTPException(
                status_code=_ai_error_status(exc),
                detail=_ai_error_detail(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI không trả về kết quả chấm bài. Thử lại sau.",
        )


def _ai_error_status(exc: Exception) -> int:
    msg = str(exc).lower()
    if "429" in msg or "too many requests" in msg or "resource exhausted" in msg:
        return status.HTTP_429_TOO_MANY_REQUESTS
    if "401" in msg or "403" in msg or "invalid api key" in msg:
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_502_BAD_GATEWAY


def _ai_error_detail(exc: Exception) -> str:
    msg = str(exc).lower()
    if "429" in msg or "too many requests" in msg or "resource exhausted" in msg:
        return (
            "OpenRouter API key đã vượt giới hạn request (429). "
            "Đợi 1–2 phút, kiểm tra credit tại openrouter.ai, hoặc thay key."
        )
    if "401" in msg or "403" in msg or "invalid" in msg and "key" in msg:
        return "OpenRouter API key không hợp lệ hoặc hết credit. Kiểm tra lại tại openrouter.ai/keys."
    return "Không thể chấm bài AI. Kiểm tra API key trong Profile hoặc thử lại."


def _clamp_band(value: object, default: float = 5.0) -> float:
    try:
        band = float(value)
    except (TypeError, ValueError):
        band = default
    return max(0.0, min(9.0, round(band * 2) / 2))


def _normalize_evaluation(
    raw: dict,
    task_type: int,
    word_count: int,
    *,
    llm_generated: bool,
) -> dict:
    min_w = 150 if task_type == 1 else 250
    overall = _clamp_band(raw.get("overall_band"))
    ta = _clamp_band(raw.get("task_achievement"), overall)
    cc = _clamp_band(raw.get("coherence_cohesion"), overall)
    lr = _clamp_band(raw.get("lexical_resource"), overall)
    gra = _clamp_band(raw.get("grammar_accuracy"), overall)

    relevance = str(raw.get("task_relevance") or "").strip().lower()
    if relevance in {"unrelated", "off_topic"}:
        ta = min(ta, 3.0)
        cc = min(cc, 5.0)
        lr = min(lr, 5.0)
        gra = min(gra, 5.0)
    elif relevance == "partially_on_topic":
        ta = min(ta, 5.0)

    avg = (ta + cc + lr + gra) / 4
    overall = _clamp_band(avg)
    if relevance in {"unrelated", "off_topic"}:
        overall = min(overall, 4.0)

    grammar = raw.get("grammar") if isinstance(raw.get("grammar"), dict) else {}
    vocabulary = raw.get("vocabulary") if isinstance(raw.get("vocabulary"), dict) else {}
    allocation = raw.get("paragraph_allocation") if isinstance(raw.get("paragraph_allocation"), dict) else {}
    model_para = raw.get("model_paragraph") if isinstance(raw.get("model_paragraph"), dict) else {}

    return {
        "overall_band": overall,
        "task_achievement": ta,
        "coherence_cohesion": cc,
        "lexical_resource": lr,
        "grammar_accuracy": gra,
        "task_relevance": relevance or "fully_on_topic",
        "word_count_comment": str(raw.get("word_count_comment") or f"~{word_count} từ (mục tiêu {min_w}+)."),
        "strengths": [str(s) for s in (raw.get("strengths") or []) if s][:6],
        "improvements": [str(s) for s in (raw.get("improvements") or []) if s][:6],
        "summary": str(raw.get("summary") or ""),
        "grammar": {
            "band": _clamp_band(grammar.get("band"), gra),
            "errors": [
                {
                    "original": str(e.get("original") or ""),
                    "correction": str(e.get("correction") or ""),
                    "rule": str(e.get("rule") or ""),
                    "severity": str(e.get("severity") or "minor"),
                }
                for e in (grammar.get("errors") or [])
                if isinstance(e, dict) and (e.get("original") or e.get("correction"))
            ][:5],
            "tips": [str(t) for t in (grammar.get("tips") or []) if t][:4],
        },
        "vocabulary": {
            "band": _clamp_band(vocabulary.get("band"), lr),
            "weak_words": [
                {
                    "word": str(w.get("word") or ""),
                    "better": str(w.get("better") or ""),
                    "reason": str(w.get("reason") or ""),
                }
                for w in (vocabulary.get("weak_words") or [])
                if isinstance(w, dict) and w.get("word")
            ][:5],
            "upgrades": [str(u) for u in (vocabulary.get("upgrades") or []) if u][:4],
            "tips": [str(t) for t in (vocabulary.get("tips") or []) if t][:4],
        },
        "paragraph_allocation": {
            "structure_ok": bool(allocation.get("structure_ok")),
            "sections": [
                {
                    "name": str(s.get("name") or ""),
                    "recommended_words": str(s.get("recommended_words") or ""),
                    "your_words": int(s.get("your_words") or 0),
                    "feedback": str(s.get("feedback") or ""),
                }
                for s in (allocation.get("sections") or [])
                if isinstance(s, dict) and s.get("name")
            ],
            "tips": [str(t) for t in (allocation.get("tips") or []) if t][:4],
        },
        "model_paragraph": {
            "focus": str(model_para.get("focus") or ""),
            "weak_excerpt": str(model_para.get("weak_excerpt") or ""),
            "improved_text": str(model_para.get("improved_text") or ""),
            "explanation": str(model_para.get("explanation") or ""),
            "expected_band_gain": str(model_para.get("expected_band_gain") or ""),
        },
        "llm_generated": llm_generated,
    }


def _fallback_evaluation(task_type: int, word_count: int) -> dict:
    min_w = 150 if task_type == 1 else 250
    wc_ratio = min(1.0, word_count / max(min_w, 1))
    band = round(5.0 + wc_ratio * 1.5, 1)
    band = min(6.5, band)
    sections = (
        [
            {"name": "Overview", "recommended_words": "40-60", "your_words": 0, "feedback": "Cần tóm tắt xu hướng chính."},
            {"name": "Body 1", "recommended_words": "50-70", "your_words": 0, "feedback": "Mô tả chi tiết nhóm dữ liệu đầu."},
            {"name": "Body 2", "recommended_words": "50-70", "your_words": 0, "feedback": "So sánh nhóm còn lại."},
        ]
        if task_type == 1
        else [
            {"name": "Introduction", "recommended_words": "40-60", "your_words": 0, "feedback": "Paraphrase đề + outline."},
            {"name": "Body 1", "recommended_words": "90-110", "your_words": 0, "feedback": "Luận điểm + ví dụ."},
            {"name": "Body 2", "recommended_words": "90-110", "your_words": 0, "feedback": "Luận điểm thứ hai + ví dụ."},
            {"name": "Conclusion", "recommended_words": "30-50", "your_words": 0, "feedback": "Tóm tắt quan điểm."},
        ]
    )
    return _normalize_evaluation(
        {
            "overall_band": band,
            "task_achievement": band,
            "coherence_cohesion": band,
            "lexical_resource": band - 0.5,
            "grammar_accuracy": band - 0.5,
            "word_count_comment": f"~{word_count} từ (mục tiêu {min_w}+).",
            "strengths": ["Bài đã được lưu thành công."],
            "improvements": ["Cấu hình OpenRouter API key cá nhân trong Profile để nhận phản hồi AI chi tiết."],
            "summary": "Chấm điểm ước lượng (chưa có API key cá nhân).",
            "grammar": {"band": band - 0.5, "errors": [], "tips": ["Kiểm tra thì và số ít/số nhiều."]},
            "vocabulary": {"band": band - 0.5, "weak_words": [], "upgrades": [], "tips": ["Dùng từ academic thay vì từ informal."]},
            "paragraph_allocation": {"structure_ok": False, "sections": sections, "tips": ["Phân bổ số từ đều giữa các đoạn."]},
            "model_paragraph": {
                "focus": "Đoạn mẫu",
                "weak_excerpt": "",
                "improved_text": "",
                "explanation": "Cấu hình OpenRouter API key trong Profile để nhận đoạn văn mẫu nâng band.",
                "expected_band_gain": "",
            },
        },
        task_type,
        word_count,
        llm_generated=False,
    )
