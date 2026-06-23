"""Audio loading, conversion, Whisper and pronunciation helpers for speaking/shadowing."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_MIN_AUDIO_RMS: float = float(os.getenv("MIN_AUDIO_RMS", "0.003"))


def load_audio_16k(path: str) -> np.ndarray:
    """Load any audio file and resample to 16 kHz mono float32 (pydub, no librosa)."""
    from pydub import AudioSegment

    seg = AudioSegment.from_file(path)
    if seg.channels > 1:
        seg = seg.set_channels(1)
    if seg.frame_rate != 16_000:
        seg = seg.set_frame_rate(16_000)
    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
    max_val = float(2 ** (8 * seg.sample_width - 1))
    if max_val > 0:
        samples /= max_val
    return samples.astype(np.float32)


def convert_to_wav(src: str) -> str:
    """Convert webm/mp4/ogg to wav using ffmpeg via pydub."""
    from pydub import AudioSegment

    seg = AudioSegment.from_file(src)
    wav_path = src + ".wav"
    seg.export(wav_path, format="wav")
    return wav_path


def has_speech(audio: np.ndarray) -> bool:
    """Return False when the recording is near-silent (likely no speech)."""
    rms = float(np.sqrt(np.mean(audio.astype("float64") ** 2)))
    logger.debug("Audio RMS=%.5f (threshold=%.4f)", rms, _MIN_AUDIO_RMS)
    return rms >= _MIN_AUDIO_RMS


def run_pronunciation(audio: np.ndarray) -> dict[str, float]:
    """Scores 0-10 from wav2vec2-based scorer; zeros when near-silent."""
    if not has_speech(audio):
        logger.info(
            "Near-silent audio (RMS < %.4f) — skipping pronunciation model.",
            _MIN_AUDIO_RMS,
        )
        return {"accuracy": 0.0, "fluency": 0.0, "prosodic": 0.0, "total": 0.0, "_silent": True}

    from ml.model_registry import get_pron_model, pron_model_available

    if not pron_model_available():
        logger.warning("Pronunciation model unavailable — returning zero scores.")
        return {"accuracy": 0.0, "fluency": 0.0, "prosodic": 0.0, "total": 0.0, "_unavailable": True}

    net = get_pron_model()
    return net.predict(audio)


def run_whisper(wav_path: str, *, initial_prompt: str | None = None) -> dict[str, Any]:
    """Transcribe audio with word timestamps (faster-whisper)."""
    try:
        from ml.whisper_asr import transcribe_audio

        result = transcribe_audio(
            wav_path,
            language="en",
            word_timestamps=True,
            initial_prompt=initial_prompt,
            condition_on_previous_text=False,
        )
    except Exception as exc:
        raise RuntimeError(f"Whisper unavailable: {exc}") from exc
    return {
        "transcript": result.get("transcript", ""),
        "word_timestamps": result.get("word_timestamps", []),
    }
