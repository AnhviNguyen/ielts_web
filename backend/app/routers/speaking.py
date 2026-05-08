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
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from pydantic import BaseModel

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

_SPEAKING_SYSTEM = """You are Catbot, an expert IELTS Speaking coach on an English learning platform.

IMPORTANT RULES:
- Always reply in English, regardless of what language the user writes in.
- Be specific and detailed — never give vague generic advice.
- Structure every response with clear labelled sections.

When asked about a speaking question, always include ALL of the following:

1. OPENING LINE(S)
   Give 2-3 specific phrases to start the answer. Example:
   "One thing I find really interesting about this is..."
   "To be honest, I have quite strong feelings about..."

2. STRUCTURE
   Briefly describe how to organise the 1-2 minute answer (e.g. Point → Reason → Example → Wrap-up).

3. USEFUL VOCABULARY
   Provide 6-10 relevant words or phrases grouped by function:
   - Discourse markers: "Furthermore, ...", "What I mean by that is..."
   - Topic vocab: (specific to the question)
   - Hedging: "I'd say...", "It seems to me that..."

4. SAMPLE SENTENCE(S)
   Write 2-3 complete, natural example sentences that directly address the question.

5. TIPS
   1 or 2 quick band-score tips (e.g. avoid repetition, use conditionals, extend answers).

Keep the tone encouraging. Use clear formatting (labels, bullet points)."""


@router.post("/chat")
async def speaking_chat(body: ChatRequest):
    """Proxy chat messages to OpenRouter for speaking coaching."""
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
        async with httpx.AsyncClient(timeout=15.0) as client:
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
_AI_TIMEOUT     = 15.0   # seconds


# ── audio helpers ─────────────────────────────────────────────────────────────

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


# ── Task A: pronunciation ─────────────────────────────────────────────────────

def _run_pronunciation(audio: np.ndarray) -> dict[str, float]:
    """Synchronous; runs in thread executor."""
    from ml.model_registry import get_pron_model
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
    return f"""IELTS Question: {question_text}
Candidate's transcript: {transcript}

Evaluate and return JSON with exactly this structure:
{{
  "grammar_score": <float 0-9>,
  "vocabulary_score": <float 0-9>,
  "grammar_errors": [
    {{"original": "...", "correction": "...", "explanation": "..."}}
  ],
  "vocabulary_feedback": [
    {{"word_used": "...", "better_alternative": "...", "reason": "..."}}
  ],
  "band_estimate": <float 4.0-9.0>,
  "overall_comment": "2-3 sentence summary in English",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."]
}}"""


async def _call_openrouter(question_text: str, transcript: str) -> dict[str, Any]:
    """Async HTTP call to OpenRouter (Claude 3 Haiku)."""
    payload = {
        "model": _AI_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(question_text, transcript)},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    headers = {
        "Authorization":  f"Bearer {_OPENROUTER_KEY}",
        "HTTP-Referer":   "http://localhost:3000",
        "Content-Type":   "application/json",
        "X-Title":        "LinguaIELTS",
    }
    async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
        resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()

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
  "grammar_score": <float 0-9>,
  "vocabulary_score": <float 0-9>,
  "grammar_errors": [
    {{"original": "...", "correction": "...", "explanation": "..."}}
  ],
  "vocabulary_feedback": [
    {{"word_used": "...", "better_alternative": "...", "reason": "..."}}
  ],
  "band_estimate": <float 4.0-9.0>,
  "overall_comment": "2-3 sentence summary in English",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."]
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


# ── endpoint ─────────────────────────────────────────────────────────────────

@router.post("/evaluate")
async def evaluate_speaking(
    file: UploadFile = File(...),
    question_text: str = Form(default=""),
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
        if transcript and not whisper_error:
            try:
                ai_result = await _call_openrouter(question_text, transcript)
            except Exception as exc:
                ai_error = str(exc)
                logger.warning("OpenRouter call failed: %s", exc)
        else:
            ai_error = whisper_error or "No transcript available"

        # ── merge response ────────────────────────────────────────────────
        pron_data = pron_result or {"accuracy": 0, "fluency": 0, "prosodic": 0, "total": 0}
        ai_data   = ai_result   or {}

        response: dict[str, Any] = {
            "pronunciation": pron_data,
            "transcript":       transcript,
            "word_timestamps":  (whisper_result or {}).get("word_timestamps", []),
            "grammar": {
                "score":  ai_data.get("grammar_score", 0),
                "errors": ai_data.get("grammar_errors", []),
            },
            "vocabulary": {
                "score":    ai_data.get("vocabulary_score", 0),
                "feedback": ai_data.get("vocabulary_feedback", []),
            },
            "band_estimate":   ai_data.get("band_estimate", pron_data.get("total", 0) / 10 * 9),
            "overall_comment": ai_data.get("overall_comment", ""),
            "strengths":       ai_data.get("strengths", []),
            "improvements":    ai_data.get("improvements", []),
        }
        if pron_error:
            response["pron_error"] = pron_error
        if whisper_error:
            response["whisper_error"] = whisper_error
        if ai_error:
            response["ai_error"] = ai_error

        return JSONResponse(content=response)

    finally:
        # Clean up temp files
        for p in {tmp_path, wav_path}:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass
