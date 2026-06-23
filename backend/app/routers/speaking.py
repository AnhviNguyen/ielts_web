"""
app/routers/speaking.py — HTTP routes for speaking coach, analysis, and evaluation.
Business logic lives in app/services/speaking_* .
"""
import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.openrouter_client import chat_completion, has_openrouter_keys
from app.core.rate_limit import limiter
from app.core.upload import ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_UPLOAD_SIZE, read_upload_limited
from app.db.database import get_db
from app.db.models import History, User
from app.repositories.profile_repository import ProfileRepository
from app.services.speaking_ai_helpers import (
    OPENROUTER_KEY,
    _call_language_cards,
    _normalize_grammar_analysis,
    _normalize_vocabulary_analysis,
)
from app.services.speaking_eval_service import evaluate_speaking_core

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speaking", tags=["Speaking"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question_text: str = ""
    user_message: str
    history: list[ChatMessage] = []


class TranscriptAnalyzeRequest(BaseModel):
    transcript: str
    question_text: str = ""


_SPEAKING_SYSTEM = """You are Catbot, an IELTS Speaking coach.
Always reply in English and keep answers concise (max ~120 words).
Use short sections with bullets:
- Opening line
- 2 key ideas
- 4-6 useful words/phrases
- 1 quick band tip
Avoid long essays unless the user explicitly asks for full sample answer."""


