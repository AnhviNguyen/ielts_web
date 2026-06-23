"""
faster-whisper ASR — replaces openai-whisper for Speaking, shadowing, and conversation.

Default: large-v3 + int8 on CPU (~2–3 GB RAM per worker) for better transcript quality
on Vietnamese-accent IELTS audio while using less memory than PyTorch Whisper large.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_WHISPER_MODEL_ID = os.getenv("WHISPER_MODEL_SIZE", "large-v3")
_WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
_WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
_WHISPER_CPU_THREADS = int(os.getenv("WHISPER_CPU_THREADS", "4"))
_WHISPER_NUM_WORKERS = int(os.getenv("WHISPER_NUM_WORKERS", "1"))

_model = None


def get_whisper_model():
    """Return the shared faster-whisper WhisperModel singleton."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        logger.info(
            "Loading faster-whisper '%s' (device=%s, compute_type=%s) …",
            _WHISPER_MODEL_ID,
            _WHISPER_DEVICE,
            _WHISPER_COMPUTE_TYPE,
        )
        _model = WhisperModel(
            _WHISPER_MODEL_ID,
            device=_WHISPER_DEVICE,
            compute_type=_WHISPER_COMPUTE_TYPE,
            cpu_threads=_WHISPER_CPU_THREADS,
            num_workers=_WHISPER_NUM_WORKERS,
        )
        logger.info("faster-whisper ready.")
    return _model


def transcribe_audio(
    wav_path: str,
    *,
    language: str = "en",
    word_timestamps: bool = False,
    initial_prompt: str | None = None,
    condition_on_previous_text: bool = False,
) -> dict[str, Any]:
    """
    Transcribe a WAV/audio file.

    Returns dict with keys: transcript, language, segments, word_timestamps.
    """
    model = get_whisper_model()
    kwargs: dict[str, Any] = {
        "language": language,
        "word_timestamps": word_timestamps,
        "condition_on_previous_text": condition_on_previous_text,
        "vad_filter": True,
    }
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt

    segments_iter, info = model.transcribe(wav_path, **kwargs)
    segments_list = list(segments_iter)

    transcript = "".join(seg.text for seg in segments_list).strip()
    language_detected = (getattr(info, "language", None) or language or "en").split("-")[0].lower()

    result_segments: list[dict[str, Any]] = []
    word_ts: list[dict[str, Any]] = []

    for seg in segments_list:
        text = (seg.text or "").strip()
        start = float(seg.start or 0)
        end = float(seg.end or 0)
        result_segments.append({"text": text, "start": start, "end": end})
        if word_timestamps and seg.words:
            for w in seg.words:
                word_ts.append(
                    {
                        "word": (w.word or "").strip(),
                        "start": round(float(w.start or 0), 3),
                        "end": round(float(w.end or 0), 3),
                        "score": round(float(w.probability or 1.0), 3),
                    }
                )

    return {
        "transcript": transcript,
        "language": language_detected,
        "segments": result_segments,
        "word_timestamps": word_ts,
    }
