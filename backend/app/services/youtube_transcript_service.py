"""
Fetch YouTube captions via yt-dlp with Chrome TLS impersonation (curl_cffi).

Replaces youtube-transcript-api which gets SSL-EOF blocked on cloud server IPs
(Hugging Face, AWS, GCP, etc.) because YouTube detects the Python TLS fingerprint.

Public interface is unchanged:
    fetch_youtube_transcript(video_id, preferred_langs) -> (segments, lang_code)
    TranscriptNotFoundError
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
import tempfile
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TranscriptNotFoundError(Exception):
    pass


# ---------------------------------------------------------------------------
# YouTube cookies (HF Secret → temp file)
# ---------------------------------------------------------------------------

_YT_COOKIES_PATH: str | None = None


def _get_yt_cookies_path() -> str | None:
    """
    Decode YouTube cookies from the HF Secret ``YT_COOKIES_BASE64`` into a
    temp file.  The file is created once and reused for the process lifetime.

    This keeps the cookies OUT of the Git repo — they only exist as an
    encrypted HF Secret and are decoded at runtime into /tmp.
    """
    global _YT_COOKIES_PATH
    if _YT_COOKIES_PATH is not None:
        return _YT_COOKIES_PATH

    b64 = os.environ.get("YT_COOKIES_BASE64")
    if not b64:
        return None

    try:
        raw = base64.b64decode(b64)
        # Ensure LF line endings (Windows exports may have CRLF)
        raw = raw.replace(b"\r\n", b"\n")
        # Strip UTF-8 BOM if present
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        with open(path, "wb") as f:
            f.write(raw)
        _YT_COOKIES_PATH = path

        # Debug: validate cookie file
        text = raw.decode("utf-8", errors="replace")
        lines = text.strip().split("\n")
        cookie_lines = [l for l in lines if l.strip() and not l.startswith("#")]
        has_header = any("Netscape" in l for l in lines[:3])
        logger.info(
            "YouTube cookies decoded to %s (%d bytes, %d cookie entries, netscape_header=%s, first_line=%r)",
            path, len(raw), len(cookie_lines), has_header, lines[0][:80] if lines else "<empty>",
        )
        if not has_header:
            logger.warning("Cookie file missing 'Netscape HTTP Cookie File' header — yt-dlp may reject it")
        if len(cookie_lines) < 3:
            logger.warning("Cookie file has very few entries (%d) — cookies may be incomplete", len(cookie_lines))
        return path
    except Exception:
        logger.exception("Failed to decode YT_COOKIES_BASE64")
        return None


# ---------------------------------------------------------------------------
# yt-dlp options
# ---------------------------------------------------------------------------

def _make_impersonate_target() -> Any:
    """
    Build an ImpersonateTarget for yt-dlp Python API.

    When using yt-dlp via CLI, a plain string like 'chrome' is auto-parsed.
    But the Python API requires the actual ImpersonateTarget object — passing
    a string causes an AssertionError in is_supported_target().

    Returns None if the import fails (curl_cffi not installed), so yt-dlp
    falls back to its default networking without impersonation.
    """
    try:
        from yt_dlp.networking.impersonate import ImpersonateTarget
        return ImpersonateTarget(client="chrome")
    except ImportError:
        logger.warning("curl_cffi or ImpersonateTarget not available — impersonation disabled")
        return None


def _ydl_opts(*, quiet: bool = True) -> dict[str, Any]:
    """
    Base yt-dlp options.
    'impersonate' makes yt-dlp use curl_cffi to mimic a real Chrome TLS
    handshake, bypassing YouTube's bot-detection on cloud server IPs.
    """
    opts: dict[str, Any] = {
        "quiet": quiet,
        "no_warnings": quiet,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "json3",   # json3 has start_time + text, easy to parse
    }
    target = _make_impersonate_target()
    if target is not None:
        opts["impersonate"] = target
    cookies = _get_yt_cookies_path()
    if cookies:
        opts["cookiefile"] = cookies
    return opts


# ---------------------------------------------------------------------------
# VTT / json3 parsers
# ---------------------------------------------------------------------------

def _parse_json3(raw_json: str | bytes) -> list[dict[str, Any]]:
    """
    Parse YouTube json3 subtitle format into [{text, start, duration}] list.

    json3 structure:
    {
      "events": [
        { "tStartMs": 1000, "dDurationMs": 2000,
          "segs": [{"utf8": "Hello "}, {"utf8": "world."}] },
        ...
      ]
    }
    """
    data = json.loads(raw_json)
    segments: list[dict[str, Any]] = []

    for event in data.get("events", []):
        segs = event.get("segs")
        if not segs:
            continue
        text = "".join((s.get("utf8") or "") for s in segs).strip()
        # Skip music markers / empty lines
        if not text or text in ("\n", "\r\n"):
            continue
        # Remove common music/noise markers like ♪, [Music], etc.
        text = re.sub(r"[\u266a\u266b]", "", text).strip()
        if not text:
            continue

        start_ms = event.get("tStartMs", 0)
        dur_ms = event.get("dDurationMs", 100)
        segments.append({
            "text": text,
            "start": start_ms / 1000.0,
            "duration": dur_ms / 1000.0,
        })

    return segments


def _parse_vtt(raw_vtt: str) -> list[dict[str, Any]]:
    """Fallback VTT parser for when json3 is not available."""
    segments: list[dict[str, Any]] = []
    time_re = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})"
    )
    tag_re = re.compile(r"<[^>]+>")

    lines = raw_vtt.splitlines()
    i = 0
    while i < len(lines):
        m = time_re.match(lines[i])
        if m:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = (int(x) for x in m.groups())
            start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
            end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
            duration = max(0.1, end - start)
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                cleaned = tag_re.sub("", lines[i]).strip()
                if cleaned:
                    text_lines.append(cleaned)
                i += 1
            text = " ".join(text_lines)
            if text:
                segments.append({"text": text, "start": start, "duration": duration})
        else:
            i += 1

    return segments


# ---------------------------------------------------------------------------
# Subtitle URL fetcher
# ---------------------------------------------------------------------------

async def _fetch_subtitle_url(url: str) -> str:
    """Download the subtitle file content from the given URL."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


