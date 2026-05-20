"""
app/routers/speaking.py
────────────────────────
POST /speaking/evaluate
  → pronunciation scoring (wav2vec2)  ─┐ parallel
  → Whisper transcription             ─┘
  → OpenRouter grammar / vocab AI       (after transcript)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from pydantic import BaseModel
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, History
from app.repositories.history_repository import HistoryRepository
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speaking", tags=["Speaking"])


# ── Chat endpoint ─────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    question_text: str = ""
    user_message: str
    history: list[ChatMessage] = []

_SPEAKING_SYSTEM = """You are Catbot, an IELTS Speaking coach.
Always reply in English and keep answers concise (max ~120 words).
Use short sections with bullets:
- Opening line
- 2 key ideas
- 4-6 useful words/phrases
- 1 quick band tip
Avoid long essays unless the user explicitly asks for full sample answer."""


@router.post("/chat")
async def speaking_chat(body: ChatRequest):
    """Proxy chat messages to OpenRouter for speaking coaching."""
    if not _OPENROUTER_KEY:
        return JSONResponse(
            status_code=503,
            content={"error": "AI service unavailable: OPENROUTER_API_KEY is missing"},
        )

    messages = [{"role": "system", "content": _SPEAKING_SYSTEM}]

    # Inject the current question as context
    if body.question_text:
        messages.append({
            "role": "system",
            "content": f"Current IELTS Speaking question the student is practising: \"{body.question_text}\"",
        })

    # Add conversation history
    for m in body.history[-10:]:   # cap at last 10 turns
        messages.append({"role": m.role, "content": m.content})

    # Add current user message
    messages.append({"role": "user", "content": body.user_message})

    payload = {
        "model":       _AI_MODEL,
        "messages":    messages,
        "temperature": 0.7,
        "max_tokens":  800,
    }
    headers = {
        "Authorization": f"Bearer {_OPENROUTER_KEY}",
        "HTTP-Referer":  "http://localhost:3000",
        "Content-Type":  "application/json",
        "X-Title":       "LinguaIELTS",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
            resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return {"reply": reply}
    except Exception as exc:
        logger.warning("Speaking chat OpenRouter error: %s", exc)
        return JSONResponse(
            status_code=502,
            content={"error": f"AI service unavailable: {exc}"},
        )

_OPENROUTER_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "",
)
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_AI_MODEL       = "anthropic/claude-3-haiku"
_AI_TIMEOUT     = 60.0   # seconds

# Prefer pydantic settings (.env) and fallback to process env.
_OPENROUTER_KEY = (settings.OPENROUTER_API_KEY or _OPENROUTER_KEY or "").strip()
_AI_MODEL_FAST = (
    getattr(settings, "OPENROUTER_FAST_MODEL", None)
    or os.getenv("OPENROUTER_FAST_MODEL", "google/gemini-2.0-flash-001")
)


class TranscriptAnalyzeRequest(BaseModel):
    transcript: str
    question_text: str = ""


_CARDS_SYSTEM = (
    "You are an IELTS Speaking language analyst. "
    "Analyze ONLY the candidate transcript (Whisper ASR text). "
    "Return ONLY valid JSON, no markdown. "
    "Every highlight field `text` MUST be an exact substring copied from the transcript."
)


def _build_language_cards_prompt(question_text: str, transcript: str) -> str:
    return f"""IELTS question: {question_text or "(not provided)"}
Candidate transcript (Whisper):
\"\"\"{transcript}\"\"\"

