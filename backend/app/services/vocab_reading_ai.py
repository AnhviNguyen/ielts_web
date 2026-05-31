"""
Generate cloze reading passages for vocabulary practice (OpenRouter + fallback).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.openrouter_client import chat_completion_json, has_openrouter_keys

logger = logging.getLogger(__name__)

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
  "answers": {"g0": "exact English word"},
  "comprehension_questions": [
    {
      "id": "cq0",
      "stem": "Question about the passage (not the gaps)?",
      "options": [{"id": "a", "text": "..."}, {"id": "b", "text": "..."}, {"id": "c", "text": "..."}, {"id": "d", "text": "..."}],
      "correct_id": "a"
    }
  ]
}
Rules:
- Write 1-2 coherent paragraphs (business/academic tone).
- Use EVERY target word exactly once as a gap; id g0, g1, ... in order.
- hint_vi is Vietnamese meaning in parentheses like (sự thỏa thuận).
- answers must match the English word form used in context (lowercase unless proper noun).
- Natural grammar; gaps replace only the target word.
- Add exactly 2 multiple-choice questions (4 options each) testing comprehension of the passage content (main idea, inference, detail). Do not ask for gap words."""


def _parse_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def _call_openrouter(words_payload: list[dict]) -> dict[str, Any]:
    user = json.dumps({"target_words": words_payload}, ensure_ascii=False)
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user},
    ]
    data, _model = await chat_completion_json(
        messages,
        max_tokens=1200,
        temperature=0.35,
        timeout=_AI_TIMEOUT,
        title="LinguaIELTS Vocab Reading",
    )
    return data


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
    return {
        "paragraphs": [{"parts": parts}],
        "answers": answers,
        "comprehension_questions": _fallback_comprehension_questions(words),
    }


def _fallback_comprehension_questions(words: list[dict]) -> list[dict[str, Any]]:
    """Simple MCQ when AI omits comprehension_questions."""
    w0 = words[0] if words else {"word": "vocabulary", "meaning_vi": "từ vựng"}
    w1 = words[1] if len(words) > 1 else w0
    return [
        {
            "id": "cq0",
            "stem": "Which topic does the passage mainly relate to?",
            "options": [
                {"id": "a", "text": f"Using words such as «{w0['word']}» in context"},
                {"id": "b", "text": "Sports and entertainment only"},
                {"id": "c", "text": "Historical dates and events"},
                {"id": "d", "text": "Cooking recipes"},
            ],
            "correct_id": "a",
        },
        {
            "id": "cq1",
            "stem": "The passage is written primarily to help learners with:",
            "options": [
                {"id": "a", "text": "Pronunciation of proper nouns"},
                {"id": "b", "text": f"Vocabulary including «{w1['word']}»"},
                {"id": "c", "text": "Mathematical formulas"},
                {"id": "d", "text": "Letter writing formats"},
            ],
            "correct_id": "b",
        },
    ]


def _normalize_comprehension(raw: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, q in enumerate(raw or []):
        if not isinstance(q, dict):
            continue
        opts = []
        for o in q.get("options") or []:
            if isinstance(o, dict) and o.get("id") and o.get("text"):
                opts.append({"id": str(o["id"]), "text": str(o["text"])})
        if len(opts) < 2:
            continue
        cid = str(q.get("correct_id") or "")
        if cid not in {o["id"] for o in opts}:
            cid = opts[0]["id"]
        out.append({
            "id": str(q.get("id") or f"cq{i}"),
            "stem": str(q.get("stem") or "Choose the best answer."),
            "options": opts[:4],
            "correct_id": cid,
        })
        if len(out) >= 3:
            break
    return out


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
    comp = _normalize_comprehension(raw.get("comprehension_questions"))
    if not comp:
        comp = _fallback_comprehension_questions(words)
    return {
        "paragraphs": paragraphs,
        "answers": answers,
        "comprehension_questions": comp,
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

    if has_openrouter_keys():
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
