"""
Fallback: download audio with yt-dlp and transcribe with Whisper (sentence-level segments).

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

logger = logging.getLogger(__name__)


class AudioTranscriptionError(Exception):
    pass


def _download_audio(video_id: str, out_dir: Path) -> str:
    """
    Download audio using yt-dlp Python API with Chrome impersonation.

    Using the Python API (not subprocess) lets us pass 'impersonate' option,
    which makes curl_cffi spoof a Chrome TLS fingerprint so YouTube doesn't
    block the connection with SSL-EOF on cloud server IP ranges.
    """
    import yt_dlp  # noqa: PLC0415

    url = f"https://www.youtube.com/watch?v={video_id}"
    out_template = str(out_dir / "%(id)s.%(ext)s")

    # Build ImpersonateTarget — yt-dlp Python API requires the object, not a string
    try:
        from yt_dlp.networking.impersonate import ImpersonateTarget
        impersonate_target = ImpersonateTarget(client="chrome")
    except ImportError:
        impersonate_target = None

    ydl_opts: dict = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
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
    if impersonate_target is not None:
        ydl_opts["impersonate"] = impersonate_target

    # Reuse YouTube cookies from HF Secret (same decode logic as transcript service)
    from app.services.youtube_transcript_service import _get_yt_cookies_path
    cookies = _get_yt_cookies_path()
    if cookies:
        ydl_opts["cookiefile"] = cookies

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        raise AudioTranscriptionError(f"yt-dlp failed: {e}") from e
    except Exception as e:
        raise AudioTranscriptionError(f"yt-dlp unexpected error: {e}") from e

    for ext in (".wav", ".m4a", ".webm", ".mp3", ".opus"):
        p = out_dir / f"{video_id}{ext}"
        if p.exists():
            return str(p)
    for f in out_dir.iterdir():
        if f.suffix in (".wav", ".m4a", ".webm", ".mp3", ".opus"):
            return str(f)
    raise AudioTranscriptionError("Downloaded audio file not found")


def _whisper_segments(wav_path: str) -> tuple[list[dict[str, Any]], str]:
    from ml.model_registry import get_whisper_model

    model = get_whisper_model()
    result = model.transcribe(wav_path, verbose=False)
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
        full = (result.get("text") or "").strip()
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