Return JSON with EXACTLY this structure:
{{
  "grammar_analysis": {{
    "score": <float 0-9>,
    "errors": [
      {{
        "text": "<exact erroneous phrase from transcript>",
        "error_type": "<e.g. subject-verb agreement, tense, article, word order>",
        "correction": "<corrected phrase or sentence>",
        "explanation": "<short explanation in English>"
      }}
    ]
  }},
  "vocabulary_analysis": {{
    "score": <float 0-9>,
    "weak_words": [
      {{"text": "<exact weak/repeated word or phrase from transcript>", "reason": "<why it is weak>"}}
    ],
    "strong_words": [
      {{"text": "<exact strong word/phrase or collocation from transcript>", "reason": "<why it is strong>"}}
    ],
    "replacements": [
      {{"weak": "<weak word>", "better": "<better alternative>", "reason": "<short reason>"}}
    ]
  }}
}}

Rules:
- Find real grammar mistakes in the transcript (not invented).
- Mark weak/repeated basic words for vocabulary; mark strong collocations separately.
- If transcript is empty, return score 0 and empty arrays."""


def _openrouter_model_candidates(preferred: str | None) -> list[str]:
    """Primary fast model, then stable fallback (_AI_MODEL). Deduped."""
    primary = (preferred or _AI_MODEL_FAST or _AI_MODEL).strip()
    out: list[str] = []
    for m in (primary, _AI_MODEL):
        if m and m not in out:
            out.append(m)
    return out


async def _call_openrouter_json(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 900,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {_OPENROUTER_KEY}",
        "HTTP-Referer": "http://localhost:5173",
        "Content-Type": "application/json",
        "X-Title": "LinguaIELTS",
    }
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    last_exc: Exception | None = None
    resp = None
    async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
        for model_id in _openrouter_model_candidates(model):
            payload = {
                "model": model_id,
                "messages": messages,
                "temperature": 0.15,
                "max_tokens": max_tokens,
            }
            try:
                resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                err_body = ""
                try:
                    err_body = exc.response.json().get("error", {}).get("message", "")
                except Exception:
                    pass
                # OpenRouter returns 404 when model slug has no provider ("No endpoints found").
                if exc.response.status_code == 404 and model_id != _AI_MODEL:
                    logger.warning(
                        "OpenRouter model %s unavailable (%s), trying fallback %s",
                        model_id,
                        err_body or exc,
                        _AI_MODEL,
                    )
                    continue
                raise
    if resp is None:
        raise last_exc or RuntimeError("OpenRouter request failed")
    content = resp.json()["choices"][0]["message"]["content"]
    try:
        return _parse_ai_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("Cards JSON parse failed, repair pass: %s", exc)
        repaired = await _repair_ai_json_via_model(content)
        return _parse_ai_json(repaired)


async def _call_language_cards(question_text: str, transcript: str) -> dict[str, Any]:
    return await _call_openrouter_json(
        _CARDS_SYSTEM,
        _build_language_cards_prompt(question_text, transcript),
        model=_AI_MODEL_FAST,
    )


def _normalize_grammar_analysis(ai: dict[str, Any]) -> dict[str, Any]:
    ga = ai.get("grammar_analysis") if isinstance(ai.get("grammar_analysis"), dict) else {}
    score = _safe_score_0_9(
        ga.get("score")
        or ai.get("grammar_score")
        or ai.get("grammar_range_accuracy_score")
    )
    errors_raw = ga.get("errors") or ai.get("grammar_errors") or []
    errors: list[dict[str, str]] = []
    for e in errors_raw:
        if not isinstance(e, dict):
            continue
        text = str(e.get("text") or e.get("original") or "").strip()
        if not text:
            continue
        errors.append({
            "text": text,
            "error_type": str(e.get("error_type") or e.get("type") or "grammar").strip(),
            "correction": str(e.get("correction") or "").strip(),
            "explanation": str(e.get("explanation") or "").strip(),
        })
    return {"score": score, "errors": errors}


def _normalize_vocabulary_analysis(ai: dict[str, Any]) -> dict[str, Any]:
    va = ai.get("vocabulary_analysis") if isinstance(ai.get("vocabulary_analysis"), dict) else {}
    score = _safe_score_0_9(
        va.get("score")
        or ai.get("vocabulary_score")
        or ai.get("lexical_resource_score")
    )
    weak = []
    for w in va.get("weak_words") or []:
        if not isinstance(w, dict):
            continue
        text = str(w.get("text") or w.get("word") or "").strip()
        if text:
            weak.append({"text": text, "reason": str(w.get("reason") or "").strip()})
    strong = []
    for w in va.get("strong_words") or []:
        if not isinstance(w, dict):
            continue
        text = str(w.get("text") or w.get("word") or "").strip()
        if text:
            strong.append({"text": text, "reason": str(w.get("reason") or "").strip()})
    reps = []
    for r in va.get("replacements") or va.get("feedback") or ai.get("vocabulary_feedback") or []:
        if not isinstance(r, dict):
            continue
        weak_w = str(r.get("weak") or r.get("word_used") or r.get("text") or "").strip()
        better = str(r.get("better") or r.get("better_alternative") or "").strip()
        if weak_w or better:
            reps.append({
                "weak": weak_w,
                "better": better,
                "reason": str(r.get("reason") or "").strip(),
            })
    return {
        "score": score,
        "weak_words": weak,
        "strong_words": strong,
        "replacements": reps,
    }


@router.post("/analyze-language")
async def analyze_language(body: TranscriptAnalyzeRequest):
    """LLM grammar + vocabulary card analysis from Whisper transcript."""
    if not _OPENROUTER_KEY:
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


# ── audio helpers ─────────────────────────────────────────────────────────────

# RMS threshold below which audio is considered near-silent (no real speech).
# wav2vec2 + Sigmoid heads produce non-zero output even for all-zero input
# due to layer biases, so we must gate it before scoring.
_MIN_AUDIO_RMS: float = float(os.getenv("MIN_AUDIO_RMS", "0.003"))


def _load_audio_16k(path: str) -> np.ndarray:
    """Load any audio file and resample to 16 kHz mono float32."""
    import librosa
    audio, _ = librosa.load(path, sr=16_000, mono=True)
    return audio.astype(np.float32)


def _convert_to_wav(src: str) -> str:
    """Convert webm/mp4/ogg → wav using ffmpeg via pydub.  Returns new path."""
    from pydub import AudioSegment
    seg = AudioSegment.from_file(src)
    wav_path = src + ".wav"
    seg.export(wav_path, format="wav")
    return wav_path


def _has_speech(audio: np.ndarray) -> bool:
    """Return False when the recording is near-silent (likely no speech)."""
    rms = float(np.sqrt(np.mean(audio.astype("float64") ** 2)))
    logger.debug("Audio RMS=%.5f (threshold=%.4f)", rms, _MIN_AUDIO_RMS)
    return rms >= _MIN_AUDIO_RMS


# ── Task A: pronunciation ─────────────────────────────────────────────────────

def _run_pronunciation(audio: np.ndarray) -> dict[str, float]:
    """
    Synchronous; runs in thread executor.
    Returns scores 0-10 from the wav2vec2-based scorer.
    Returns all-zeros with a _silent flag when audio is near-silent so
    that the Sigmoid bias does NOT produce spurious high scores.
    """
    if not _has_speech(audio):
        logger.info(
            "Near-silent audio (RMS < %.4f) — skipping pronunciation model, "
            "returning zero scores.", _MIN_AUDIO_RMS,
        )
        return {"accuracy": 0.0, "fluency": 0.0, "prosodic": 0.0, "total": 0.0, "_silent": True}

    from ml.model_registry import get_pron_model
    pt_path = Path(os.getenv("PRON_MODEL_PATH", "model/pron_scorer_best.pt"))
    if not pt_path.is_absolute():
        pt_path = Path(__file__).resolve().parents[2] / pt_path
    if not pt_path.exists():
        raise FileNotFoundError(
            f"Pronunciation model not found at {pt_path}. "
            "Set PRON_MODEL_PATH env var or place pron_scorer_best.pt in backend/model/."
        )
    net = get_pron_model()
    return net.predict(audio)


# ── Task B: Whisper ───────────────────────────────────────────────────────────

def _run_whisper(wav_path: str) -> dict[str, Any]:
    """Synchronous; runs in thread executor."""
    from ml.model_registry import get_whisper_model
    model = get_whisper_model()
    result = model.transcribe(
        wav_path,
        language="en",
        word_timestamps=True,
        verbose=False,
    )
    transcript = result.get("text", "").strip()

    # Flatten word-level timestamps from segments
    word_ts: list[dict] = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            word_ts.append({
                "word":  w.get("word", "").strip(),
                "start": round(w.get("start", 0.0), 3),
                "end":   round(w.get("end",   0.0), 3),
                "score": round(w.get("probability", 1.0), 3),
            })

    return {"transcript": transcript, "word_timestamps": word_ts}


# ── Task C: OpenRouter AI ─────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are an IELTS Speaking examiner. Analyze the candidate's spoken response. "
    "Return ONLY valid JSON, no markdown, no explanation. "
    "All string values must escape internal double quotes."
)


def _build_user_prompt(question_text: str, transcript: str) -> str:
    # band_estimate is intentionally omitted — the server computes it from the
    # four IELTS criteria so the LLM cannot inflate it independently.
    return f"""IELTS Question: {question_text}
Candidate's transcript: {transcript}

You are scoring ONLY the linguistic content of the transcript (not audio quality).
Use IELTS Speaking descriptors and evaluate exactly these 4 criteria:
1) Fluency & Coherence
2) Lexical Resource
3) Grammatical Range & Accuracy
4) Pronunciation (text-based impression only; acoustic model score is computed separately by backend).

Evaluate and return JSON with EXACTLY this structure (all scores on IELTS 0-9 scale):
{{
  "fluency_coherence_score": <float 0-9>,
  "lexical_resource_score": <float 0-9>,
  "grammar_range_accuracy_score": <float 0-9>,
  "pronunciation_text_score": <float 0-9>,
  "grammar_score": <float 0-9, same as grammar_range_accuracy_score>,
  "vocabulary_score": <float 0-9, same as lexical_resource_score>,
  "coherence_score": <float 0-9, same as fluency_coherence_score>,
  "task_response_score": <float 0-9, relevance to the IELTS question / avoid off-topic>,
  "is_off_topic": <true|false>,
  "task_response_comment": "1 short sentence about whether answer addresses the prompt",
  "grammar_errors": [
    {{"original": "...", "correction": "...", "explanation": "..."}}
  ],
  "grammar_analysis": {{
    "score": <float 0-9>,
    "errors": [
      {{
        "text": "<exact erroneous phrase copied from transcript>",
        "error_type": "<e.g. subject-verb agreement, tense>",
        "correction": "<corrected phrase>",
        "explanation": "<short explanation>"
      }}
    ]
  }},
  "vocabulary_feedback": [
    {{"word_used": "...", "better_alternative": "...", "reason": "..."}}
  ],
  "vocabulary_analysis": {{
    "score": <float 0-9>,
    "weak_words": [{{"text": "<exact phrase>", "reason": "..."}}],
    "strong_words": [{{"text": "<exact phrase>", "reason": "..."}}],
    "replacements": [{{"weak": "...", "better": "...", "reason": "..."}}]
  }},
  "overall_comment": "2-3 sentence summary in English",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "band_boost_tips": [
    "Actionable tip 1 for raising band",
    "Actionable tip 2 for raising band",
    "Actionable tip 3 for raising band"
  ],
  "upgraded_sample_answer": "A stronger model response (around 100-160 words) that addresses the same IELTS question with better coherence, vocabulary, and grammar.",
  "criteria_feedback": {{
    "fluency_coherence": {{
      "strengths": ["...", "..."],
      "issues": ["...", "..."],
      "advice": ["...", "..."]
    }},
    "lexical_resource": {{
      "strengths": ["...", "..."],
      "issues": ["...", "..."],
      "advice": ["...", "..."]
    }},
    "grammar_range_accuracy": {{
      "strengths": ["...", "..."],
      "issues": ["...", "..."],
      "advice": ["...", "..."]
    }}
  }}
}}

