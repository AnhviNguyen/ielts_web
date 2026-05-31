"""
Segment normalization for shadowing transcripts.

Pipeline:
  1. raw fragments → merge into blocks (flush on sentence punctuation / time-gap / length)
  2. each block → split on .!? sentence boundaries
  3. any remaining long phrase (no .!?) → smart_split by grammar priority
"""

from __future__ import annotations

import re
from typing import Any

_YT_ID_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"^([a-zA-Z0-9_-]{11})$"),
]

# Split after .!? when followed by whitespace + uppercase (or quote / bracket)
_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-Z\'"\u201C\u2018\[])')

# Maximum words per output segment; smart_split enforces this
_MAX_WORDS = 18

# Buffer limits for the merge phase.
# ~120 chars ≈ 20-25 words (average English word ~5 chars + space).
# 4 seconds ≈ one natural breath / thought unit in spoken English.
_MAX_BUFFER_CHARS = 120
_MAX_BUFFER_SECONDS = 4.0

# Words that signal a good split point after a comma
_FANBOYS = {"and", "but", "so", "yet", "for", "nor", "or"}
_TRANSITIONS = {
    "however", "therefore", "moreover", "furthermore", "meanwhile",
    "nonetheless", "otherwise", "besides", "consequently", "thus",
    "hence", "still", "instead", "indeed", "similarly",
}
_COMMA_SPLIT_WORDS = _FANBOYS | _TRANSITIONS

# Relative/subordinate clause markers
_RELATIVE_RE = re.compile(
    r'\b(which|who|whom|whose|where|when|that|although|because|since|unless|while|whereas)\b',
    re.IGNORECASE,
)

# Comma followed by a split-word
_COMMA_KEYWORD_RE = re.compile(
    r',\s*(' + '|'.join(re.escape(w) for w in sorted(_COMMA_SPLIT_WORDS)) + r')\b',
    re.IGNORECASE,
)


# ── Public helpers ────────────────────────────────────────────────────────────

def extract_youtube_video_id(url: str) -> str | None:
    url = (url or "").strip()
    for pat in _YT_ID_PATTERNS:
        m = pat.search(url)
        if m:
            return m.group(1)
    return None


# ── Internal: smart phrase splitter ──────────────────────────────────────────

def _smart_split(text: str, max_words: int = _MAX_WORDS) -> list[str]:
    """
    Split a long phrase (no .!? ending) into natural shorter chunks.

    Priority:
      1. Semicolons  →  ";  …"
      2. Comma + FANBOYS (and/but/so/yet/for/nor/or)
      3. Comma + transition words (however/therefore/…)
      4. Relative-clause marker (which/who/where/that/…)
      5. Any comma nearest to the midpoint
      6. Hard cut at max_words
    """
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]

    # 1. Semicolons
    if ";" in text:
        parts = [p.strip() for p in text.split(";") if p.strip()]
        if len(parts) > 1:
            out: list[str] = []
            for p in parts:
                out.extend(_smart_split(p, max_words))
            return out

    # 2 & 3. Comma + FANBOYS/transitions
    m = _COMMA_KEYWORD_RE.search(text)
    if m:
        left = text[: m.start()].strip()
        right = text[m.start() + 1 :].strip()  # drop the comma itself
        if left and right:
            return _smart_split(left, max_words) + _smart_split(right, max_words)

    # 4. Relative-clause marker (skip first word to avoid splitting too early)
    m = _RELATIVE_RE.search(text, len(words[0]) + 1)
    if m:
        left = text[: m.start()].strip()
        right = text[m.start() :].strip()
        if left and right and len(left.split()) >= 3:
            return _smart_split(left, max_words) + _smart_split(right, max_words)

    # 5. Nearest comma to midpoint
    commas = [cm.start() for cm in re.finditer(r",", text)]
    if commas:
        mid = len(text) // 2
        best = min(commas, key=lambda c: abs(c - mid))
        left = text[:best].strip()
        right = text[best + 1 :].strip()
        if left and right:
            return _smart_split(left, max_words) + _smart_split(right, max_words)

    # 6. Hard cut at max_words
    left = " ".join(words[:max_words])
    right = " ".join(words[max_words:])
    return [left] + _smart_split(right, max_words)


