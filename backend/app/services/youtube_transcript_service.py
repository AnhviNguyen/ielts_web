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
import html
import http.cookiejar
import io
import json
import logging
import os
import re
import tempfile
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TranscriptNotFoundError(Exception):
    pass


# ---------------------------------------------------------------------------
# YouTube cookies (HF Secret → temp file)
# ---------------------------------------------------------------------------

_YT_COOKIES_PATH: str | None = None

_NETSCAPE_HEADER = (
    "# Netscape HTTP Cookie File\n"
    "# https://curl.haxx.se/rfc/cookie_spec.html\n"
    "# This is a generated file! Do not edit.\n\n"
)


def _normalize_cookie_bytes(raw: bytes) -> bytes:
    """Strip BOM/CRLF and keep only YouTube/Google cookies for yt-dlp."""
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8", errors="replace")

    kept: dict[tuple[str, str], str] = {}
    for line in text.split("\n"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain = parts[0].lower().lstrip(".")
        if domain not in ("youtube.com", "google.com"):
            continue
        kept[(parts[0], parts[5])] = line

    body = "\n".join(kept.values())
    if body:
        text = _NETSCAPE_HEADER + body + "\n"
    elif not any("Netscape HTTP Cookie File" in line for line in text.split("\n")[:5]):
        text = _NETSCAPE_HEADER + text.lstrip("\n")
    return text.encode("utf-8")


def _is_bot_check_error(message: str) -> bool:
    msg = message.lower()
    return (
        "sign in to confirm" in msg
        or "not a bot" in msg
        or "login_required" in msg
        or "bot detection" in msg
        or "requestblocked" in msg
        or "ipblocked" in msg
        or "blocking requests from your ip" in msg
    )


def cookies_debug_info() -> dict[str, Any]:
    """Lightweight status for ops/debug endpoints."""
    path = _get_yt_cookies_path()
    info: dict[str, Any] = {
        "loaded": path is not None,
        "path": path,
        "env_file": (os.environ.get("YT_COOKIES_FILE") or "").strip() or None,
        "has_base64": bool(os.environ.get("YT_COOKIES_BASE64")),
        "has_proxy": _youtube_proxy_config() is not None,
        "has_supadata": bool(_supadata_api_key()),
        "has_apify": bool(_apify_api_token()),
    }
    if path and os.path.isfile(path):
        info["bytes"] = os.path.getsize(path)
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
            info["entries"] = sum(
                1 for line in text.split("\n")
                if line.strip() and not line.startswith("#") and "\t" in line
            )
            info["has_login_info"] = "LOGIN_INFO" in text
        except OSError:
            pass
    return info


def _cookies_cache_path() -> str:
    """Writable path for normalized cookies (gunicorn runs as appuser, not root)."""
    override = (os.environ.get("YT_COOKIES_CACHE_FILE") or "").strip()
    if override:
        parent = os.path.dirname(override)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return override
    for candidate in (
        os.path.join(os.path.expanduser("~"), ".cache", "yt_cookies.txt"),
        "/app/data/yt_cookies_normalized.txt",
        os.path.join(tempfile.gettempdir(), f"yt_cookies_{getattr(os, 'getuid', lambda: 0)()}.txt"),
    ):
        parent = os.path.dirname(candidate)
        try:
            os.makedirs(parent, exist_ok=True)
            return candidate
        except OSError:
            continue
    return os.path.join(tempfile.gettempdir(), "yt_cookies.txt")


def _write_normalized_cookies(raw: bytes) -> str:
    normalized = _normalize_cookie_bytes(raw)
    path = _cookies_cache_path()
    with open(path, "wb") as f:
        f.write(normalized)
    text = normalized.decode("utf-8", errors="replace")
    cookie_lines = [l for l in text.split("\n") if l.strip() and not l.startswith("#")]
    logger.info(
        "YouTube cookies normalized to %s (%d bytes, %d entries)",
        path, len(normalized), len(cookie_lines),
    )
    return path


def _get_yt_cookies_path() -> str | None:
    """
    Resolve YouTube cookies for yt-dlp.

    Priority:
    1. ``YT_COOKIES_FILE`` — path to Netscape cookies.txt (e.g. mounted in Docker)
    2. ``YT_COOKIES_BASE64`` — HF Secret / env var decoded to a temp file
    """
    global _YT_COOKIES_PATH
    if _YT_COOKIES_PATH is not None:
        return _YT_COOKIES_PATH

    file_path = (os.environ.get("YT_COOKIES_FILE") or "").strip()
    if file_path and os.path.isfile(file_path) and os.access(file_path, os.R_OK):
        # Pre-baked cache from Docker entrypoint — appuser reads, no rewrite needed
        if file_path.startswith("/home/appuser/.cache/") or file_path.startswith("/app/data/"):
            _YT_COOKIES_PATH = file_path
            logger.info("Using YouTube cookies at %s", file_path)
            return file_path
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
            _YT_COOKIES_PATH = _write_normalized_cookies(raw)
            return _YT_COOKIES_PATH
        except Exception:
            logger.exception("Failed to read YT_COOKIES_FILE at %s", file_path)
            return None

    secrets_path = "/app/secrets/yt_cookies.txt"
    if os.path.isfile(secrets_path):
        try:
            with open(secrets_path, "rb") as f:
                raw = f.read()
            _YT_COOKIES_PATH = _write_normalized_cookies(raw)
            return _YT_COOKIES_PATH
        except Exception:
            logger.exception("Failed to read secrets cookies at %s", secrets_path)
            return None

    b64 = os.environ.get("YT_COOKIES_BASE64")
    if not b64:
        return None

    try:
        raw = base64.b64decode(b64)
        _YT_COOKIES_PATH = _write_normalized_cookies(raw)
        return _YT_COOKIES_PATH
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
        "ignore_no_formats_error": True,
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
    proxy_url = _youtube_proxy_url()
    if proxy_url:
        opts["proxy"] = proxy_url
    return opts


def _player_client_fallbacks() -> list[list[str]]:
    """Try multiple Innertube clients — datacenter IPs often need cookies + fallbacks."""
    if _get_yt_cookies_path():
        return [
            ["web_safari", "mweb"],
            ["tv", "web_safari"],
            ["tv", "web"],
            ["mweb"],
        ]
    return [
        ["web_safari", "mweb"],
        ["tv", "web_safari"],
        ["tv_simply"],
        ["web_embedded"],
    ]


def _download_player_client_fallbacks() -> list[list[str]]:
    """Player clients that expose downloadable audio (web_safari HLS avoids PO-token blocks)."""
    if _get_yt_cookies_path():
        return [
            ["web_creator"],
            ["web_safari"],
            ["android_vr"],
            ["web_safari", "mweb"],
            ["mweb"],
            ["tv", "web_safari"],
            ["tv", "web"],
            ["ios"],
        ]
    return [
        ["web_safari"],
        ["web_safari", "mweb"],
        ["mweb"],
        ["tv_simply"],
    ]


_DOWNLOAD_FORMAT_FALLBACKS = (
    "ba/b",
    "bestaudio[protocol^=m3u8]/bestaudio/best",
    "bestaudio/best",
    "best",
)


def _with_player_clients(opts: dict[str, Any], clients: list[str]) -> dict[str, Any]:
    merged = dict(opts)
    extractor_args = dict(merged.get("extractor_args") or {})
    youtube_args = dict(extractor_args.get("youtube") or {})
    youtube_args["player_client"] = clients
    extractor_args["youtube"] = youtube_args
    merged["extractor_args"] = extractor_args
    return merged


def _without_impersonate(opts: dict[str, Any]) -> dict[str, Any]:
    merged = dict(opts)
    merged.pop("impersonate", None)
    return merged


def _ytdlp_run_extract(url: str, opts: dict[str, Any]) -> dict[str, Any]:
    """extract_info with player-client fallbacks; last resort drops TLS impersonation."""
    import yt_dlp  # noqa: PLC0415

    last_error: Exception | None = None
    clients_list = list(_player_client_fallbacks())
    attempts: list[dict[str, Any]] = [_with_player_clients(opts, c) for c in clients_list]
    attempts.append(_without_impersonate(opts))

    for attempt_opts in attempts:
        try:
            with yt_dlp.YoutubeDL(attempt_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if info:
                clients = (
                    attempt_opts.get("extractor_args", {})
                    .get("youtube", {})
                    .get("player_client")
                )
                logger.info("yt-dlp extract_info ok | clients=%s impersonate=%s", clients, "impersonate" in attempt_opts)
                return info
        except yt_dlp.utils.DownloadError as e:
            last_error = e
            logger.warning("yt-dlp extract_info failed | %s", e)
        except Exception as e:
            last_error = e
            logger.warning("yt-dlp extract_info error | %s", e)

    if last_error:
        raise last_error
    raise TranscriptNotFoundError("yt-dlp returned empty info")


def ytdlp_extract_info(url: str, extra_opts: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run yt-dlp extract_info with player-client fallbacks for cloud/datacenter IPs."""
    base = _ydl_opts()
    if extra_opts:
        base.update(extra_opts)
    return _ytdlp_run_extract(url, base)


def ytdlp_download(url: str, extra_opts: dict[str, Any]) -> None:
    """Run yt-dlp download with player-client and format fallbacks."""
    import yt_dlp  # noqa: PLC0415

    base = _ydl_opts(quiet=True)
    base["skip_download"] = False
    for key in ("writesubtitles", "writeautomaticsub", "subtitlesformat", "ignore_no_formats_error"):
        base.pop(key, None)
    base.update(extra_opts)

    last_error: Exception | None = None
    for clients in _download_player_client_fallbacks():
        for fmt in _DOWNLOAD_FORMAT_FALLBACKS:
            opts = _with_player_clients(base, clients)
            opts["format"] = fmt
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                logger.info("yt-dlp download ok | clients=%s format=%s", clients, fmt)
                return
            except yt_dlp.utils.DownloadError as e:
                last_error = e
                err = str(e)
                if "No video formats found" in err or "Requested format is not available" in err:
                    logger.warning(
                        "yt-dlp download no formats | clients=%s format=%s",
                        clients, fmt,
                    )
                    continue
                logger.warning("yt-dlp download failed | clients=%s format=%s | %s", clients, fmt, e)
            except Exception as e:
                last_error = e
                logger.warning("yt-dlp download error | clients=%s format=%s | %s", clients, fmt, e)

    if last_error:
        raise last_error
    raise RuntimeError("yt-dlp download failed with no error detail")


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


def _parse_timedtext_xml3(raw_xml: str) -> list[dict[str, Any]]:
    """Parse YouTube timedtext XML format 3: <p t=\"ms\" d=\"ms\">text</p>."""
    segments: list[dict[str, Any]] = []
    tag_re = re.compile(r"<[^>]+>")
    for m in re.finditer(r'<p\s+t="(\d+)"\s+d="(\d+)"[^>]*>(.*?)</p>', raw_xml, re.DOTALL):
        t_ms, d_ms, text = int(m.group(1)), int(m.group(2)), m.group(3)
        text = html.unescape(tag_re.sub("", text)).strip()
        if text:
            segments.append({
                "text": text,
                "start": t_ms / 1000.0,
                "duration": max(0.1, d_ms / 1000.0),
            })
    if segments:
        return segments
    for m in re.finditer(
        r'<text\s+start="([\d.]+)"\s+dur="([\d.]+)"[^>]*>(.*?)</text>',
        raw_xml,
        re.DOTALL,
    ):
        start, duration, text = float(m.group(1)), float(m.group(2)), m.group(3)
        text = html.unescape(tag_re.sub("", text)).strip()
        if text:
            segments.append({
                "text": text,
                "start": start,
                "duration": max(0.1, duration),
            })
    return segments


def parse_timedtext_content(raw_content: str) -> list[dict[str, Any]]:
    """Detect json3 / XML timedtext / VTT and return raw caption segments."""
    text = (raw_content or "").strip()
    if not text:
        return []
    if text.startswith("{"):
        return _parse_json3(text)
    if "<timedtext" in text or "<p t=" in text or "<text start=" in text:
        return _parse_timedtext_xml3(text)
    return _parse_vtt(text)


_INNERTUBE_ANDROID_CLIENT = {
    "clientName": "ANDROID",
    "clientVersion": "20.10.38",
    "hl": "en",
    "gl": "US",
}


def _httpx_yt_client_kwargs() -> dict[str, Any]:
    """Cookies + optional proxy for direct YouTube HTTP calls."""
    kwargs: dict[str, Any] = {}
    cookie_path = _get_yt_cookies_path()
    if cookie_path and os.path.isfile(cookie_path):
        try:
            jar = http.cookiejar.MozillaCookieJar(cookie_path)
            jar.load(ignore_discard=True, ignore_expires=True)
            cookies = httpx.Cookies()
            for c in jar:
                cookies.set(c.name, (c.value or "").strip(), domain=c.domain, path=c.path)
            kwargs["cookies"] = cookies
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load YT cookies: %s", exc)
    proxy = _youtube_proxy_url()
    if proxy:
        kwargs["proxy"] = proxy
    return kwargs


def _innertube_player_response(video_id: str) -> dict[str, Any]:
    endpoint = "https://www.youtube.com/youtubei/v1/player"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "com.google.android.youtube/20.10.38 "
            "(Linux; U; Android 14) gzip"
        ),
    }
    client_kwargs = _httpx_yt_client_kwargs()
    attempts = [
        {"context": {"client": _INNERTUBE_ANDROID_CLIENT}, "videoId": video_id},
    ]
    if client_kwargs.get("cookies"):
        attempts.append({
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20260618.05.00",
                    "hl": "en",
                    "gl": "US",
                }
            },
            "videoId": video_id,
        })

    last_status: str | None = None
    with httpx.Client(timeout=20.0, **client_kwargs) as client:
        for body in attempts:
            url = endpoint
            if body["context"]["client"]["clientName"] == "WEB":
                url += "?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
            r = client.post(url, json=body, headers=headers)
            r.raise_for_status()
            player = r.json()
            tracks = (
                player.get("captions", {})
                .get("playerCaptionsTracklistRenderer", {})
                .get("captionTracks", [])
            )
            if tracks:
                return player
            last_status = (player.get("playabilityStatus") or {}).get("status")
    raise TranscriptNotFoundError(
        f"No caption tracks for {video_id}"
        + (f" (playability={last_status})" if last_status else "")
    )


