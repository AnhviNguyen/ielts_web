"""OpenRouter + JSON helpers shared by speaking router and eval service."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings
from app.core.openrouter_client import (
    build_model_cascade,
    chat_completion,
    chat_completion_json,
    has_openrouter_keys,
    openrouter_key,
)
from app.core.user_ai_client import UserAISettings, ai_chat_completion, ai_chat_completion_json

logger = logging.getLogger(__name__)

AI_MODEL = "anthropic/claude-3-haiku"
AI_TIMEOUT = 60.0

OPENROUTER_KEY = openrouter_key()
AI_MODEL_FAST = (
    getattr(settings, "OPENROUTER_FAST_MODEL", None)
    or os.getenv("OPENROUTER_FAST_MODEL", "google/gemini-2.0-flash-001")
)

CARDS_SYSTEM = (
    "You are an IELTS Speaking language analyst. "
    "Analyze ONLY the candidate transcript (Whisper ASR text). "
    "Return ONLY valid JSON, no markdown. "
    "Every highlight field `text` MUST be an exact substring copied from the transcript."
)

SYSTEM_PROMPT = (
    "You are an IELTS Speaking examiner. Analyze the candidate's spoken response. "
    "Return ONLY valid JSON, no markdown, no explanation. "
    "All string values must escape internal double quotes."
)

def _build_language_cards_prompt(question_text: str, transcript: str) -> str:
    return f"""IELTS question: {question_text or "(not provided)"}
Candidate transcript (Whisper):
\"\"\"{transcript}\"\"\"

Return JSON with EXACTLY this structure:
{{
  "grammar_analysis": {{
    "score": <float 0-9>,
    "errors": [
      {{
        "text": "<exact erroneous phrase from transcript>",
        "error_type": "<e.g. subject-verb agreement, tense, article, word order>",
        "correction": "<corrected phrase or sentence>",
        "explanation": "<short explanation in English>"
      }}
    ]
  }},
  "vocabulary_analysis": {{
    "score": <float 0-9>,
    "weak_words": [
      {{"text": "<exact weak/repeated word or phrase from transcript>", "reason": "<why it is weak>"}}
    ],
    "strong_words": [
      {{"text": "<exact strong word/phrase or collocation from transcript>", "reason": "<why it is strong>"}}
    ],
    "replacements": [
      {{"weak": "<weak word>", "better": "<better alternative>", "reason": "<short reason>"}}
    ]
  }}
}}

