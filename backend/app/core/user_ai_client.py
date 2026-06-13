"""
Per-user AI routing — personal OpenRouter API key.

When a user configures their OpenRouter key in Profile, conversation / writing /
translation use that key instead of the shared server OPENROUTER_API_KEY.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.core.openrouter_client import (
    chat_completion,
    chat_completion_json,
    has_openrouter_keys,
    parse_json_content,
)
from app.core.user_ai_secrets import decrypt_api_key
from app.db.models import UserProfile

logger = logging.getLogger(__name__)

VALID_PROVIDERS = frozenset({"system", "openrouter"})
_LEGACY_PROVIDERS = frozenset({"gemini", "openai", "grok"})


@dataclass(frozen=True)
class UserAISettings:
    provider: str = "system"
    api_key: str | None = None

    @property
    def is_active(self) -> bool:
        return self.provider == "openrouter" and bool(self.api_key)


def load_user_ai(profile: UserProfile | None) -> UserAISettings:
    if not profile:
        return UserAISettings()
    provider = (profile.ai_provider or "system").strip().lower()
    if provider in _LEGACY_PROVIDERS:
        logger.info(
            "user_id=%s has legacy AI provider %s — requires OpenRouter key",
            profile.user_id,
            provider,
        )
        return UserAISettings()
    if provider not in VALID_PROVIDERS:
        provider = "system"
    api_key: str | None = None
    if provider == "openrouter" and profile.ai_api_key_encrypted:
        try:
            api_key = decrypt_api_key(profile.ai_api_key_encrypted)
        except ValueError:
            logger.warning("Could not decrypt AI key for user_id=%s", profile.user_id)
    return UserAISettings(provider=provider, api_key=api_key)


def has_user_ai_available(ai: UserAISettings | None = None) -> bool:
    """True only when the user configured a personal OpenRouter API key."""
    return bool(ai and ai.is_active)


def has_ai_available(ai: UserAISettings | None = None) -> bool:
    if ai and ai.is_active:
        return True
    return has_openrouter_keys()


async def ai_chat_completion(
    messages: list[dict[str, str]],
    *,
    ai: UserAISettings | None = None,
    model: str | None = None,
    max_tokens: int = 900,
    temperature: float = 0.3,
    timeout: float = 60.0,
    title: str = "LinguaIELTS",
) -> tuple[str, str]:
    if ai and ai.is_active:
        return await chat_completion(
            messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            title=title,
            api_keys=[ai.api_key or ""],
        )
    return await chat_completion(
        messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        title=title,
    )


async def ai_chat_completion_json(
    messages: list[dict[str, str]],
    *,
    ai: UserAISettings | None = None,
    model: str | None = None,
    max_tokens: int = 900,
    temperature: float = 0.15,
    timeout: float = 60.0,
    title: str = "LinguaIELTS",
) -> tuple[dict[str, Any], str]:
    raw, used = await ai_chat_completion(
        messages,
        ai=ai,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        title=title,
    )
    return parse_json_content(raw), used