# ---------------------------------------------------------------------------
# Main fetch function
# ---------------------------------------------------------------------------

def fetch_youtube_transcript(
    video_id: str,
    preferred_langs: list[str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Fetch YouTube captions via yt-dlp with Chrome TLS impersonation.

    Returns (raw_segments, language_code).
    Each segment: { text: str, start: float, duration: float }

    Raises TranscriptNotFoundError if no captions are available.
    """
    import yt_dlp  # noqa: PLC0415

    langs = preferred_langs or ["en", "en-US", "en-GB"]

    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = _ydl_opts()
    opts["subtitleslangs"] = langs

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        raise TranscriptNotFoundError(f"yt-dlp DownloadError: {e}") from e
    except Exception as e:
        logger.exception("yt-dlp extract_info failed | video=%s | error=%s", video_id, e)
        raise TranscriptNotFoundError(str(e)) from e

    if not info:
        raise TranscriptNotFoundError("yt-dlp returned empty info")

    # Determine subtitle source: prefer manual over auto-generated
    # Manual subtitles
    subtitles: dict = info.get("subtitles") or {}
    # Auto-generated captions
    auto_captions: dict = info.get("automatic_captions") or {}

    # Try each preferred language in order, manual first
    sub_url: str | None = None
    sub_lang: str = "en"
    sub_is_json3: bool = True

    def _pick_url(sub_dict: dict, lang_key: str) -> tuple[str | None, bool]:
        """Pick json3 URL first, then vtt, then any available."""
        entries: list[dict] = sub_dict.get(lang_key) or []
        for fmt in ("json3",):
            for e in entries:
                if e.get("ext") == fmt or (e.get("url", "").find("fmt=json3") != -1):
                    return e["url"], True
        for e in entries:
            if e.get("ext") == "vtt" or "vtt" in e.get("url", ""):
                return e["url"], False
        if entries:
            return entries[0].get("url"), False
        return None, False

    # Priority: manual EN → auto EN → manual vi → auto vi
    for lang in langs:
        # Check manual subtitles
        u, is_json3 = _pick_url(subtitles, lang)
        if u:
            sub_url = u
            sub_lang = lang.split("-")[0].lower()
            sub_is_json3 = is_json3
            logger.info("Manual subtitle found | video=%s lang=%s", video_id, lang)
            break
        # Check auto-generated
        u, is_json3 = _pick_url(auto_captions, lang)
        if u:
            sub_url = u
            sub_lang = lang.split("-")[0].lower()
            sub_is_json3 = is_json3
            logger.info("Auto-caption found | video=%s lang=%s", video_id, lang)
            break

    if not sub_url:
        raise TranscriptNotFoundError(
            f"No captions found for video {video_id} in languages {langs}"
        )

    # Download the subtitle file — we do this synchronously since this function
    # is already run in a thread (asyncio.to_thread in shadowing_service.py)
    try:
        import urllib.request
        with urllib.request.urlopen(sub_url, timeout=15) as resp:
            raw_content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise TranscriptNotFoundError(f"Failed to download subtitle file: {e}") from e

    # Parse
    if sub_is_json3:
        segments = _parse_json3(raw_content)
    else:
        segments = _parse_vtt(raw_content)

    if not segments:
        raise TranscriptNotFoundError(f"Subtitle file was empty after parsing | video={video_id}")

    logger.info(
        "YouTube transcript fetched via yt-dlp | video=%s lang=%s lines=%d",
        video_id,
        sub_lang,
        len(segments),
    )
    return segments, sub_lang