# ── Internal: timestamp distribution ─────────────────────────────────────────

def _round_ts(value: float) -> float:
    return round(float(value), 1)


def _distribute_timestamps(
    parts: list[str],
    start: float,
    duration: float,
) -> list[dict[str, Any]]:
    """Assign proportional timestamps to a list of text parts."""
    total_chars = sum(len(p) for p in parts) or 1
    result: list[dict[str, Any]] = []
    cur = start
    for i, part in enumerate(parts):
        frac = len(part) / total_chars
        dur = duration * frac
        is_last = i == len(parts) - 1
        result.append({
            "text": part,
            "start": _round_ts(cur),
            "duration": _round_ts(
                max(0.1, start + duration - cur) if is_last else max(0.1, dur)
            ),
        })
        cur += dur
    return result


# ── Internal: sentence-level splitting ───────────────────────────────────────

def _split_block(text: str, start: float, duration: float) -> list[dict[str, Any]]:
    """
    Split a text block into individual segments:
      - First split on .!? sentence boundaries.
      - Then apply smart_split to any sentence that is still too long.
    """
    # Step 1: sentence-boundary split
    sentences = _SENTENCE_BOUNDARY.split(text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return []

    # Step 2: smart-split long sentences
    final_parts: list[str] = []
    for sent in sentences:
        if len(sent.split()) > _MAX_WORDS:
            final_parts.extend(_smart_split(sent))
        else:
            final_parts.append(sent)

    if not final_parts:
        return []

    if len(final_parts) == 1:
        return [{"text": final_parts[0], "start": _round_ts(start), "duration": _round_ts(duration)}]

    return _distribute_timestamps(final_parts, start, duration)


# ── Internal: raw fragment merger ─────────────────────────────────────────────

def _merge_raw_to_sentences(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Merge caption fragments into natural blocks, then split into segments.

    Flush triggers (in order of check):
      1. Time gap ≥ _MAX_BUFFER_SECONDS since buffer start.
      2. Fragment ends with .!? (sentence complete).
      3. Buffer length ≥ _MAX_BUFFER_CHARS (flush at word boundary).
    """
    if not raw:
        return []

    out: list[dict[str, Any]] = []
    buf_text: list[str] = []
    buf_start: float | None = None
    buf_end: float = 0.0

    def flush() -> None:
        nonlocal buf_text, buf_start, buf_end
        if not buf_text or buf_start is None:
            return
        text = re.sub(r"\s+", " ", " ".join(buf_text)).strip()
        if text:
            duration = max(0.1, buf_end - buf_start)
            out.extend(_split_block(text, buf_start, duration))
        buf_text.clear()
        buf_start = None
        buf_end = 0.0

    for entry in raw:
        t = (entry.get("text") or "").strip()
        if not t:
            continue
        start = float(entry.get("start", 0))
        dur = float(entry.get("duration", 2.0))
        end = start + dur

        # Time-gap flush
        if buf_start is not None and (start - buf_start) >= _MAX_BUFFER_SECONDS:
            flush()

        if buf_start is None:
            buf_start = start
        buf_text.append(t)
        buf_end = end

        # Punctuation flush
        if re.search(r"[.!?]\s*$", t):
            flush()
            continue

        # Length flush
        if len(" ".join(buf_text)) >= _MAX_BUFFER_CHARS:
            flush()

    flush()
    return out


# ── Public API ────────────────────────────────────────────────────────────────

def normalize_segments(
    raw_entries: list[dict[str, Any]],
    language: str = "en",
) -> list[dict[str, Any]]:
    """
    Convert raw transcript entries to numbered sentence-level segments.

    Each segment is a single natural sentence or short phrase (≤ ~20 words).
    """
    merged = _merge_raw_to_sentences(raw_entries)
    segments: list[dict[str, Any]] = []
    for idx, seg in enumerate(merged, start=1):
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
