"""Speaking evaluation pipeline (Whisper + pronunciation + LLM)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import invalidate_leaderboard_cache
from app.db.models import User
from app.repositories.history_repository import HistoryRepository
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.services.speaking_ai_helpers import (
    OPENROUTER_KEY,
    _call_language_cards,
    _call_openrouter,
    _empty_criteria_feedback,
    _normalize_grammar_analysis,
    _normalize_vocabulary_analysis,
    _safe_score_0_9,
)
from app.services.speaking_audio_utils import (
    convert_to_wav,
    load_audio_16k,
    run_pronunciation,
    run_whisper,
)

logger = logging.getLogger(__name__)


async def evaluate_speaking_core(
    db: AsyncSession,
    current_user: User,
    tmp_path: str,
    suffix: str,
    question_text: str = "",
    session_id: int | None = None,
    quiz_id: str | None = None,
    question_id: str | None = None,
    attempt_id: str | None = None,
    answer_duration_seconds: int | None = None,
    persist_result: bool = False,
) -> dict[str, Any]:
    """Run speaking evaluation; used by HTTP handler and Celery worker."""
    wav_path = tmp_path
    try:
        if suffix.lower() not in (".wav",):
            try:
                wav_path = convert_to_wav(tmp_path)
            except Exception as exc:
                logger.warning("pydub convert failed, trying raw path: %s", exc)

        try:
            audio_16k = await asyncio.to_thread(load_audio_16k, wav_path)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not decode audio: {exc}") from exc

        pron_future = asyncio.to_thread(run_pronunciation, audio_16k)
        whisper_future = asyncio.to_thread(run_whisper, wav_path)

        pron_result: dict | None = None
        whisper_result: dict | None = None
        pron_error: str | None = None
        whisper_error: str | None = None
        ai_result: dict | None = None
        ai_error: str | None = None

        try:
            pron_result, whisper_result = await asyncio.gather(
                pron_future, whisper_future, return_exceptions=False
            )
        except Exception as exc:
            logger.error("parallel tasks failed: %s", exc)
            try:
                pron_result = await asyncio.to_thread(run_pronunciation, audio_16k)
            except Exception as e:
                pron_error = str(e)
            try:
                whisper_result = await asyncio.to_thread(run_whisper, wav_path)
            except Exception as e:
                whisper_error = str(e)

        transcript = (whisper_result or {}).get("transcript", "")
        if transcript and not whisper_error and OPENROUTER_KEY:
            try:
                ai_result = await _call_openrouter(question_text, transcript)
            except Exception as exc:
                ai_error = str(exc)
                logger.warning("OpenRouter call failed: %s", exc)
        elif transcript and not OPENROUTER_KEY:
            ai_error = "OPENROUTER_API_KEY is missing"
        else:
            ai_error = whisper_error or "No transcript available"

        if transcript and not whisper_error and OPENROUTER_KEY and not ai_result:
            try:
                ai_result = await _call_language_cards(question_text, transcript)
                ai_error = None
            except Exception as exc:
                if not ai_error:
                    ai_error = str(exc)
                logger.warning("Language cards fallback failed: %s", exc)

        pron_data = pron_result or {"accuracy": 0.0, "fluency": 0.0, "prosodic": 0.0, "total": 0.0}
        ai_data = ai_result or {}

        grammar_score = _safe_score_0_9(
            ai_data.get("grammar_score") or ai_data.get("grammar_range_accuracy_score")
        )
        vocabulary_score = _safe_score_0_9(
            ai_data.get("vocabulary_score") or ai_data.get("lexical_resource_score")
        )
        coherence_score = _safe_score_0_9(
            ai_data.get("coherence_score") or ai_data.get("fluency_coherence_score")
        )
        task_response_score = _safe_score_0_9(ai_data.get("task_response_score"))
        pronunciation_text_score = _safe_score_0_9(ai_data.get("pronunciation_text_score"))
        is_off_topic = bool(ai_data.get("is_off_topic", False))
        pron_total = float(pron_data.get("total", 0))
        llm_generated = bool(ai_result)
        grammar_analysis = (
            _normalize_grammar_analysis(ai_data) if llm_generated else {"score": 0.0, "errors": []}
        )
        vocabulary_analysis = (
            _normalize_vocabulary_analysis(ai_data)
            if llm_generated
            else {"score": 0.0, "weak_words": [], "strong_words": [], "replacements": []}
        )
        if llm_generated:
            grammar_score = grammar_analysis["score"]
            vocabulary_score = vocabulary_analysis["score"]

        pron_9 = round(pron_total / 10 * 9, 2)
        effective_fc = coherence_score
        if task_response_score > 0:
            effective_fc = round((coherence_score * 0.6) + (task_response_score * 0.4), 2)

        raw_band = (grammar_score + vocabulary_score + effective_fc + pron_9) / 4
        if is_off_topic:
            raw_band = min(raw_band, 5.0)
        band_estimate = max(0.0, min(9.0, round(raw_band * 2) / 2))

        response: dict[str, Any] = {
            "pronunciation": pron_data,
            "transcript": transcript,
            "word_timestamps": (whisper_result or {}).get("word_timestamps", []),
            "grammar_analysis": grammar_analysis,
            "vocabulary_analysis": vocabulary_analysis,
            "grammar": {
                "score": grammar_score,
                "errors": [
                    {
                        "original": e["text"],
                        "correction": e["correction"],
                        "explanation": e["explanation"],
                        "error_type": e["error_type"],
                        "text": e["text"],
                    }
                    for e in grammar_analysis.get("errors", [])
                ],
            },
            "vocabulary": {
                "score": vocabulary_score,
                "feedback": [
                    {
                        "word_used": r["weak"],
                        "better_alternative": r["better"],
                        "reason": r["reason"],
                    }
                    for r in vocabulary_analysis.get("replacements", [])
                ],
                "weak_words": vocabulary_analysis.get("weak_words", []),
                "strong_words": vocabulary_analysis.get("strong_words", []),
                "replacements": vocabulary_analysis.get("replacements", []),
            },
            "coherence_score": coherence_score,
            "fluency_coherence_score": coherence_score,
            "lexical_resource_score": vocabulary_score,
            "grammar_range_accuracy_score": grammar_score,
            "pronunciation_text_score": pronunciation_text_score,
            "task_response_score": task_response_score,
            "task_response_comment": ai_data.get("task_response_comment", ""),
            "is_off_topic": is_off_topic,
            "llm_generated": llm_generated,
            "band_estimate": band_estimate,
            "overall_comment": ai_data.get("overall_comment")
            or ("LLM analysis unavailable." if ai_error else ""),
            "strengths": ai_data.get("strengths") or [],
            "improvements": ai_data.get("improvements") or [],
            "band_boost_tips": ai_data.get("band_boost_tips") or [],
            "upgraded_sample_answer": ai_data.get("upgraded_sample_answer") or "",
            "criteria_feedback": ai_data.get("criteria_feedback") or _empty_criteria_feedback(),
            "_score_breakdown": {
                "grammar": round(grammar_score, 2),
                "vocabulary": round(vocabulary_score, 2),
                "coherence": round(coherence_score, 2),
                "task_response": round(task_response_score, 2),
                "effective_fc": round(effective_fc, 2),
                "pron_9scale": pron_9,
            },
        }
        if pron_error:
            response["pron_error"] = pron_error
        if whisper_error:
            response["whisper_error"] = whisper_error
        if ai_error:
            response["ai_error"] = ai_error

        if persist_result:
            score_payload = {
                "question_id": question_id,
                "attempt_id": attempt_id,
                "question_text": question_text,
                "band_estimate": band_estimate,
                "grammar_score": grammar_score,
                "vocabulary_score": vocabulary_score,
                "coherence_score": coherence_score,
                "fluency_coherence_score": coherence_score,
                "lexical_resource_score": vocabulary_score,
                "grammar_range_accuracy_score": grammar_score,
                "task_response_score": task_response_score,
                "task_response_comment": response.get("task_response_comment", ""),
                "is_off_topic": is_off_topic,
                "llm_generated": llm_generated,
                "pronunciation_total": pron_total,
                "overall_comment": response.get("overall_comment", ""),
                "strengths": response.get("strengths", []),
                "improvements": response.get("improvements", []),
                "band_boost_tips": response.get("band_boost_tips", []),
                "upgraded_sample_answer": response.get("upgraded_sample_answer", ""),
                "criteria_feedback": response.get("criteria_feedback", {}),
            }

            history_repo = HistoryRepository(db)
            if session_id:
                session_repo = PracticeSessionRepository(db)
                sess = await session_repo.get_by_id_for_user(
                    session_id=session_id, user_id=current_user.id
                )
                if sess and sess.session_type == "speaking":
                    await session_repo.mark_submitted(sess, score=band_estimate)

            await history_repo.create(
                user_id=current_user.id,
                quiz_id=str(quiz_id or session_id or "speaking"),
                subject="Speaking",
                score=int(round(band_estimate * 10)),
                total_questions=10,
                percentage=round((band_estimate / 9) * 100, 2),
                answers=score_payload,
                band_score=band_estimate,
                mode="practice",
                duration_seconds=answer_duration_seconds or 0,
            )
            progress_repo = ProgressRepository(db)
            existing = await progress_repo.get_by_subject(current_user.id, "Speaking")
            total_q = (existing.total_questions if existing else 0) + 1
            completed_q = (existing.completed_questions if existing else 0) + 1
            percentage = round((completed_q / max(total_q, 1)) * 100, 2)
            await progress_repo.upsert(
                user_id=current_user.id,
                subject="Speaking",
                total_questions=total_q,
                completed_questions=completed_q,
                percentage=percentage,
            )
            await ProfileRepository(db).update_streak_and_xp(
                current_user.id,
                xp_to_add=max(1, (answer_duration_seconds or 0) // 600),
            )
            invalidate_leaderboard_cache()

        return response

    finally:
        for p in {tmp_path, wav_path}:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass
