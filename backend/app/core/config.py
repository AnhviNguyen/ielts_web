"""
app/core/config.py
──────────────────
Application settings loaded from environment variables / .env file.
Uses pydantic-settings for type-safe configuration.
"""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "LinguaIELTS API"
    DEBUG: bool = False
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./linguaielts.db"

    # ── JWT ──────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ADMIN_EMAILS: str = ""
    AVATAR_UPLOAD_DIR: str = "uploads/avatars"

    # ── ML / Speaking pipeline ────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    # Must be a model slug that exists on OpenRouter (mistral-7b-instruct returns 404).
    OPENROUTER_FAST_MODEL: str = "google/gemini-2.0-flash-001"
    PRON_MODEL_PATH: str = "model/pron_scorer_best.pt"
    WHISPER_MODEL_SIZE: str = "base"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "dev", "development"}:
                return True
        return value


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance (singleton pattern)."""
    return Settings()


# Module-level singleton for convenience imports
settings = get_settings()


def admin_email_set() -> set[str]:
    """Return lowercase admin bootstrap emails from ADMIN_EMAILS."""
    return {
        email.strip().lower()
        for email in settings.ADMIN_EMAILS.split(",")
        if email.strip()
    }
