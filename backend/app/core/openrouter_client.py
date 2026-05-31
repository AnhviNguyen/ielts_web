"""
Shared OpenRouter HTTP client — multi-key rotation + free-model cascade.

Designed so many users share AI capacity without exhausting a single key/model:
  1. OPENROUTER_PREFER_FREE=true → try :free models first (no token cost)
  2. Multiple keys (OPENROUTER_API_KEY + OPENROUTER_API_KEYS) rotated on 402/429
  3. Full model cascade per key before moving to the next key
  4. provider.allow_fallbacks lets OpenRouter route to alternate providers
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_FREE_MODELS: tuple[str, ...] = (
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-3-12b-it:free",
)

_RETRYABLE_STATUS = frozenset({402, 404, 429, 503})
_FALLBACK_MODEL = "anthropic/claude-3-haiku"

_key_rr = 0
_key_lock = threading.Lock()


def openrouter_keys() -> list[str]:
    """Primary key + comma-separated extras (deduped)."""
    out: list[str] = []
    primary = (settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "") or "").strip()
    if primary:
        out.append(primary)
    extra = (getattr(settings, "OPENROUTER_API_KEYS", None) or os.getenv("OPENROUTER_API_KEYS", "") or "").strip()
    for k in extra.split(","):
        k = k.strip()
        if k and k not in out:
            out.append(k)
    return out


def openrouter_key() -> str:
    keys = openrouter_keys()
    return keys[0] if keys else ""


def has_openrouter_keys() -> bool:
    return bool(openrouter_keys())


def free_models() -> list[str]:
    raw = (getattr(settings, "OPENROUTER_FREE_MODELS", None) or "").strip()
    if raw:
        return [m.strip() for m in raw.split(",") if m.strip()]
    return list(DEFAULT_FREE_MODELS)


def prefer_free_models() -> bool:
    val = getattr(settings, "OPENROUTER_PREFER_FREE", None)
    if val is not None:
        return bool(val)
    return settings.ENVIRONMENT == "production"


def build_model_cascade(preferred: str | None = None, *, prefer_free: bool | None = None) -> list[str]:
    """Build deduped model list. Free-first when prefer_free=True (default in production)."""
    use_free_first = prefer_free_models() if prefer_free is None else prefer_free
    primary = (
        (preferred or "").strip()
        or (settings.OPENROUTER_FAST_MODEL or "").strip()
        or "google/gemini-2.0-flash-001"
    )
    free = free_models()
    if use_free_first:
        candidates = (*free, primary, _FALLBACK_MODEL)
    else:
        candidates = (primary, *free, _FALLBACK_MODEL)
    out: list[str] = []
    for m in candidates:
        if m and m not in out:
            out.append(m)
    return out


def _rotate_keys(keys: list[str]) -> list[str]:
    global _key_rr
    if len(keys) <= 1:
        return keys
    with _key_lock:
        start = _key_rr % len(keys)
        _key_rr += 1
    return keys[start:] + keys[:start]


def default_headers(*, title: str = "LinguaIELTS", api_key: str | None = None) -> dict[str, str]:
    key = (api_key or openrouter_key()).strip()
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.FRONTEND_ORIGIN or "http://localhost:5173",
        "X-Title": title,
    }


def _should_try_next_model(exc: httpx.HTTPStatusError) -> bool:
    if exc.response.status_code in _RETRYABLE_STATUS:
        return True
    try:
        body = exc.response.json()
        msg = str(body.get("error", {}).get("message", "")).lower()
        if any(k in msg for k in ("quota", "credit", "rate limit", "insufficient", "no endpoints", "overloaded")):
            return True
    except Exception:
        pass
    return False


def should_retry_model(exc: httpx.HTTPStatusError) -> bool:
    return _should_try_next_model(exc)


def should_try_next_key(exc: httpx.HTTPStatusError) -> bool:
    """Rotate API key on account-level quota / rate-limit errors."""
    if exc.response.status_code in {402, 429}:
        return True
    return _should_try_next_model(exc)


def parse_json_content(raw: str) -> dict[str, Any]:
    """Extract and parse a JSON object from model output."""
    text = (raw or "").strip()
    if not text:
        raise json.JSONDecodeError("Empty AI response", text, 0)

    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        data = json.loads(match.group(0))
        if isinstance(data, dict):
            return data

    raise json.JSONDecodeError("No JSON object in AI response", text, 0)


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int = 900,
    temperature: float = 0.3,
    timeout: float = 60.0,
    title: str = "LinguaIELTS",
    extra_payload: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    POST to OpenRouter with key rotation + model cascade.

    Returns (content, model_used).
    """
    keys = openrouter_keys()
    if not keys:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    cascade = build_model_cascade(model)
    last_exc: Exception | None = None

    for api_key in _rotate_keys(keys):
        headers = default_headers(title=title, api_key=api_key)
        key_failed = False
        async with httpx.AsyncClient(timeout=timeout) as client:
            for model_id in cascade:
                payload: dict[str, Any] = {
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "provider": {"allow_fallbacks": True},
                }
                if extra_payload:
                    payload.update(extra_payload)
                try:
                    resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
                    resp.raise_for_status()
                    content = resp.json()["choices"][0]["message"]["content"]
                    logger.debug("OpenRouter OK model=%s key=...%s", model_id, api_key[-6:])
                    return content, model_id
                except httpx.HTTPStatusError as exc:
                    last_exc = exc
                    if should_try_next_key(exc) and len(keys) > 1:
                        logger.warning(
                            "OpenRouter key ...%s exhausted (%s), rotating key",
                            api_key[-6:],
                            exc.response.status_code,
                        )
                        key_failed = True
                        break
                    if _should_try_next_model(exc) and model_id != cascade[-1]:
                        logger.warning(
                            "OpenRouter model %s failed (%s), trying next model",
                            model_id,
                            exc.response.status_code,
                        )
                        continue
                    raise
        if not key_failed:
            break

    raise last_exc or RuntimeError("OpenRouter request failed")


async def chat_completion_json(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int = 900,
    temperature: float = 0.15,
    timeout: float = 60.0,
    title: str = "LinguaIELTS",
) -> tuple[dict[str, Any], str]:
    raw, used = await chat_completion(
        messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        title=title,
    )
    return parse_json_content(raw), used
