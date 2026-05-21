"""
Generate cloze reading passages for vocabulary practice (OpenRouter + fallback).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_OPENROUTER_KEY = (settings.OPENROUTER_API_KEY or "").strip()
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_AI_MODEL = (
    getattr(settings, "OPENROUTER_FAST_MODEL", None)
    or "google/gemini-2.0-flash-001"
)
_AI_TIMEOUT = 45.0

_SYSTEM = """You create IELTS-style English reading cloze exercises for vocabulary learners.
Return ONLY valid JSON (no markdown fences) with this exact shape:
{
  "paragraphs": [
    {
      "parts": [
        {"type": "text", "content": "English sentence fragment "},
        {"type": "gap", "id": "g0", "hint_vi": "(nghĩa tiếng Việt ngắn)"},
        {"type": "text", "content": " rest of sentence."}
      ]
    }
  ],
  "answers": {"g0": "exact English word"}
}
Rules:
- Write 1-2 coherent paragraphs (business/academic tone).
- Use EVERY target word exactly once as a gap; id g0, g1, ... in order.
- hint_vi is Vietnamese meaning in parentheses like (sự thỏa thuận).
- answers must match the English word form used in context (lowercase unless proper noun).
- Natural grammar; gaps replace only the target word."""


def _parse_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def _call_openrouter(words_payload: list[dict]) -> dict[str, Any]:
    user = json.dumps({"target_words": words_payload}, ensure_ascii=False)
    headers = {
        "Authorization": f"Bearer {_OPENROUTER_KEY}",
        "HTTP-Referer": "http://localhost:5173",
        "Content-Type": "application/json",
        "X-Title": "LinguaIELTS Vocab Reading",
    }
    payload = {
        "model": _AI_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0.35,
        "max_tokens": 1200,
    }
    async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
        resp = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return _parse_json(content)


def _fallback_passage(words: list[dict]) -> dict[str, Any]:
    """Template passage when AI is unavailable."""
    parts: list[dict] = []
    answers: dict[str, str] = {}
    for i, w in enumerate(words):
        gid = f"g{i}"
        hint = w.get("meaning_vi") or w.get("meaning_en") or ""
        if hint and not hint.startswith("("):
            hint = f"({hint})"
        if i == 0:
            parts.append({"type": "text", "content": "Many teams rely on clear communication. For instance, they may need a "})
        else:
            parts.append({"type": "text", "content": " Later, the same group might discuss a "})
        parts.append({"type": "gap", "id": gid, "hint_vi": hint or "(nghĩa)"})
        parts.append({"type": "text", "content": " during the project."})
        answers[gid] = w["word"].strip()
    return {"paragraphs": [{"parts": parts}], "answers": answers}


def _normalize_passage(raw: dict[str, Any], words: list[dict]) -> dict[str, Any]:
    paragraphs = raw.get("paragraphs") or []
    answers = dict(raw.get("answers") or {})
    # Ensure each word has an answer entry
    gap_ids = []
    for para in paragraphs:
        for p in para.get("parts") or []:
            if p.get("type") == "gap" and p.get("id"):
                gap_ids.append(p["id"])
    for i, w in enumerate(words):
        gid = f"g{i}"
        if gid not in answers and i < len(gap_ids):
            answers[gap_ids[i]] = w["word"].strip()
        elif gid not in answers:
            answers[gid] = w["word"].strip()
    return {
        "paragraphs": paragraphs,
        "answers": answers,
        "source": raw.get("source", "ai"),
    }


async def generate_reading_passage(words: list[dict]) -> dict[str, Any]:
    """
    words: [{ word, meaning_vi, meaning_en?, word_id }]
    """
    if not words:
        return {"paragraphs": [], "answers": {}, "source": "empty"}

    payload = [
        {
            "word": w["word"],
            "meaning_vi": w.get("meaning_vi") or "",
            "word_id": w.get("word_id"),
        }
        for w in words
    ]

    if _OPENROUTER_KEY:
        try:
            raw = await _call_openrouter(payload)
            out = _normalize_passage(raw, words)
            out["source"] = "ai"
            return out
        except Exception as exc:
            logger.warning("Vocab reading AI failed, using fallback: %s", exc)

    out = _fallback_passage(words)
    out["source"] = "fallback"
    return out
