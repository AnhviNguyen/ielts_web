"""Shadowing pronunciation check — Whisper + pron_scorer_best.pt."""

from __future__ import annotations

import asyncio
import logging
import re
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def _normalize_token(w: str) -> str:
    return re.sub(r"[^\w']", "", w.lower())


def _align_words(spoken: str, target: str) -> dict:
    target_tokens = [_normalize_token(w) for w in target.split() if _normalize_token(w)]
    spoken_tokens = [_normalize_token(w) for w in spoken.split() if _normalize_token(w)]
    target_words = target.split()

    word_results = []
    correct_count = 0
    max_len = max(len(target_tokens), len(spoken_tokens))
    for i in range(max_len):
        t = target_tokens[i] if i < len(target_tokens) else None
        s = spoken_tokens[i] if i < len(spoken_tokens) else None
        word = target_words[i] if i < len(target_words) else (spoken.split()[i] if i < len(spoken.split()) else "")
        ok = bool(t and s and t == s)
        if ok:
            correct_count += 1
        word_results.append({
            "word": word or t or s or "",
            "ok": ok,
            "spoken": spoken.split()[i] if i < len(spoken.split()) else None,
        })

    score = round((correct_count / len(target_tokens)) * 100) if target_tokens else 0
    wrong = [w["word"] for w in word_results if not w["ok"]]
    return {
        "word_results": word_results,
        "score": score,
        "wrong": wrong,
        "correct_count": correct_count,
        "total_words": len(target_tokens),
    }


async def check_pronunciation_from_bytes(
    audio_bytes: bytes,
    filename: str,
    target_text: str,
) -> dict:
    """Run Whisper + pronunciation model; align transcript to target sentence."""
    from app.services.speaking_audio_utils import (
        convert_to_wav,
        has_speech,
        load_audio_16k,
        run_pronunciation,
        run_whisper,
    )

    suffix = Path(filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    wav_path = tmp_path
    try:
        if suffix.lower() != ".wav":
            try:
                wav_path = convert_to_wav(tmp_path)
            except Exception as exc:
                logger.warning("wav convert failed: %s", exc)

        audio_16k = await asyncio.to_thread(load_audio_16k, wav_path)
        if not has_speech(audio_16k):
            raise ValueError(
                "Không phát hiện giọng nói trong bản ghi. Hãy nói to hơn hoặc kiểm tra micro."
            )

        pron_result, whisper_result = await asyncio.gather(
            asyncio.to_thread(run_pronunciation, audio_16k),
            asyncio.to_thread(run_whisper, wav_path),
        )

        transcript = (whisper_result or {}).get("transcript", "").strip()
        alignment = _align_words(transcript, target_text)

        pron = pron_result or {}
        model_total = float(pron.get("total", 0) or 0)
        # Blend text alignment (0-100) with model score (0-10 → 0-100)
        combined = round(alignment["score"] * 0.55 + min(100, model_total * 10) * 0.45)

        return {
            "score": combined,
            "text_score": alignment["score"],
            "transcript": transcript,
            "target_text": target_text,
            "word_results": alignment["word_results"],
            "wrong_words": alignment["wrong"],
            "pronunciation": {
                "accuracy": float(pron.get("accuracy", 0)),
                "fluency": float(pron.get("fluency", 0)),
                "prosodic": float(pron.get("prosodic", 0)),
                "total": model_total,
            },
        }
    finally:
        for p in {tmp_path, wav_path}:
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass
