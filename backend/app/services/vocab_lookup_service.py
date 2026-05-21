"""
Vocabulary lookup via OpenRouter (streaming NDJSON) with dictionary fallback.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_FAST_MODEL = (settings.OPENROUTER_FAST_MODEL or "google/gemini-2.0-flash-001").strip()
_FALLBACK_MODEL = "google/gemini-2.0-flash-001"
_TIMEOUT = 25.0

_SYSTEM = """You are a concise English–Vietnamese dictionary for IELTS learners.
Output ONLY newline-delimited JSON (NDJSON), one object per line, no markdown.
Emit lines in this order (skip only if truly unknown):
{"field":"phonetic","value":"IPA without slashes"}
{"field":"word_type","value":"noun"}
{"field":"meaning_en","value":"Clear English definition(s), semicolon-separated if multiple"}
{"field":"meaning_vi","value":"Natural Vietnamese translation"}
{"field":"example","value":"One short example sentence in English"}
{"field":"example_vi","value":"Vietnamese translation of the example"}
{"field":"all_meanings","value":[{"type":"noun","defs":["def1"],"example":"..."}]}
The all_meanings value must be a JSON array. Keep responses accurate and concise."""


def _openrouter_key() -> str:
    return (settings.OPENROUTER_API_KEY or "").strip()


def _model_candidates() -> list[str]:
    out: list[str] = []
    for m in (_FAST_MODEL, _FALLBACK_MODEL, "anthropic/claude-3-haiku"):
        if m and m not in out:
            out.append(m)
    return out


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_openrouter_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "LinguaIELTS Vocab Lookup",
    }


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


def _apply_field(result: dict[str, Any], field: str, value: Any) -> None:
    if field == "all_meanings":
        if isinstance(value, list):
            result["allMeanings"] = value
        elif isinstance(value, str):
            try:
                result["allMeanings"] = json.loads(value)
            except json.JSONDecodeError:
                pass
        return
    key_map = {
        "phonetic": "phonetic",
        "word_type": "word_type",
        "meaning_en": "meaning_en",
        "meaning_vi": "meaning_vi",
        "example": "example",
        "example_vi": "example_vi",
    }
    if field in key_map and value is not None:
        result[key_map[field]] = str(value).strip() if not isinstance(value, (list, dict)) else value


def _parse_ndjson_line(line: str) -> tuple[str, Any] | None:
    line = line.strip()
    if not line or line.startswith("```"):
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    field = obj.get("field")
    if not field:
        return None
    return field, obj.get("value")


async def _fallback_lookup(word: str) -> dict[str, Any]:
    """Free Dictionary + MyMemory when OpenRouter unavailable."""
    result = _empty_result(word)
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            r = await client.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            )
            if r.is_success:
                entry = r.json()[0]
                result["word"] = entry.get("word") or word
                result["phonetic"] = _extract_phonetic(entry)
                result["word_type"] = (entry.get("meanings") or [{}])[0].get("partOfSpeech", "")
                result["meaning_en"] = _build_en_gloss(entry)
                result["example"] = _first_example(entry)
                result["allMeanings"] = _build_all_meanings(entry)
                for p in entry.get("phonetics") or []:
                    if p.get("audio"):
                        result["audio"] = p["audio"]
                        break
        except Exception as exc:
            logger.debug("Dictionary API fallback failed: %s", exc)

        try:
            r2 = await client.get(
                "https://api.mymemory.translated.net/get",
                params={"q": word, "langpair": "en|vi", "de": "a@b.com"},
            )
            if r2.is_success:
                tr = r2.json().get("responseData", {}).get("translatedText", "")
                if tr and tr.lower() != word.lower() and "MYMEMORY WARNING" not in tr.upper():
                    result["meaning_vi"] = tr
        except Exception as exc:
            logger.debug("MyMemory fallback failed: %s", exc)

        if result["example"]:
            try:
                r3 = await client.get(
                    "https://api.mymemory.translated.net/get",
                    params={
                        "q": result["example"][:200],
                        "langpair": "en|vi",
                        "de": "a@b.com",
                    },
                )
                if r3.is_success:
                    tr = r3.json().get("responseData", {}).get("translatedText", "")
                    if tr:
                        result["example_vi"] = tr
            except Exception:
                pass

    return result


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


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_word_lookup(word: str) -> AsyncIterator[str]:
    """Yield SSE events: patch (partial field), done (final), error."""
    clean = re.sub(r"[^a-zA-Z'-]", "", word).lower()
    if not clean:
        yield _sse({"error": "invalid_word"})
        return

    result = _empty_result(clean)

    if not _openrouter_key():
        final = await _fallback_lookup(clean)
        yield _sse({"done": True, "result": final})
        return

    line_buf = ""
    content_buf = ""
    last_exc: Exception | None = None

    for model_id in _model_candidates():
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": f'Define the English word "{clean}" for an IELTS student.'},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
            "stream": True,
            "provider": {"allow_fallbacks": True},
        }
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    _OPENROUTER_URL,
                    json=payload,
                    headers=_headers(),
                ) as resp:
                    if resp.status_code == 404 and model_id != _FALLBACK_MODEL:
                        logger.warning("OpenRouter model %s unavailable, next fallback", model_id)
                        continue
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        delta = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                        if not delta:
                            continue
                        content_buf += delta
                        line_buf += delta
                        while "\n" in line_buf:
                            raw_line, line_buf = line_buf.split("\n", 1)
                            parsed = _parse_ndjson_line(raw_line)
                            if not parsed:
                                continue
                            field, value = parsed
                            _apply_field(result, field, value)
                            patch = {k: v for k, v in result.items() if v}
                            yield _sse({"patch": patch})

            # trailing line without newline
            if line_buf.strip():
                parsed = _parse_ndjson_line(line_buf)
                if parsed:
                    _apply_field(result, parsed[0], parsed[1])
                    yield _sse({"patch": {k: v for k, v in result.items() if v}})

            # parse full buffer as JSON fallback if NDJSON incomplete
            if not result.get("meaning_en") and content_buf.strip():
                repaired = _try_parse_full_json(content_buf)
                if repaired:
                    result.update(repaired)

            if result.get("meaning_en") or result.get("meaning_vi"):
                yield _sse({"done": True, "result": result})
                return

            last_exc = RuntimeError("empty stream result")
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            if exc.response.status_code == 404:
                continue
            break
        except Exception as exc:
            last_exc = exc
            logger.warning("Vocab lookup stream error (%s): %s", model_id, exc)
            continue

    logger.warning("OpenRouter vocab lookup failed, using free APIs: %s", last_exc)
    final = await _fallback_lookup(clean)
    yield _sse({"done": True, "result": final, "fallback": True})


def _try_parse_full_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    out = _empty_result(obj.get("word", ""))
    for k in ("phonetic", "word_type", "meaning_en", "meaning_vi", "example", "example_vi"):
        if obj.get(k):
            out[k] = obj[k]
    if obj.get("all_meanings"):
        out["allMeanings"] = obj["all_meanings"]
    elif obj.get("allMeanings"):
        out["allMeanings"] = obj["allMeanings"]
    return out
