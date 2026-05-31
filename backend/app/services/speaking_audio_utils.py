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
    """Load any audio file and resample to 16 kHz mono float32."""
    import librosa

    audio, _ = librosa.load(path, sr=16_000, mono=True)
    return audio.astype(np.float32)


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

    from ml.model_registry import get_pron_model

    pt_path = Path(os.getenv("PRON_MODEL_PATH", "model/pron_scorer_best.pt"))
    if not pt_path.is_absolute():
        pt_path = Path(__file__).resolve().parents[2] / pt_path
    if not pt_path.exists():
        raise FileNotFoundError(
            f"Pronunciation model not found at {pt_path}. "
            "Set PRON_MODEL_PATH or place pron_scorer_best.pt in backend/model/."
        )
    net = get_pron_model()
    return net.predict(audio)


def run_whisper(wav_path: str, *, initial_prompt: str | None = None) -> dict[str, Any]:
    """Transcribe audio with word timestamps."""
    from ml.model_registry import get_whisper_model

    model = get_whisper_model()
    kwargs: dict[str, Any] = {
        "language": "en",
        "word_timestamps": True,
        "verbose": False,
        "condition_on_previous_text": False,
        "fp16": False,
    }
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt
    result = model.transcribe(wav_path, **kwargs)
    transcript = result.get("text", "").strip()
    word_ts: list[dict] = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            word_ts.append(
                {
                    "word": w.get("word", "").strip(),
                    "start": round(w.get("start", 0.0), 3),
                    "end": round(w.get("end", 0.0), 3),
                    "score": round(w.get("probability", 1.0), 3),
                }
            )
    return {"transcript": transcript, "word_timestamps": word_ts}
