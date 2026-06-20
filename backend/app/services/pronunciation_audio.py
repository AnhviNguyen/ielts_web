"""Convert uploaded browser audio to mono float32 waveform for SpeechBrain scoring."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np


def prepare_speech_waveform(waveform: np.ndarray, sample_rate: int) -> np.ndarray:
    """Peak-normalize, trim silence, pad short clips — helps ASR on browser recordings."""
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent

    if waveform.size == 0:
        return waveform

    audio = waveform.astype(np.float32)
    peak = float(np.max(np.abs(audio)))
    if peak > 1e-6:
        audio = (audio / peak) * 0.92

    samples_int = (np.clip(audio, -1.0, 1.0) * 32_767).astype(np.int16)
    seg = AudioSegment(
        samples_int.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1,
    )

    try:
        thresh = seg.dBFS - 14 if seg.dBFS != float("-inf") else -40
        nonsilent = detect_nonsilent(seg, min_silence_len=100, silence_thresh=thresh, seek_step=10)
        if nonsilent:
            start = max(0, nonsilent[0][0] - 40)
            end = min(len(seg), nonsilent[-1][1] + 60)
            seg = seg[start:end]
    except Exception:
        pass

    min_ms = 700
    if len(seg) < min_ms:
        seg = seg + AudioSegment.silent(duration=min_ms - len(seg), frame_rate=sample_rate)

    out = np.array(seg.get_array_of_samples(), dtype=np.float32) / 32_767.0
    return out.astype(np.float32)


def audio_bytes_to_waveform(audio_bytes: bytes, filename: str) -> tuple[np.ndarray, int]:
    """Load WebM/WAV/OGG bytes via pydub; validate duration; return (waveform, sample_rate)."""
    from pydub import AudioSegment

    if len(audio_bytes) < 64:
        raise ValueError("File ghi âm quá ngắn hoặc rỗng.")

    suffix = (Path(filename or "audio.webm").suffix or ".webm").lower().lstrip(".")
    fmt = None if suffix in {"webm", "bin"} else suffix

    seg = AudioSegment.from_file(BytesIO(audio_bytes), format=fmt)
    duration_s = len(seg) / 1000.0
    if duration_s < 0.3:
        raise ValueError("Âm thanh quá ngắn (<0.3 giây). Hãy nói rõ hơn.")
    if duration_s > 10.0:
        raise ValueError("Âm thanh quá dài (>10 giây). Hãy chỉ nói một từ.")

    if seg.channels > 1:
        seg = seg.set_channels(1)
    if seg.frame_rate != 16_000:
        seg = seg.set_frame_rate(16_000)

    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
    max_val = float(2 ** (8 * seg.sample_width - 1))
    if max_val > 0:
        samples /= max_val

    samples = prepare_speech_waveform(samples, 16_000)
    return samples, 16_000