Rules:
- Find real grammar mistakes in the transcript (not invented).
- Mark weak/repeated basic words for vocabulary; mark strong collocations separately.
- If transcript is empty, return score 0 and empty arrays."""


def _openrouter_model_candidates(preferred: str | None) -> list[str]:
    """Primary → free models → stable fallback. Delegates to shared cascade."""
    return build_model_cascade(preferred or AI_MODEL_FAST)


async def _call_openrouter_json(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 900,
    ai: UserAISettings | None = None,
) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        if ai and ai.is_active:
            data, _used = await ai_chat_completion_json(
                messages,
                ai=ai,
                model=model,
                max_tokens=max_tokens,
                timeout=AI_TIMEOUT,
                title="LinguaIELTS",
            )
            return data
        data, _used = await chat_completion_json(
            messages,
            model=model,
            max_tokens=max_tokens,
            timeout=AI_TIMEOUT,
            title="LinguaIELTS",
        )
        return data
    except json.JSONDecodeError as exc:
        logger.warning("Cards JSON parse failed, repair pass: %s", exc)
        if ai and ai.is_active:
            raw, _ = await ai_chat_completion(
                messages,
                ai=ai,
                model=model,
                max_tokens=max_tokens,
                timeout=AI_TIMEOUT,
                title="LinguaIELTS",
            )
        else:
            raw, _ = await chat_completion(
                messages,
                model=model,
                max_tokens=max_tokens,
                timeout=AI_TIMEOUT,
                title="LinguaIELTS",
            )
        repaired = await _repair_ai_json_via_model(raw)
        return _parse_ai_json(repaired)


async def _call_language_cards(
    question_text: str, transcript: str, *, ai: UserAISettings | None = None
) -> dict[str, Any]:
    return await _call_openrouter_json(
        CARDS_SYSTEM,
        _build_language_cards_prompt(question_text, transcript),
        ai=ai,
    )


def _normalize_grammar_analysis(ai: dict[str, Any]) -> dict[str, Any]:
    ga = ai.get("grammar_analysis") if isinstance(ai.get("grammar_analysis"), dict) else {}
    score = _safe_score_0_9(
        ga.get("score")
        or ai.get("grammar_score")
        or ai.get("grammar_range_accuracy_score")
    )
    errors_raw = ga.get("errors") or ai.get("grammar_errors") or []
    errors: list[dict[str, str]] = []
    for e in errors_raw:
        if not isinstance(e, dict):
            continue
        text = str(e.get("text") or e.get("original") or "").strip()
        if not text:
            continue
        errors.append({
            "text": text,
            "error_type": str(e.get("error_type") or e.get("type") or "grammar").strip(),
            "correction": str(e.get("correction") or "").strip(),
            "explanation": str(e.get("explanation") or "").strip(),
        })
    return {"score": score, "errors": errors}


def _normalize_vocabulary_analysis(ai: dict[str, Any]) -> dict[str, Any]:
    va = ai.get("vocabulary_analysis") if isinstance(ai.get("vocabulary_analysis"), dict) else {}
    score = _safe_score_0_9(
        va.get("score")
        or ai.get("vocabulary_score")
        or ai.get("lexical_resource_score")
    )
    weak = []
    for w in va.get("weak_words") or []:
        if not isinstance(w, dict):
            continue
        text = str(w.get("text") or w.get("word") or "").strip()
        if text:
            weak.append({"text": text, "reason": str(w.get("reason") or "").strip()})
    strong = []
    for w in va.get("strong_words") or []:
        if not isinstance(w, dict):
            continue
        text = str(w.get("text") or w.get("word") or "").strip()
        if text:
            strong.append({"text": text, "reason": str(w.get("reason") or "").strip()})
    reps = []
    for r in va.get("replacements") or va.get("feedback") or ai.get("vocabulary_feedback") or []:
        if not isinstance(r, dict):
            continue
        weak_w = str(r.get("weak") or r.get("word_used") or r.get("text") or "").strip()
        better = str(r.get("better") or r.get("better_alternative") or "").strip()
        if weak_w or better:
            reps.append({
                "weak": weak_w,
                "better": better,
                "reason": str(r.get("reason") or "").strip(),
            })
    return {
        "score": score,
        "weak_words": weak,
        "strong_words": strong,
        "replacements": reps,
    }

def _build_user_prompt(question_text: str, transcript: str) -> str:
    # band_estimate is intentionally omitted — the server computes it from the
    # four IELTS criteria so the LLM cannot inflate it independently.
    return f"""IELTS Question: {question_text}
Candidate's transcript: {transcript}

You are scoring ONLY the linguistic content of the transcript (not audio quality).
Use IELTS Speaking descriptors and evaluate exactly these 4 criteria:
1) Fluency & Coherence
2) Lexical Resource
3) Grammatical Range & Accuracy
4) Pronunciation (text-based impression only; acoustic model score is computed separately by backend).

Evaluate and return JSON with EXACTLY this structure (all scores on IELTS 0-9 scale):
{{
  "fluency_coherence_score": <float 0-9>,
  "lexical_resource_score": <float 0-9>,
  "grammar_range_accuracy_score": <float 0-9>,
  "pronunciation_text_score": <float 0-9>,
  "grammar_score": <float 0-9, same as grammar_range_accuracy_score>,
  "vocabulary_score": <float 0-9, same as lexical_resource_score>,
  "coherence_score": <float 0-9, same as fluency_coherence_score>,
  "task_response_score": <float 0-9, relevance to the IELTS question / avoid off-topic>,
  "is_off_topic": <true|false>,
  "task_response_comment": "1 short sentence about whether answer addresses the prompt",
  "grammar_errors": [
    {{"original": "...", "correction": "...", "explanation": "..."}}
  ],
  "grammar_analysis": {{
    "score": <float 0-9>,
    "errors": [
      {{
        "text": "<exact erroneous phrase copied from transcript>",
        "error_type": "<e.g. subject-verb agreement, tense>",
        "correction": "<corrected phrase>",
        "explanation": "<short explanation>"
      }}
    ]
  }},
  "vocabulary_feedback": [
    {{"word_used": "...", "better_alternative": "...", "reason": "..."}}
  ],
  "vocabulary_analysis": {{
    "score": <float 0-9>,
    "weak_words": [{{"text": "<exact phrase>", "reason": "..."}}],
    "strong_words": [{{"text": "<exact phrase>", "reason": "..."}}],
    "replacements": [{{"weak": "...", "better": "...", "reason": "..."}}]
  }},
  "overall_comment": "2-3 sentence summary in English",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "band_boost_tips": [
    "Actionable tip 1 for raising band",
    "Actionable tip 2 for raising band",
    "Actionable tip 3 for raising band"
  ],
  "upgraded_sample_answer": "A stronger model response (around 100-160 words) that addresses the same IELTS question with better coherence, vocabulary, and grammar.",
  "criteria_feedback": {{
    "fluency_coherence": {{
      "strengths": ["...", "..."],
      "issues": ["...", "..."],
      "advice": ["...", "..."]
    }},
    "lexical_resource": {{
      "strengths": ["...", "..."],
      "issues": ["...", "..."],
      "advice": ["...", "..."]
    }},
    "grammar_range_accuracy": {{
      "strengths": ["...", "..."],
      "issues": ["...", "..."],
      "advice": ["...", "..."]
    }}
  }}
}}

