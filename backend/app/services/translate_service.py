"""
Lightweight translation via Google Translate public endpoint (no API key).
Handles long texts by splitting into safe-size chunks.
"""

from __future__ import annotations

import logging
import urllib.parse

import httpx

logger = logging.getLogger(__name__)

# Google's gtx endpoint rejects requests whose URL is too long.
# Keeping each chunk ≤ 900 characters is well within the safe limit.
_MAX_CHUNK_CHARS = 900


async def translate_text(
    text: str,
    from_lang: str = "en",
    to_lang: str = "vi",
) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    chunks = _split_into_chunks(text, _MAX_CHUNK_CHARS)
    translated_parts: list[str] = []
    for chunk in chunks:
        part = await _translate_chunk(chunk, from_lang, to_lang)
        translated_parts.append(part)

    return " ".join(translated_parts).strip()


async def _translate_chunk(text: str, from_lang: str, to_lang: str) -> str:
    """Send a single safe-size chunk to the Google Translate endpoint."""
    params = {
        "client": "gtx",
        "sl": from_lang or "auto",
        "tl": to_lang or "vi",
        "dt": "t",
        "q": text,
    }
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(params)

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    if not data or not isinstance(data[0], list):
        return ""

    parts = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
    result = "".join(parts).strip()
    logger.debug("Translated %d chars %s→%s", len(text), from_lang, to_lang)
    return result


def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    """
    Split text into chunks of at most `max_chars` characters.
    Tries to break at sentence boundaries (. ! ?) first, then at spaces.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    remaining = text

    while len(remaining) > max_chars:
        window = remaining[:max_chars]

        # Prefer breaking at last sentence-ending punctuation in the window
        cut = _last_sentence_break(window)

        # Fall back to last space so we don't cut mid-word
        if cut == -1:
            cut = window.rfind(" ")

        # Hard cut if no whitespace found
        if cut == -1:
            cut = max_chars

        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].lstrip()

    if remaining:
        chunks.append(remaining.strip())

    return [c for c in chunks if c]


def _last_sentence_break(text: str) -> int:
    """Return the index just after the last sentence-ending char (. ! ?)."""
    for i in range(len(text) - 1, -1, -1):
        if text[i] in ".!?":
            return i + 1
    return -1
