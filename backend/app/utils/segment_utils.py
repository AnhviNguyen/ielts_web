"""
Segment normalization for shadowing transcripts.
Sentence-level chunks, max 10s duration, timestamps to 1 decimal.
"""

from __future__ import annotations

import re
from typing import Any

MAX_SEGMENT_DURATION = 10.0
_YT_ID_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"^([a-zA-Z0-9_-]{11})$"),
]


def extract_youtube_video_id(url: str) -> str | None:
    url = (url or "").strip()
    for pat in _YT_ID_PATTERNS:
        m = pat.search(url)
        if m:
            return m.group(1)
    return None


def _round_ts(value: float) -> float:
    return round(float(value), 1)


def _split_long_segment(text: str, start: float, duration: float) -> list[dict[str, Any]]:
    """Split a segment longer than MAX_SEGMENT_DURATION into smaller chunks."""
    if duration <= MAX_SEGMENT_DURATION:
        return [{"text": text.strip(), "start": _round_ts(start), "duration": _round_ts(duration)}]

    words = text.split()
    if len(words) <= 1:
        mid = duration / 2
        return [
            {"text": text.strip(), "start": _round_ts(start), "duration": _round_ts(mid)},
            {"text": text.strip(), "start": _round_ts(start + mid), "duration": _round_ts(duration - mid)},
        ]

    parts: list[dict[str, Any]] = []
    n = max(2, int(duration / MAX_SEGMENT_DURATION) + 1)
    chunk_words = max(1, len(words) // n)
    part_dur = duration / n
    for i in range(n):
        w_start = i * chunk_words
        w_end = len(words) if i == n - 1 else (i + 1) * chunk_words
        chunk_text = " ".join(words[w_start:w_end]).strip()
        if not chunk_text:
            continue
        parts.append({
            "text": chunk_text,
            "start": _round_ts(start + i * part_dur),
            "duration": _round_ts(part_dur if i < n - 1 else max(0.1, duration - i * part_dur)),
        })
    return parts


def _merge_raw_to_sentences(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge caption fragments into sentence-level segments using end punctuation."""
    if not raw:
        return []

    sentences: list[dict[str, Any]] = []
    buf_text: list[str] = []
    buf_start: float | None = None
    buf_end: float = 0.0

    def flush():
        nonlocal buf_text, buf_start, buf_end
        if not buf_text or buf_start is None:
            return
        text = " ".join(buf_text).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            duration = max(0.1, buf_end - buf_start)
            sentences.append({
                "text": text,
                "start": _round_ts(buf_start),
                "duration": _round_ts(duration),
            })
        buf_text = []
        buf_start = None
        buf_end = 0.0

    for entry in raw:
        t = (entry.get("text") or "").strip()
        if not t:
            continue
        start = float(entry.get("start", 0))
        dur = float(entry.get("duration", 0.1))
        end = start + dur
        if buf_start is None:
            buf_start = start
        buf_text.append(t)
        buf_end = end
        if re.search(r"[.!?]\s*$", t):
            flush()

    flush()
    return sentences


def normalize_segments(
    raw_entries: list[dict[str, Any]],
    language: str = "en",
) -> list[dict[str, Any]]:
    """
    Convert raw transcript entries to numbered sentence-level segments.
    Splits segments longer than 10 seconds.
    """
    merged = _merge_raw_to_sentences(raw_entries)
    flat: list[dict[str, Any]] = []
    for item in merged:
        flat.extend(_split_long_segment(item["text"], item["start"], item["duration"]))

    segments: list[dict[str, Any]] = []
    for idx, seg in enumerate(flat, start=1):
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        segments.append({
            "id": idx,
            "text": text,
            "start": seg["start"],
            "duration": seg["duration"],
            "language": language,
        })
    return segments