If the transcript is empty or unintelligible, return all scores as 0 and note it in overall_comment."""


async def _call_openrouter(question_text: str, transcript: str) -> dict[str, Any]:
    """Async HTTP call to OpenRouter (fast model for scoring + card payloads)."""
    headers = {
        "Authorization": f"Bearer {_OPENROUTER_KEY}",
        "HTTP-Referer": "http://localhost:5173",
        "Content-Type": "application/json",
        "X-Title": "LinguaIELTS",
    }
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(question_text, transcript)},
    ]
    last_exc: Exception | None = None
    resp = None
    async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
        for model_id in _openrouter_model_candidates(None):
            payload = {
                "model": model_id,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1200,
            }
            try:
                resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code == 404 and model_id != _AI_MODEL:
                    logger.warning("OpenRouter evaluate model %s unavailable, fallback %s", model_id, _AI_MODEL)
                    continue
                raise
    if resp is None:
        raise last_exc or RuntimeError("OpenRouter request failed")

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        return _parse_ai_json(content)
    except json.JSONDecodeError as exc:
        logger.warning("Primary AI JSON parse failed, trying repair pass: %s", exc)
        repaired_content = await _repair_ai_json_via_model(content)
        return _parse_ai_json(repaired_content)


async def _repair_ai_json_via_model(raw_text: str) -> str:
    """
    Ask model to rewrite malformed analysis text into strict valid JSON.
    Returns raw text output from model (still parsed by _parse_ai_json afterwards).
    """
    repair_prompt = f"""Rewrite the following text into STRICT valid JSON only.