If the transcript is empty or unintelligible, return all scores as 0 and note it in overall_comment."""


async def _call_openrouter(question_text: str, transcript: str) -> dict[str, Any]:
    """Async OpenRouter call for speaking evaluation (key rotation + free cascade)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(question_text, transcript)},
    ]
    raw, _model = await chat_completion(
        messages,
        max_tokens=1200,
        temperature=0.2,
        timeout=AI_TIMEOUT,
        title="LinguaIELTS Speaking Eval",
    )
    try:
        return _parse_ai_json(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Primary AI JSON parse failed, trying repair pass: %s", exc)
        repaired_content = await _repair_ai_json_via_model(raw)
        return _parse_ai_json(repaired_content)


async def _repair_ai_json_via_model(raw_text: str) -> str:
    """
    Ask model to rewrite malformed analysis text into strict valid JSON.
    Returns raw text output from model (still parsed by _parse_ai_json afterwards).
    """
    repair_prompt = f"""Rewrite the following text into STRICT valid JSON only.
Do not add markdown.
Do not add explanations.
Keep exactly this schema and keys:
{{
  "fluency_coherence_score": <float 0-9>,
  "lexical_resource_score": <float 0-9>,
  "grammar_range_accuracy_score": <float 0-9>,
  "pronunciation_text_score": <float 0-9>,
  "grammar_score": <float 0-9>,
  "vocabulary_score": <float 0-9>,
  "coherence_score": <float 0-9>,
  "task_response_score": <float 0-9>,
  "is_off_topic": <true|false>,
  "task_response_comment": "...",
  "grammar_errors": [
    {{"original": "...", "correction": "...", "explanation": "..."}}
  ],
  "vocabulary_feedback": [
    {{"word_used": "...", "better_alternative": "...", "reason": "..."}}
  ],
  "overall_comment": "2-3 sentence summary in English",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "band_boost_tips": ["...", "...", "..."],
  "upgraded_sample_answer": "...",
  "criteria_feedback": {{
    "fluency_coherence": {{"strengths": ["..."], "issues": ["..."], "advice": ["..."]}},
    "lexical_resource": {{"strengths": ["..."], "issues": ["..."], "advice": ["..."]}},
    "grammar_range_accuracy": {{"strengths": ["..."], "issues": ["..."], "advice": ["..."]}}
  }}
}}

Input text to normalize:
{raw_text}
"""
    raw, _model = await chat_completion(
        [
            {"role": "system", "content": "You convert malformed JSON-like text into strict valid JSON."},
            {"role": "user", "content": repair_prompt},
        ],
        model=AI_MODEL,
        max_tokens=800,
        temperature=0,
        timeout=AI_TIMEOUT,
        title="LinguaIELTS JSON Repair",
    )
    return raw


def _extract_json_candidate(text: str) -> str:
    """
    Extract the most likely JSON object from model output.
    Handles markdown fences and extra prose around JSON.
    """
    raw = (text or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1].strip()
    return raw


def _parse_ai_json(text: str) -> dict[str, Any]:
    """
    Parse model output to JSON with small repair attempts.
    Raises JSONDecodeError if still invalid.
    """
    candidate = _extract_json_candidate(text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Common normalization for smart quotes and accidental trailing commas.
        repaired = (
            candidate
            .replace("“", "\"")
            .replace("”", "\"")
            .replace("’", "'")
            .replace(",]", "]")
            .replace(",}", "}")
        )
        return json.loads(repaired)


def _empty_criteria_feedback() -> dict[str, Any]:
    return {
        "fluency_coherence": {"strengths": [], "issues": [], "advice": []},
        "lexical_resource": {"strengths": [], "issues": [], "advice": []},
        "grammar_range_accuracy": {"strengths": [], "issues": [], "advice": []},
    }


def _safe_score_0_9(value: Any) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(9.0, num))
