"""
Fallback: download audio with yt-dlp and transcribe with faster-whisper (sentence-level segments).

Uses yt-dlp Python API with Chrome TLS impersonation (curl_cffi) to bypass YouTube
bot-detection that blocks cloud server IPs (Hugging Face, AWS, GCP, etc.).
"""

from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.services.youtube_transcript_service import ytdlp_download

logger = logging.getLogger(__name__)


class AudioTranscriptionError(Exception):
    pass


def _download_audio(video_id: str, out_dir: Path) -> str:
    """
    Download audio using yt-dlp with Chrome impersonation and player-client fallbacks.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_template = str(out_dir / "%(id)s.%(ext)s")

    ydl_opts: dict = {
        "outtmpl": out_template,
        "no_playlist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
    }

    try:
        ytdlp_download(url, ydl_opts)
    except Exception as e:
        msg = str(e)
        if "Sign in to confirm" in msg or "not a bot" in msg.lower():
            raise AudioTranscriptionError(
                "YouTube chặn IP server khi tải audio (Whisper). "
                "Thử video có phụ đề EN (CC), hoặc export lại cookie mới vào ~/DATN/secrets/yt_cookies.txt."
            ) from e
        raise AudioTranscriptionError(f"yt-dlp failed: {e}") from e

    for ext in (".wav", ".m4a", ".webm", ".mp3", ".opus"):
        p = out_dir / f"{video_id}{ext}"
        if p.exists():
            return str(p)
    for f in out_dir.iterdir():
        if f.suffix in (".wav", ".m4a", ".webm", ".mp3", ".opus"):
            return str(f)
    raise AudioTranscriptionError("Downloaded audio file not found")


def _whisper_segments(wav_path: str) -> tuple[list[dict[str, Any]], str]:
    from ml.whisper_asr import transcribe_audio

    result = transcribe_audio(wav_path, language="en", word_timestamps=False)
    language = (result.get("language") or "en").split("-")[0].lower()

    raw: list[dict[str, Any]] = []
    for seg in result.get("segments", []):
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        raw.append({
            "text": text,
            "start": float(seg.get("start", 0)),
            "duration": max(0.1, float(seg.get("end", 0)) - float(seg.get("start", 0))),
        })

    if not raw:
        full = (result.get("transcript") or "").strip()
        if full:
            sentences = re.split(r"(?<=[.!?])\s+", full)
            t = 0.0
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                dur = max(2.0, len(s.split()) * 0.35)
                raw.append({"text": s, "start": t, "duration": dur})
                t += dur

    return raw, language


def transcribe_youtube_audio(video_id: str) -> tuple[list[dict[str, Any]], str]:
    """Download + Whisper. Returns raw caption-style entries."""
    with tempfile.TemporaryDirectory(prefix="shadowing_") as tmp:
        tmp_path = Path(tmp)
        audio_path = _download_audio(video_id, tmp_path)
        if not audio_path.endswith(".wav"):
            wav_out = str(tmp_path / "converted.wav")
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", wav_out],
                    check=True,
                    capture_output=True,
                    timeout=120,
                )
                audio_path = wav_out
            except Exception:
                pass
        return _whisper_segments(audio_path)