Do not add markdown.
Do not add explanations.
Keep exactly this schema and keys:
{{
  "fluency_coherence_score": <float 0-9>,
  "lexical_resource_score": <float 0-9>,
  "grammar_range_accuracy_score": <float 0-9>,
  "pronunciation_text_score": <float 0-9>,
  "grammar_score": <float 0-9>,
  "vocabulary_score": <float 0-9>,
  "coherence_score": <float 0-9>,
  "task_response_score": <float 0-9>,
  "is_off_topic": <true|false>,
  "task_response_comment": "...",
  "grammar_errors": [
    {{"original": "...", "correction": "...", "explanation": "..."}}
  ],
  "vocabulary_feedback": [
    {{"word_used": "...", "better_alternative": "...", "reason": "..."}}
  ],
  "overall_comment": "2-3 sentence summary in English",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "band_boost_tips": ["...", "...", "..."],
  "upgraded_sample_answer": "...",
  "criteria_feedback": {{
    "fluency_coherence": {{"strengths": ["..."], "issues": ["..."], "advice": ["..."]}},
    "lexical_resource": {{"strengths": ["..."], "issues": ["..."], "advice": ["..."]}},
    "grammar_range_accuracy": {{"strengths": ["..."], "issues": ["..."], "advice": ["..."]}}
  }}
}}