def _pick_caption_track(
    tracks: list[dict[str, Any]],
    langs: list[str],
) -> dict[str, Any] | None:
    if not tracks:
        return None
    lowered = [lang.lower() for lang in langs]
    for lang in lowered:
        for track in tracks:
            code = (track.get("languageCode") or "").lower()
            if code == lang or code.startswith(f"{lang}-"):
                if track.get("kind") != "asr":
                    return track
    for lang in lowered:
        for track in tracks:
            code = (track.get("languageCode") or "").lower()
            if code == lang or code.startswith(f"{lang}-"):
                return track
    return tracks[0]


def _list_preferred_caption_tracks(
    tracks: list[dict[str, Any]],
    langs: list[str],
) -> list[dict[str, Any]]:
    """Return EN tracks in preference order (manual before auto-generated)."""
    if not tracks:
        return []
    lowered = [lang.lower() for lang in langs]
    ordered: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    def _add(track: dict[str, Any]) -> None:
        url = track.get("baseUrl") or ""
        if url and url not in seen_urls:
            seen_urls.add(url)
            ordered.append(track)

    for lang in lowered:
        for track in tracks:
            code = (track.get("languageCode") or "").lower()
            if (code == lang or code.startswith(f"{lang}-")) and track.get("kind") != "asr":
                _add(track)
    for lang in lowered:
        for track in tracks:
            code = (track.get("languageCode") or "").lower()
            if code == lang or code.startswith(f"{lang}-"):
                _add(track)
    for track in tracks:
        _add(track)
    return ordered


def _caption_url_from_track(track: dict[str, Any]) -> tuple[str, str]:
    lang = (track.get("languageCode") or "en").split("-")[0].lower()
    caption_url = track["baseUrl"]
    if "fmt=" not in caption_url:
        sep = "&" if "?" in caption_url else "?"
        caption_url = f"{caption_url}{sep}fmt=json3"
    return caption_url, lang


_WATCH_PAGE_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _extract_player_response_from_watch_page(video_id: str) -> dict[str, Any] | None:
    """Parse ytInitialPlayerResponse from watch HTML (works when InnerTube POST is blocked)."""
    kwargs = _httpx_yt_client_kwargs()
    with httpx.Client(timeout=25.0, follow_redirects=True, **kwargs) as client:
        r = client.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"User-Agent": _WATCH_PAGE_UA, "Accept-Language": "en-US,en;q=0.9"},
        )
        r.raise_for_status()
        html = r.text

    for marker in ("var ytInitialPlayerResponse = ", "ytInitialPlayerResponse = "):
        idx = html.find(marker)
        if idx < 0:
            continue
        start = idx + len(marker)
        depth = 0
        for i, ch in enumerate(html[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html[start : i + 1])
                    except json.JSONDecodeError:
                        break
    return None


def _caption_tracks_from_player(player: dict[str, Any]) -> list[dict[str, Any]]:
    return (
        player.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )


def _resolve_player_response(video_id: str) -> dict[str, Any]:
    """InnerTube first; fall back to watch-page HTML on datacenter IP blocks."""
    last_error: Exception | None = None
    try:
        player = _innertube_player_response(video_id)
        if _caption_tracks_from_player(player):
            return player
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        logger.warning("InnerTube player failed for %s: %s", video_id, exc)

    player = _extract_player_response_from_watch_page(video_id)
    if player:
        tracks = _caption_tracks_from_player(player)
        if tracks:
            logger.info("YouTube captions via watch-page HTML | video=%s", video_id)
            return player
        status = (player.get("playabilityStatus") or {}).get("status")
        if status == "LOGIN_REQUIRED":
            raise TranscriptNotFoundError(
                f"YouTube chặn IP server cho video {video_id} (LOGIN_REQUIRED). "
                "Thêm Webshare free (YOUTUBE_WEBSHARE_USERNAME/PASSWORD trong .env) "
                "hoặc thử video khác có CC."
            )

    if last_error and not isinstance(last_error, TranscriptNotFoundError):
        raise TranscriptNotFoundError(
            f"Could not resolve caption tracks for {video_id}: {last_error}"
        ) from last_error
    raise TranscriptNotFoundError(f"No caption tracks for {video_id}")


def get_innertube_caption_url(
    video_id: str,
    preferred_langs: list[str] | None = None,
) -> tuple[str, str]:
    """
    Return a signed caption URL (InnerTube, watch-page HTML, cookies/proxy when set).
    """
    langs = _expand_lang_prefs(preferred_langs or ["en"])
    player = _resolve_player_response(video_id)
    tracks = _caption_tracks_from_player(player)
    track = _pick_caption_track(tracks, langs)
    if not track or not track.get("baseUrl"):
        raise TranscriptNotFoundError(f"No caption tracks for {video_id}")
    return _caption_url_from_track(track)


_SUPADATA_BASE = "https://api.supadata.ai/v1"


def _supadata_api_key() -> str | None:
    from app.core.config import settings

    key = (settings.SUPADATA_API_KEY or os.environ.get("SUPADATA_API_KEY") or "").strip()
    return key or None


def _segments_from_supadata_content(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, str):
        text = content.strip()
        if not text:
            return []
        return [{"text": text, "start": 0.0, "duration": max(0.1, len(text.split()) * 0.35)}]
    if not isinstance(content, list):
        return []
    segments: list[dict[str, Any]] = []
    for chunk in content:
        if not isinstance(chunk, dict):
            continue
        text = (chunk.get("text") or "").strip()
        if not text:
            continue
        segments.append({
            "text": text,
            "start": float(chunk.get("offset") or 0) / 1000.0,
            "duration": max(0.1, float(chunk.get("duration") or 100) / 1000.0),
        })
    return segments


def _poll_supadata_transcript_job(
    client: httpx.Client,
    job_id: str,
    headers: dict[str, str],
    *,
    max_wait_s: float = 120.0,
) -> tuple[list[dict[str, Any]], str]:
    deadline = time.monotonic() + max_wait_s
    while time.monotonic() < deadline:
        r = client.get(f"{_SUPADATA_BASE}/transcript/{job_id}", headers=headers)
        r.raise_for_status()
        data = r.json()
        status = (data.get("status") or "").lower()
        if status == "completed":
            segments = _segments_from_supadata_content(data.get("content"))
            if not segments:
                raise TranscriptNotFoundError("Supadata job returned empty transcript")
            lang = (data.get("lang") or "en").split("-")[0].lower()
            return segments, lang
        if status == "failed":
            raise TranscriptNotFoundError(
                data.get("error") or data.get("message") or "Supadata transcript job failed"
            )
        time.sleep(1.0)
    raise TranscriptNotFoundError("Supadata transcript job timed out")


def _fetch_transcript_via_supadata(
    video_id: str,
    langs: list[str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Fetch YouTube transcript via Supadata API (works on cloud VPS IPs)."""
    api_key = _supadata_api_key()
    if not api_key:
        raise TranscriptNotFoundError("Supadata API key not configured")

    preferred = _expand_lang_prefs(langs or ["en"])
    headers = {"x-api-key": api_key}
    last_error: TranscriptNotFoundError | None = None

    with httpx.Client(timeout=90.0) as client:
        for lang in preferred:
            lang_code = lang.split("-")[0].lower()
            try:
                r = client.get(
                    f"{_SUPADATA_BASE}/youtube/transcript",
                    params={"videoId": video_id, "lang": lang_code, "text": "false"},
                    headers=headers,
                )
                if r.status_code == 202:
                    job_id = (r.json() or {}).get("jobId")
                    if not job_id:
                        raise TranscriptNotFoundError("Supadata returned async job without jobId")
                    segments, resolved = _poll_supadata_transcript_job(client, job_id, headers)
                    logger.info(
                        "YouTube transcript via Supadata (async) | video=%s lang=%s lines=%d",
                        video_id,
                        resolved,
                        len(segments),
                    )
                    return segments, resolved

                if r.status_code in (404, 206):
                    detail = (r.json() or {}).get("message") or r.text[:200]
                    raise TranscriptNotFoundError(f"Supadata: {detail}")

                r.raise_for_status()
                data = r.json()
                segments = _segments_from_supadata_content(data.get("content"))
                if not segments:
                    raise TranscriptNotFoundError(f"Supadata returned empty transcript for {video_id}")
                resolved = (data.get("lang") or lang_code).split("-")[0].lower()
                logger.info(
                    "YouTube transcript via Supadata | video=%s lang=%s lines=%d",
                    video_id,
                    resolved,
                    len(segments),
                )
                return segments, resolved
            except TranscriptNotFoundError as exc:
                last_error = exc
                logger.warning("Supadata lang=%s failed | video=%s | %s", lang_code, video_id, exc)

    if last_error:
        raise last_error
    raise TranscriptNotFoundError(f"No Supadata transcript for {video_id}")


_APIFY_BASE = "https://api.apify.com/v2"


def _apify_api_token() -> str | None:
    from app.core.config import settings

    token = (settings.APIFY_API_TOKEN or os.environ.get("APIFY_API_TOKEN") or "").strip()
    return token or None


def _apify_actor_id() -> str:
    from app.core.config import settings

    actor = (settings.APIFY_YOUTUBE_TRANSCRIPT_ACTOR or "").strip()
    return actor or "codepoetry~youtube-transcript-ai-scraper"


def _segments_from_apify_transcript_json(chunks: Any) -> list[dict[str, Any]]:
    if not isinstance(chunks, list):
        return []
    segments: list[dict[str, Any]] = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        text = (chunk.get("text") or "").strip()
        if not text:
            continue
        start = float(chunk.get("start") or 0)
        end = chunk.get("end")
        if end is not None:
            duration = max(0.1, float(end) - start)
        else:
            duration = max(0.1, float(chunk.get("duration") or 0.1))
        segments.append({"text": text, "start": start, "duration": duration})
    return segments


def _fetch_transcript_via_apify(
    video_id: str,
    langs: list[str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Fetch YouTube transcript via Apify actor (captions-first, no AI fallback)."""
    token = _apify_api_token()
    if not token:
        raise TranscriptNotFoundError("Apify API token not configured")

    preferred = _expand_lang_prefs(langs or ["en"])
    lang_codes: list[str] = []
    for lang in preferred:
        code = lang.split("-")[0].lower()
        if code not in lang_codes:
            lang_codes.append(code)

    actor = _apify_actor_id()
    payload = {
        "startUrls": [{"url": f"https://www.youtube.com/watch?v={video_id}"}],
        "languages": lang_codes[:5] or ["en"],
        "subType": "both",
        "outputFormats": ["json"],
        "enableAiFallback": False,
        "maxResults": 1,
    }

    with httpx.Client(timeout=180.0) as client:
        r = client.post(
            f"{_APIFY_BASE}/acts/{actor}/run-sync-get-dataset-items",
            params={"token": token, "timeout": 120},
            json=payload,
        )
        if r.status_code == 401:
            raise TranscriptNotFoundError("Apify: unauthorized API token")
        if r.status_code >= 400:
            detail = r.text[:300]
            try:
                detail = (r.json() or {}).get("error", {}).get("message") or detail
            except Exception:  # noqa: BLE001
                pass
            raise TranscriptNotFoundError(f"Apify HTTP {r.status_code}: {detail}")
        items = r.json()

    if not isinstance(items, list) or not items:
        raise TranscriptNotFoundError(f"Apify returned no dataset items for {video_id}")

    item = items[0]
    if item.get("error") or item.get("error_code"):
        code = item.get("error_code") or "ERROR"
        msg = item.get("error") or code
        raise TranscriptNotFoundError(f"Apify: {code} — {msg}")

    segments = _segments_from_apify_transcript_json(item.get("transcript_json"))
    if not segments:
        raise TranscriptNotFoundError(f"Apify returned empty transcript for {video_id}")

    resolved = (item.get("language") or lang_codes[0] or "en").split("-")[0].lower()
    logger.info(
        "YouTube transcript via Apify | video=%s lang=%s lines=%d",
        video_id,
        resolved,
        len(segments),
    )
    return segments, resolved


def _try_cloud_transcript_providers(
    video_id: str,
    langs: list[str],
) -> tuple[list[dict[str, Any]], str] | None:
    """Supadata then Apify. Returns None when no providers are configured."""
    configured = False
    last_error: TranscriptNotFoundError | None = None

    if _supadata_api_key():
        configured = True
        try:
            return _fetch_transcript_via_supadata(video_id, langs)
        except TranscriptNotFoundError as exc:
            last_error = exc
            logger.warning("Supadata caption fetch failed | video=%s | %s", video_id, exc)

    if _apify_api_token():
        configured = True
        try:
            return _fetch_transcript_via_apify(video_id, langs)
        except TranscriptNotFoundError as exc:
            last_error = exc
            logger.warning("Apify caption fetch failed | video=%s | %s", video_id, exc)

    if not configured:
        return None
    return None


def fetch_caption_segments(
    video_id: str,
    preferred_langs: list[str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Fetch caption segments — Supadata/Apify first, then direct YouTube."""
    langs = _expand_lang_prefs(preferred_langs or ["en"])

    cloud = _try_cloud_transcript_providers(video_id, langs)
    if cloud is not None:
        return cloud

    player = _resolve_player_response(video_id)
    tracks = _list_preferred_caption_tracks(_caption_tracks_from_player(player), langs)
    if not tracks:
        raise TranscriptNotFoundError(f"No caption tracks for {video_id}")

    kwargs = _httpx_yt_client_kwargs()
    last_error: Exception | None = None
    with httpx.Client(timeout=25.0, **kwargs) as client:
        for track in tracks:
            caption_url, lang = _caption_url_from_track(track)
            try:
                r = client.get(caption_url)
                r.raise_for_status()
                segments = parse_timedtext_content(r.text)
                if segments:
                    return segments, lang
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "Caption download failed | video=%s lang=%s | %s",
                    video_id,
                    track.get("languageCode"),
                    exc,
                )

    if last_error:
        raise TranscriptNotFoundError(
            f"Caption file empty for {video_id}: {last_error}"
        ) from last_error
    raise TranscriptNotFoundError(f"Caption file empty for {video_id}")


def fetch_caption_from_url(caption_url: str) -> list[dict[str, Any]]:
    """Fetch+parse a signed YouTube timedtext URL (server-side; works on Oracle when URL is signed)."""
    parsed = caption_url.strip()
    if not parsed.startswith("https://www.youtube.com/") and "google.com/timedtext" not in parsed:
        raise TranscriptNotFoundError("Invalid caption URL")
    kwargs = _httpx_yt_client_kwargs()
    with httpx.Client(timeout=25.0, **kwargs) as client:
        r = client.get(parsed)
        r.raise_for_status()
        raw = r.text
    segments = parse_timedtext_content(raw)
    if not segments:
        raise TranscriptNotFoundError("Caption file empty")
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

def _youtube_proxy_config() -> Any | None:
    """Build youtube-transcript-api ProxyConfig from settings (optional)."""
    from app.core.config import settings

    if settings.YOUTUBE_WEBSHARE_USERNAME and settings.YOUTUBE_WEBSHARE_PASSWORD:
        from youtube_transcript_api.proxies import WebshareProxyConfig
        return WebshareProxyConfig(
            proxy_username=settings.YOUTUBE_WEBSHARE_USERNAME.strip(),
            proxy_password=settings.YOUTUBE_WEBSHARE_PASSWORD.strip(),
        )

    proxy_url = (settings.YOUTUBE_PROXY_URL or "").strip()
    if proxy_url:
        from youtube_transcript_api.proxies import GenericProxyConfig
        return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)

    return None


def _youtube_proxy_url() -> str | None:
    """Proxy URL for yt-dlp — generic URL or Webshare rotating proxy."""
    from urllib.parse import quote

    from app.core.config import settings

    proxy_url = (settings.YOUTUBE_PROXY_URL or "").strip()
    if proxy_url:
        return proxy_url

    user = (settings.YOUTUBE_WEBSHARE_USERNAME or "").strip()
    password = (settings.YOUTUBE_WEBSHARE_PASSWORD or "").strip()
    if user and password:
        return f"http://{quote(user, safe='')}:{quote(password, safe='')}@p.webshare.io:80"
    return None


def _build_transcript_api():
    from youtube_transcript_api import YouTubeTranscriptApi

    proxy_config = _youtube_proxy_config()
    if proxy_config is not None:
        return YouTubeTranscriptApi(proxy_config=proxy_config)
    return YouTubeTranscriptApi()


def _transcript_snippet_fields(item: Any) -> tuple[str, float, float]:
    """Support dict (legacy) and FetchedTranscriptSnippet (youtube-transcript-api >= 1.x)."""
    if isinstance(item, dict):
        text = (item.get("text") or "").strip()
        start = float(item.get("start", 0))
        duration = max(0.1, float(item.get("duration", 0.1)))
    else:
        text = (getattr(item, "text", None) or "").strip()
        start = float(getattr(item, "start", 0))
        duration = max(0.1, float(getattr(item, "duration", 0.1)))
    return text, start, duration


def _fetch_transcript_via_api(
    video_id: str,
    langs: list[str],
) -> tuple[list[dict[str, Any]], str]:
    """Fallback: youtube-transcript-api (no audio download, lighter than Whisper)."""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        IpBlocked,
        NoTranscriptFound,
        RequestBlocked,
        TranscriptsDisabled,
        VideoUnavailable,
    )

    api = _build_transcript_api()
    try:
        listing = api.list(video_id)
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound, RequestBlocked, IpBlocked) as e:
        raise TranscriptNotFoundError(str(e)) from e
    except Exception as e:
        if _is_bot_check_error(str(e)):
            raise TranscriptNotFoundError(str(e)) from e
        raise TranscriptNotFoundError(f"transcript-api list failed: {e}") from e

    transcript = None
    lang_code = "en"
    for lang in langs:
        try:
            transcript = listing.find_transcript([lang])
            lang_code = lang.split("-")[0].lower()
            break
        except Exception:
            continue
    if transcript is None:
        try:
            transcript = listing.find_generated_transcript(langs)
            lang_code = "en"
        except Exception as e:
            raise TranscriptNotFoundError(f"No captions via transcript-api: {e}") from e

    items = transcript.fetch()
    segments: list[dict[str, Any]] = []
    for item in items:
        text, start, duration = _transcript_snippet_fields(item)
        if not text:
            continue
        segments.append({
            "text": text,
            "start": start,
            "duration": duration,
        })
    if not segments:
        raise TranscriptNotFoundError("transcript-api returned empty segments")
    logger.info("YouTube transcript via transcript-api | video=%s lang=%s lines=%d", video_id, lang_code, len(segments))
    return segments, lang_code


def _expand_lang_prefs(langs: list[str] | None) -> list[str]:
    base = langs or ["en", "en-US", "en-GB"]
    seen: list[str] = []
    for lang in list(base) + ["en", "en-US", "en-GB"]:
        if lang and lang not in seen:
            seen.append(lang)
    return seen


def _pick_subtitle_from_info(
    subtitles: dict,
    auto_captions: dict,
    langs: list[str],
    video_id: str,
) -> tuple[str | None, str, bool]:
    """Pick subtitle URL from yt-dlp info dict; match en/en-US/any en*."""
    sub_url: str | None = None
    sub_lang = "en"
    sub_is_json3 = True

    def _pick_url(sub_dict: dict, lang_key: str) -> tuple[str | None, bool]:
        entries: list[dict] = sub_dict.get(lang_key) or []
        for e in entries:
            if e.get("ext") == "json3" or "fmt=json3" in (e.get("url") or ""):
                return e.get("url"), True
        for e in entries:
            if e.get("ext") == "vtt" or "vtt" in (e.get("url") or ""):
                return e.get("url"), False
        if entries:
            return entries[0].get("url"), False
        return None, False

    def _lang_keys(sub_dict: dict) -> list[str]:
        keys: list[str] = []
        for lang in langs:
            if lang in sub_dict:
                keys.append(lang)
        for key in sorted(sub_dict.keys()):
            if key not in keys and any(key == l or key.startswith(l.split("-")[0]) for l in langs):
                keys.append(key)
        for key in sorted(sub_dict.keys()):
            if key not in keys and key.startswith("en"):
                keys.append(key)
        return keys

    for lang_key in _lang_keys(subtitles):
        u, is_json3 = _pick_url(subtitles, lang_key)
        if u:
            logger.info("Manual subtitle found | video=%s lang=%s", video_id, lang_key)
            return u, lang_key.split("-")[0].lower(), is_json3

    for lang_key in _lang_keys(auto_captions):
        u, is_json3 = _pick_url(auto_captions, lang_key)
        if u:
            logger.info("Auto-caption found | video=%s lang=%s", video_id, lang_key)
            return u, lang_key.split("-")[0].lower(), is_json3

    logger.warning(
        "yt-dlp info has no matching subs | video=%s manual=%s auto=%s",
        video_id,
        list(subtitles.keys())[:15],
        list(auto_captions.keys())[:15],
    )
    return None, sub_lang, sub_is_json3


def _ytdlp_write_subtitle_files(
    url: str,
    video_id: str,
    langs: list[str],
) -> tuple[list[dict[str, Any]], str]:
    """Download subtitle files to disk via yt-dlp (works when info dict lacks sub URLs)."""
    import glob
    import yt_dlp  # noqa: PLC0415

    with tempfile.TemporaryDirectory(prefix="yt_sub_") as tmp:
        outtmpl = os.path.join(tmp, video_id)
        base = _ydl_opts(quiet=True)
        base.update({
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "json3/vtt/best",
            "outtmpl": outtmpl,
            "noplaylist": True,
        })

        last_error: Exception | None = None
        attempts = [_with_player_clients(base, c) for c in _player_client_fallbacks()]
        attempts.append(_without_impersonate(base))
        for opts in attempts:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                last_error = None
                break
            except Exception as e:
                last_error = e
                logger.warning("yt-dlp subtitle write failed | %s", e)

        if last_error:
            raise TranscriptNotFoundError(f"yt-dlp subtitle write failed: {last_error}") from last_error

        files = sorted(glob.glob(os.path.join(tmp, f"{video_id}*")))
        if not files:
            raise TranscriptNotFoundError(f"yt-dlp wrote no subtitle files for {video_id}")

        def _score(path: str) -> tuple[int, int]:
            name = os.path.basename(path).lower()
            lang_rank = 0
            for i, lang in enumerate(langs):
                if f".{lang.lower()}." in name or name.endswith(f".{lang.lower()}.json3"):
                    lang_rank = len(langs) - i
                    break
            fmt_rank = 2 if name.endswith(".json3") else (1 if name.endswith(".vtt") else 0)
            return lang_rank, fmt_rank

        best = max(files, key=_score)
        raw_content = open(best, encoding="utf-8", errors="replace").read()
        sub_lang = "en"
        for lang in langs:
            if f".{lang}." in best:
                sub_lang = lang.split("-")[0].lower()
                break

        if best.endswith(".json3"):
            segments = _parse_json3(raw_content)
        else:
            segments = _parse_vtt(raw_content)

        if not segments:
            raise TranscriptNotFoundError(f"yt-dlp subtitle file empty | {best}")
        logger.info("yt-dlp subtitle file ok | video=%s file=%s lines=%d", video_id, os.path.basename(best), len(segments))
        return segments, sub_lang


def _fetch_youtube_transcript_ytdlp(
    video_id: str,
    langs: list[str],
) -> tuple[list[dict[str, Any]], str]:
    langs = _expand_lang_prefs(langs)
    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = _ydl_opts()
    opts["subtitleslangs"] = langs

    try:
        info = ytdlp_extract_info(url, opts)
    except Exception as e:
        if isinstance(e, TranscriptNotFoundError):
            raise
        logger.exception("yt-dlp extract_info failed | video=%s | error=%s", video_id, e)
        raise TranscriptNotFoundError(str(e)) from e

    if not info:
        raise TranscriptNotFoundError("yt-dlp returned empty info")

    subtitles: dict = info.get("subtitles") or {}
    auto_captions: dict = info.get("automatic_captions") or {}
    sub_url, sub_lang, sub_is_json3 = _pick_subtitle_from_info(subtitles, auto_captions, langs, video_id)

    if not sub_url:
        return _ytdlp_write_subtitle_files(url, video_id, langs)

    try:
        from curl_cffi import requests as cffi_requests
        resp = cffi_requests.get(sub_url, impersonate="chrome", timeout=15)
        resp.raise_for_status()
        raw_content = resp.text
    except ImportError:
        logger.warning("curl_cffi not available — falling back to urllib for subtitle download")
        try:
            import urllib.request
            with urllib.request.urlopen(sub_url, timeout=15) as resp:
                raw_content = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            return _ytdlp_write_subtitle_files(url, video_id, langs)
    except Exception as e:
        logger.warning("subtitle URL fetch failed, trying yt-dlp write | %s", e)
        return _ytdlp_write_subtitle_files(url, video_id, langs)

    if sub_is_json3:
        segments = _parse_json3(raw_content)
    else:
        segments = _parse_vtt(raw_content)

    if not segments:
        return _ytdlp_write_subtitle_files(url, video_id, langs)

    logger.info(
        "YouTube transcript fetched via yt-dlp | video=%s lang=%s lines=%d",
        video_id,
        sub_lang,
        len(segments),
    )
    return segments, sub_lang


def fetch_youtube_transcript(
    video_id: str,
    preferred_langs: list[str] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Fetch YouTube captions.

    Production / cookie mode: yt-dlp + cookies first (cloud IPs block transcript-api).
    Local dev: transcript-api first (lighter).
    """
    langs = _expand_lang_prefs(preferred_langs)
    has_proxy = _youtube_proxy_config() is not None
    use_ytdlp_first = not has_proxy and (
        os.environ.get("ENVIRONMENT") == "production" or bool(_get_yt_cookies_path())
    )
    methods: list[Any] = []
    if _supadata_api_key():
        methods.append(_fetch_transcript_via_supadata)
    if _apify_api_token():
        methods.append(_fetch_transcript_via_apify)
    if has_proxy:
        methods.extend([_fetch_transcript_via_api, _fetch_youtube_transcript_ytdlp])
    elif use_ytdlp_first:
        methods.extend([_fetch_youtube_transcript_ytdlp, _fetch_transcript_via_api])
    else:
        methods.extend([_fetch_transcript_via_api, _fetch_youtube_transcript_ytdlp])

    errors: list[TranscriptNotFoundError] = []
    for method in methods:
        try:
            return method(video_id, langs)
        except TranscriptNotFoundError as e:
            errors.append(e)
            logger.warning("%s failed | video=%s | %s", method.__name__, video_id, e)

    for err in errors:
        if _is_bot_check_error(str(err)):
            raise TranscriptNotFoundError(
                "YouTube chặn IP server Oracle (cookie không đủ). "
                "Thêm proxy residential — Webshare: YOUTUBE_WEBSHARE_USERNAME/PASSWORD trong .env."
            ) from err
    if errors:
        raise errors[-1]
    raise TranscriptNotFoundError(f"No captions for video {video_id}")