@limiter.limit("30/minute")
@router.post("/chat")
async def speaking_chat(
    request: Request,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Proxy chat messages to OpenRouter for speaking coaching (JWT required)."""
    _ = current_user
    if not has_openrouter_keys():
        return JSONResponse(
            status_code=503,
            content={"error": "AI service unavailable: OPENROUTER_API_KEY is missing"},
        )

    messages = [{"role": "system", "content": _SPEAKING_SYSTEM}]
    if body.question_text:
        messages.append({
            "role": "system",
            "content": f'Current IELTS Speaking question the student is practising: "{body.question_text}"',
        })
    for m in body.history[-10:]:
        role = m.role if m.role in {"user", "assistant"} else "user"
        messages.append({"role": role, "content": m.content})
    messages.append({"role": "user", "content": body.user_message})

    try:
        reply, _model = await chat_completion(
            messages,
            max_tokens=800,
            temperature=0.7,
            timeout=60.0,
            title="LinguaIELTS Speaking Coach",
        )
        return {"reply": reply}
    except Exception as exc:
        logger.warning("Speaking chat OpenRouter error: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"error": f"AI service unavailable: {exc}"},
        )


@limiter.limit("20/minute")
@router.post("/analyze-language")
async def analyze_language(
    request: Request,
    body: TranscriptAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """LLM grammar + vocabulary card analysis from Whisper transcript (JWT required)."""
    _ = current_user
    if not OPENROUTER_KEY:
        return JSONResponse(
            status_code=503,
            content={"error": "OPENROUTER_API_KEY is missing"},
        )
    transcript = (body.transcript or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript is required")
    try:
        raw = await _call_language_cards(body.question_text, transcript)
        return {
            "llm_generated": True,
            "grammar_analysis": _normalize_grammar_analysis(raw),
            "vocabulary_analysis": _normalize_vocabulary_analysis(raw),
        }
    except Exception as exc:
        logger.warning("analyze-language failed: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"error": f"Language analysis failed: {exc}"},
        )


@router.post("/evaluate")
@limiter.limit("5/minute")
async def evaluate_speaking(
    request: Request,
    file: UploadFile = File(...),
    question_text: str = Form(default=""),
    session_id: int | None = Form(default=None),
    quiz_id: str | None = Form(default=None),
    question_id: str | None = Form(default=None),
    attempt_id: str | None = Form(default=None),
    answer_duration_seconds: int | None = Form(default=None),
    persist_result: bool = Form(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """HTTP handler: save upload, optionally dispatch Celery, else run pipeline inline."""
    await ProfileRepository(db).ensure_speaking_eval_allowed(current_user.id)

    suffix = (Path(file.filename or "audio.webm").suffix or ".webm").lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio file type")
    audio_bytes = await read_upload_limited(file, MAX_AUDIO_UPLOAD_SIZE)
    from app.core.shared_uploads import save_shared_upload

    try:
        tmp_path = save_shared_upload(audio_bytes, suffix)
    except OSError as exc:
        logger.exception("Failed to save speaking upload")
        raise HTTPException(
            status_code=503,
            detail="Không lưu được file ghi âm trên server. Thử lại sau.",
        ) from exc

    if settings.CELERY_ENABLED:
        from app.core.task_ownership import register_task_owner
        from app.tasks.speaking_tasks import evaluate_speaking_task

        task = evaluate_speaking_task.delay(
            {
                "tmp_path": tmp_path,
                "suffix": suffix,
                "question_text": question_text,
                "session_id": session_id,
                "quiz_id": quiz_id,
                "question_id": question_id,
                "attempt_id": attempt_id,
                "answer_duration_seconds": answer_duration_seconds,
                "persist_result": persist_result,
                "user_id": current_user.id,
            }
        )
        register_task_owner(task.id, current_user.id)
        await ProfileRepository(db).increment_speaking_eval(current_user.id)
        return {"task_id": task.id, "status": "processing"}

    try:
        result = await evaluate_speaking_core(
            db=db,
            current_user=current_user,
            tmp_path=tmp_path,
            suffix=suffix,
            question_text=question_text,
            session_id=session_id,
            quiz_id=quiz_id,
            question_id=question_id,
            attempt_id=attempt_id,
            answer_duration_seconds=answer_duration_seconds,
            persist_result=persist_result,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Speaking evaluate failed for user %s", current_user.id)
        raise HTTPException(
            status_code=503,
            detail="Đánh giá Speaking tạm thời không khả dụng. Thử lại sau vài giây (Whisper đang tải lần đầu).",
        ) from exc
    await ProfileRepository(db).increment_speaking_eval(current_user.id)
    return JSONResponse(content=result)


@router.get("/evaluate/result/{task_id}")
async def get_evaluate_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.core.celery_app import celery_app
    from app.core.task_ownership import verify_task_owner

    if not verify_task_owner(task_id, current_user.id):
        raise HTTPException(status_code=403, detail="Không có quyền truy cập task này")

    task = celery_app.AsyncResult(task_id)
    state_map = {"PENDING": 0, "STARTED": 30, "RETRY": 20}
    if task.state == "SUCCESS":
        return {"status": "done", "result": task.result}
    if task.state == "FAILURE":
        detail = str(task.result) if task.result else "Đánh giá thất bại, vui lòng thử lại"
        return {"status": "error", "detail": detail[:500]}
    return {"status": "processing", "progress": state_map.get(task.state, 10)}


@router.get("/attempt-summary")
async def get_speaking_attempt_summary(
    quiz_id: str,
    attempt_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return speaking results for a specific attempt (or latest) of a quiz."""
    rs = await db.execute(
        select(History)
        .where(
            History.user_id == current_user.id,
            History.subject == "Speaking",
            History.quiz_id == str(quiz_id),
        )
        .order_by(History.completed_at.desc())
    )
    rows = list(rs.scalars().all())
    if not rows:
        return {"items": [], "average": None, "attempt_id": None, "quiz_id": str(quiz_id)}

    def _attempt_from_row(r: History) -> str | None:
        payload = r.answers if isinstance(r.answers, dict) else {}
        return payload.get("attempt_id")

    target_attempt = attempt_id
    if not target_attempt:
        for row in rows:
            found = _attempt_from_row(row)
            if found:
                target_attempt = found
                break

    if target_attempt:
        rows = [r for r in rows if _attempt_from_row(r) == target_attempt]

    items = []
    for r in rows:
        payload = r.answers if isinstance(r.answers, dict) else {}
        items.append(
            {
                "history_id": r.id,
                "question_id": payload.get("question_id"),
                "question_text": payload.get("question_text", ""),
                "band_estimate": float(payload.get("band_estimate") or r.band_score or 0),
                "grammar_score": float(payload.get("grammar_score") or 0),
                "vocabulary_score": float(payload.get("vocabulary_score") or 0),
                "coherence_score": float(payload.get("coherence_score") or 0),
                "fluency_coherence_score": float(
                    payload.get("fluency_coherence_score") or payload.get("coherence_score") or 0
                ),
                "lexical_resource_score": float(
                    payload.get("lexical_resource_score") or payload.get("vocabulary_score") or 0
                ),
                "grammar_range_accuracy_score": float(
                    payload.get("grammar_range_accuracy_score") or payload.get("grammar_score") or 0
                ),
                "task_response_score": float(payload.get("task_response_score") or 0),
                "task_response_comment": payload.get("task_response_comment") or "",
                "is_off_topic": bool(payload.get("is_off_topic", False)),
                "llm_generated": bool(payload.get("llm_generated", False)),
                "pronunciation_total": float(payload.get("pronunciation_total") or 0),
                "overall_comment": payload.get("overall_comment") or "",
                "strengths": payload.get("strengths") or [],
                "improvements": payload.get("improvements") or [],
                "band_boost_tips": payload.get("band_boost_tips") or [],
                "upgraded_sample_answer": payload.get("upgraded_sample_answer") or "",
                "criteria_feedback": payload.get("criteria_feedback") or {},
                "completed_at": r.completed_at,
            }
        )

    def _avg(key: str) -> float:
        vals = [float(i.get(key) or 0) for i in items]
        return round(sum(vals) / max(len(vals), 1), 2)

    average = {
        "band_estimate": _avg("band_estimate"),
        "grammar_score": _avg("grammar_score"),
        "vocabulary_score": _avg("vocabulary_score"),
        "coherence_score": _avg("coherence_score"),
        "fluency_coherence_score": _avg("fluency_coherence_score"),
        "lexical_resource_score": _avg("lexical_resource_score"),
        "grammar_range_accuracy_score": _avg("grammar_range_accuracy_score"),
        "task_response_score": _avg("task_response_score"),
        "pronunciation_total": _avg("pronunciation_total"),
    }
    items.sort(key=lambda x: str(x.get("question_id") or ""))
    return {
        "items": items,
        "average": average,
        "attempt_id": target_attempt,
        "quiz_id": str(quiz_id),
    }