Input text to normalize:
{raw_text}
"""
    payload = {
        "model": _AI_MODEL,
        "messages": [
            {"role": "system", "content": "You convert malformed JSON-like text into strict valid JSON."},
            {"role": "user", "content": repair_prompt},
        ],
        "temperature": 0,
        "max_tokens": 800,
    }
    headers = {
        "Authorization": f"Bearer {_OPENROUTER_KEY}",
        "HTTP-Referer": "http://localhost:3000",
        "Content-Type": "application/json",
        "X-Title": "LinguaIELTS",
    }
    async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
        resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _extract_json_candidate(text: str) -> str:
    """
    Extract the most likely JSON object from model output.
    Handles markdown fences and extra prose around JSON.
    """
    raw = (text or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1].strip()
    return raw


def _parse_ai_json(text: str) -> dict[str, Any]:
    """
    Parse model output to JSON with small repair attempts.
    Raises JSONDecodeError if still invalid.
    """
    candidate = _extract_json_candidate(text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Common normalization for smart quotes and accidental trailing commas.
        repaired = (
            candidate
            .replace("“", "\"")
            .replace("”", "\"")
            .replace("’", "'")
            .replace(",]", "]")
            .replace(",}", "}")
        )
        return json.loads(repaired)


def _empty_criteria_feedback() -> dict[str, Any]:
    return {
        "fluency_coherence": {"strengths": [], "issues": [], "advice": []},
        "lexical_resource": {"strengths": [], "issues": [], "advice": []},
        "grammar_range_accuracy": {"strengths": [], "issues": [], "advice": []},
    }


def _safe_score_0_9(value: Any) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(9.0, num))


# ── endpoint ─────────────────────────────────────────────────────────────────

@router.post("/evaluate")
async def evaluate_speaking(
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
    """
    Receive recorded audio + question text, run 3-step pipeline:
      A) Pronunciation model (wav2vec2)
      B) Whisper transcription
      C) OpenRouter AI grammar/vocab  [after B]
    Returns merged evaluation JSON.
    """
    # ── save upload to temp file ──────────────────────────────────────────
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    wav_path = tmp_path
    try:
        # Convert non-wav formats
        if suffix.lower() not in (".wav",):
            try:
                wav_path = _convert_to_wav(tmp_path)
            except Exception as exc:
                logger.warning("pydub convert failed, trying raw path: %s", exc)

        # Load 16 kHz audio array (shared between tasks)
        try:
            audio_16k = await asyncio.to_thread(_load_audio_16k, wav_path)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not decode audio: {exc}")

        # ── Task A + B in parallel ────────────────────────────────────────
        pron_future     = asyncio.to_thread(_run_pronunciation, audio_16k)
        whisper_future  = asyncio.to_thread(_run_whisper, wav_path)

        pron_result: dict | None      = None
        whisper_result: dict | None   = None
        pron_error: str | None        = None
        whisper_error: str | None     = None
        ai_result: dict | None        = None
        ai_error: str | None          = None

        try:
            pron_result, whisper_result = await asyncio.gather(
                pron_future, whisper_future, return_exceptions=False
            )
        except Exception as exc:
            logger.error("parallel tasks failed: %s", exc)
            # Try individually so we get partial results
            try:
                pron_result = await asyncio.to_thread(_run_pronunciation, audio_16k)
            except Exception as e:
                pron_error = str(e)
            try:
                whisper_result = await asyncio.to_thread(_run_whisper, wav_path)
            except Exception as e:
                whisper_error = str(e)

        # ── Task C: AI (needs transcript) ─────────────────────────────────
        transcript = (whisper_result or {}).get("transcript", "")
        if transcript and not whisper_error and _OPENROUTER_KEY:
            try:
                ai_result = await _call_openrouter(question_text, transcript)
            except Exception as exc:
                ai_error = str(exc)
                logger.warning("OpenRouter call failed: %s", exc)
        elif transcript and not _OPENROUTER_KEY:
            ai_error = "OPENROUTER_API_KEY is missing"
        else:
            ai_error = whisper_error or "No transcript available"

        # Fallback: cards-only LLM pass if full scoring JSON failed
        if transcript and not whisper_error and _OPENROUTER_KEY and not ai_result:
            try:
                ai_result = await _call_language_cards(question_text, transcript)
                ai_error = None
            except Exception as exc:
                if not ai_error:
                    ai_error = str(exc)
                logger.warning("Language cards fallback failed: %s", exc)

        # ── merge response ────────────────────────────────────────────────
        pron_data = pron_result or {"accuracy": 0.0, "fluency": 0.0, "prosodic": 0.0, "total": 0.0}
        ai_data   = ai_result   or {}

        grammar_score    = _safe_score_0_9(ai_data.get("grammar_score") or ai_data.get("grammar_range_accuracy_score"))
        vocabulary_score = _safe_score_0_9(ai_data.get("vocabulary_score") or ai_data.get("lexical_resource_score"))
        coherence_score  = _safe_score_0_9(ai_data.get("coherence_score") or ai_data.get("fluency_coherence_score"))
        task_response_score = _safe_score_0_9(ai_data.get("task_response_score"))
        pronunciation_text_score = _safe_score_0_9(ai_data.get("pronunciation_text_score"))
        is_off_topic = bool(ai_data.get("is_off_topic", False))
        pron_total       = float(pron_data.get("total", 0))
        llm_generated = bool(ai_result)
        grammar_analysis = _normalize_grammar_analysis(ai_data) if llm_generated else {"score": 0.0, "errors": []}
        vocabulary_analysis = _normalize_vocabulary_analysis(ai_data) if llm_generated else {
            "score": 0.0,
            "weak_words": [],
            "strong_words": [],
            "replacements": [],
        }
        if llm_generated:
            grammar_score = grammar_analysis["score"]
            vocabulary_score = vocabulary_analysis["score"]

        # ── IELTS Speaking band: average of the 4 official criteria ──────
        # Fluency & Coherence  → coherence_score  (0-9, from LLM)
        # Lexical Resource      → vocabulary_score (0-9, from LLM)
        # Grammatical Range     → grammar_score    (0-9, from LLM)
        # Pronunciation         → pron_total       (0-10, from wav2vec2 → rescaled to 0-9)
        pron_9 = round(pron_total / 10 * 9, 2)
        effective_fc = coherence_score
        if task_response_score > 0:
            effective_fc = round((coherence_score * 0.6) + (task_response_score * 0.4), 2)

        raw_band = (grammar_score + vocabulary_score + effective_fc + pron_9) / 4
        if is_off_topic:
            raw_band = min(raw_band, 5.0)
        # Round to nearest 0.5 following IELTS convention; clamp to [0, 9]
        band_estimate = max(0.0, min(9.0, round(raw_band * 2) / 2))

        response: dict[str, Any] = {
            "pronunciation": pron_data,
            "transcript":       transcript,
            "word_timestamps":  (whisper_result or {}).get("word_timestamps", []),
            "grammar_analysis": grammar_analysis,
            "vocabulary_analysis": vocabulary_analysis,
            "grammar": {
                "score":  grammar_score,
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
                "score":    vocabulary_score,
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
            "coherence_score": coherence_score,  # Fluency & Coherence
            "fluency_coherence_score": coherence_score,
            "lexical_resource_score": vocabulary_score,
            "grammar_range_accuracy_score": grammar_score,
            "pronunciation_text_score": pronunciation_text_score,
            "task_response_score": task_response_score,
            "task_response_comment": ai_data.get("task_response_comment", ""),
            "is_off_topic": is_off_topic,
            "llm_generated": llm_generated,
            "band_estimate":   band_estimate,
            "overall_comment": ai_data.get("overall_comment") or ("LLM analysis unavailable." if ai_error else ""),
            "strengths":       ai_data.get("strengths") or [],
            "improvements":    ai_data.get("improvements") or [],
            "band_boost_tips": ai_data.get("band_boost_tips") or [],
            "upgraded_sample_answer": ai_data.get("upgraded_sample_answer") or "",
            "criteria_feedback": ai_data.get("criteria_feedback") or _empty_criteria_feedback(),
            # Debug info so the frontend can show the breakdown
            "_score_breakdown": {
                "grammar":     round(grammar_score, 2),
                "vocabulary":  round(vocabulary_score, 2),
                "coherence":   round(coherence_score, 2),
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
                "question_id":        question_id,
                "attempt_id":         attempt_id,
                "question_text":      question_text,
                "band_estimate":      band_estimate,
                "grammar_score":      grammar_score,
                "vocabulary_score":   vocabulary_score,
                "coherence_score":    coherence_score,
                "fluency_coherence_score": coherence_score,
                "lexical_resource_score": vocabulary_score,
                "grammar_range_accuracy_score": grammar_score,
                "task_response_score": task_response_score,
                "task_response_comment": response.get("task_response_comment", ""),
                "is_off_topic": is_off_topic,
                "llm_generated": llm_generated,
                "pronunciation_total": pron_total,
                "overall_comment":    response.get("overall_comment", ""),
                "strengths":          response.get("strengths", []),
                "improvements":       response.get("improvements", []),
                "band_boost_tips":    response.get("band_boost_tips", []),
                "upgraded_sample_answer": response.get("upgraded_sample_answer", ""),
                "criteria_feedback":  response.get("criteria_feedback", {}),
            }

            history_repo = HistoryRepository(db)
            if session_id:
                session_repo = PracticeSessionRepository(db)
                sess = await session_repo.get_by_id_for_user(session_id=session_id, user_id=current_user.id)
                if sess and sess.session_type == "speaking":
                    await session_repo.mark_submitted(sess, score=band_estimate)

            await history_repo.create(
                user_id=current_user.id,
                quiz_id=str(quiz_id or session_id or "speaking"),
                subject="Speaking",
                score=int(round(band_estimate * 10)),   # store as 0-90 int
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
            # speaking evaluation earns at least 1 XP by activity rule
            await ProfileRepository(db).update_streak_and_xp(
                current_user.id,
                xp_to_add=max(1, (answer_duration_seconds or 0) // 600),
            )

        return JSONResponse(content=response)

    finally:
        # Clean up temp files
        for p in {tmp_path, wav_path}:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass


@router.get("/attempt-summary")
async def get_speaking_attempt_summary(
    quiz_id: str,
    attempt_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Return speaking results for a specific attempt (or latest attempt) of a quiz.
    """
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
                "history_id":         r.id,
                "question_id":        payload.get("question_id"),
                "question_text":      payload.get("question_text", ""),
                "band_estimate":      float(payload.get("band_estimate")      or r.band_score or 0),
                "grammar_score":      float(payload.get("grammar_score")      or 0),
                "vocabulary_score":   float(payload.get("vocabulary_score")   or 0),
                "coherence_score":    float(payload.get("coherence_score")    or 0),
                "fluency_coherence_score": float(payload.get("fluency_coherence_score") or payload.get("coherence_score") or 0),
                "lexical_resource_score": float(payload.get("lexical_resource_score") or payload.get("vocabulary_score") or 0),
                "grammar_range_accuracy_score": float(payload.get("grammar_range_accuracy_score") or payload.get("grammar_score") or 0),
                "task_response_score":float(payload.get("task_response_score") or 0),
                "task_response_comment": payload.get("task_response_comment") or "",
                "is_off_topic": bool(payload.get("is_off_topic", False)),
                "llm_generated": bool(payload.get("llm_generated", False)),
                "pronunciation_total":float(payload.get("pronunciation_total") or 0),
                "overall_comment":    payload.get("overall_comment") or "",
                "strengths":          payload.get("strengths") or [],
                "improvements":       payload.get("improvements") or [],
                "band_boost_tips":    payload.get("band_boost_tips") or [],
                "upgraded_sample_answer": payload.get("upgraded_sample_answer") or "",
                "criteria_feedback":   payload.get("criteria_feedback") or {},
                "completed_at":       r.completed_at,
            }
        )

    def _avg(key: str) -> float:
        vals = [float(i.get(key) or 0) for i in items]
        return round(sum(vals) / max(len(vals), 1), 2)

    average = {
        "band_estimate":       _avg("band_estimate"),
        "grammar_score":       _avg("grammar_score"),
        "vocabulary_score":    _avg("vocabulary_score"),
        "coherence_score":     _avg("coherence_score"),
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
