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
    # Production: postgresql+asyncpg://linguaielts:password@localhost:5432/linguaielts
    # Local demo:  sqlite+aiosqlite:///./linguaielts.db
    DATABASE_URL: str = "postgresql+asyncpg://linguaielts:password@localhost:5432/linguaielts"

    # ── Redis / Celery ─────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_ENABLED: bool = False
    # Production: fail startup/health when Redis unreachable (default true if ENVIRONMENT=production)
    REDIS_REQUIRED: bool | None = None
    # Use PgBouncer transaction pool — disables asyncpg prepared statement cache
    PGBOUNCER_ENABLED: bool = False

    # ── JWT ──────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ADMIN_EMAILS: str = ""
    AVATAR_UPLOAD_DIR: str = "uploads/avatars"

    # ── Object storage (S3 / MinIO) ─────────────────────────────
    STORAGE_BACKEND: str = "local"  # local | s3
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "linguaielts"
    S3_REGION: str = "us-east-1"
    # Public URL prefix for browser (CDN, gateway /media/, or MinIO direct)
    S3_PUBLIC_BASE_URL: str = ""

    # ── Metrics ────────────────────────────────────────────────
    METRICS_ENABLED: bool = True

    # ── ML preload ─────────────────────────────────────────────
    ML_PRELOAD_ON_STARTUP: bool | None = None

    # ── History archive ──────────────────────────────────────────
    HISTORY_ARCHIVE_AFTER_DAYS: int = 365

    # ── Auth cookies (refresh httpOnly + CSRF) ───────────────────
    AUTH_HTTPONLY_REFRESH: bool | None = None

    # ── Observability ──────────────────────────────────────────
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"
    # When False, startup skips SQLAlchemy create_all (use Alembic upgrade head in production).
    AUTO_CREATE_TABLES: bool = True

    # ── Email (password reset) ─────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True
    PASSWORD_RESET_EXPIRE_HOURS: int = 24

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

    @property
    def redis_required(self) -> bool:
        if self.REDIS_REQUIRED is not None:
            return self.REDIS_REQUIRED
        return self.ENVIRONMENT == "production"

    @property
    def ml_preload_on_startup(self) -> bool:
        """API workers skip heavy ML load when Celery handles speaking/shadowing."""
        if self.ML_PRELOAD_ON_STARTUP is not None:
            return self.ML_PRELOAD_ON_STARTUP
        if self.ENVIRONMENT == "production":
            return False
        return not self.CELERY_ENABLED

    @property
    def auth_httponly_refresh(self) -> bool:
        if self.AUTH_HTTPONLY_REFRESH is not None:
            return self.AUTH_HTTPONLY_REFRESH
        return self.ENVIRONMENT == "production"


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
