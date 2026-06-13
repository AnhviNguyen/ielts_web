"""
Vocabulary lookup via Free Dictionary API (dictionaryapi.dev) + MyMemory for Vietnamese.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DICTIONARY_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
_MYMEMORY_URL = "https://api.mymemory.translated.net/get"
_TIMEOUT = 10.0


def _empty_result(word: str) -> dict[str, Any]:
    return {
        "word": word,
        "phonetic": "",
        "word_type": "",
        "meaning_en": "",
        "meaning_vi": "",
        "example": "",
        "example_vi": "",
        "audio": "",
        "allMeanings": [],
    }


def _normalize_audio(url: str) -> str:
    if url.startswith("//"):
        return f"https:{url}"
    return url


def _extract_phonetic(entry: dict) -> str:
    if entry.get("phonetic"):
        return str(entry["phonetic"]).strip("/ ")
    for p in entry.get("phonetics") or []:
        if p.get("text"):
            return str(p["text"]).strip("/ ")
    return ""


def _build_en_gloss(entry: dict) -> str:
    parts: list[str] = []
    for m in (entry.get("meanings") or [])[:3]:
        pos = m.get("partOfSpeech", "")
        prefix = f"({pos}) " if pos else ""
        for d in (m.get("definitions") or [])[:2]:
            if d.get("definition"):
                parts.append(f"{prefix}{d['definition']}")
    return "; ".join(parts)


def _first_example(entry: dict) -> str:
    for m in entry.get("meanings") or []:
        for d in m.get("definitions") or []:
            if d.get("example"):
                return d["example"]
    return ""


def _build_all_meanings(entry: dict) -> list[dict]:
    out = []
    for m in (entry.get("meanings") or [])[:4]:
        defs = [d["definition"] for d in (m.get("definitions") or [])[:3] if d.get("definition")]
        if defs:
            ex = next((d.get("example") for d in m.get("definitions") or [] if d.get("example")), "")
            out.append({"type": m.get("partOfSpeech", ""), "defs": defs, "example": ex or ""})
    return out


async def _translate_en_vi(client: httpx.AsyncClient, text: str) -> str:
    if not text.strip():
        return ""
    try:
        r = await client.get(
            _MYMEMORY_URL,
            params={"q": text[:200], "langpair": "en|vi", "de": "a@b.com"},
        )
        if not r.is_success:
            return ""
        tr = r.json().get("responseData", {}).get("translatedText", "")
        if not tr or tr.lower() == text.lower() or "MYMEMORY WARNING" in tr.upper():
            return ""
        return tr
    except Exception as exc:
        logger.debug("MyMemory translation failed: %s", exc)
        return ""


async def lookup_word(word: str) -> dict[str, Any]:
    """Look up an English word via dictionaryapi.dev (+ Vietnamese via MyMemory)."""
    clean = re.sub(r"[^a-zA-Z'-]", "", word).lower()
    if not clean:
        return _empty_result(word)

    result = _empty_result(clean)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            r = await client.get(_DICTIONARY_URL.format(word=clean))
            if r.status_code == 404:
                result["meaning_vi"] = await _translate_en_vi(client, clean)
                return result
            r.raise_for_status()
            entry = r.json()[0]
            result["word"] = entry.get("word") or clean
            result["phonetic"] = _extract_phonetic(entry)
            result["word_type"] = (entry.get("meanings") or [{}])[0].get("partOfSpeech", "")
            result["meaning_en"] = _build_en_gloss(entry)
            result["example"] = _first_example(entry)
            result["allMeanings"] = _build_all_meanings(entry)
            for p in entry.get("phonetics") or []:
                if p.get("audio"):
                    result["audio"] = _normalize_audio(p["audio"])
                    break
        except httpx.HTTPStatusError as exc:
            logger.warning("Dictionary API HTTP error for %r: %s", clean, exc)
        except Exception as exc:
            logger.warning("Dictionary API failed for %r: %s", clean, exc)

        result["meaning_vi"] = await _translate_en_vi(client, clean)
        if result["example"]:
            result["example_vi"] = await _translate_en_vi(client, result["example"])

    return result


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_word_lookup(word: str) -> AsyncIterator[str]:
    """Yield a single SSE done event (backward-compatible with streaming clients)."""
    clean = re.sub(r"[^a-zA-Z'-]", "", word).lower()
    if not clean:
        yield _sse({"error": "invalid_word"})
        return

    result = await lookup_word(clean)
    yield _sse({"done": True, "result": result})
