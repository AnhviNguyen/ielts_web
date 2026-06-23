"""
app/core/config.py
──────────────────
Application settings loaded from environment variables / .env file.
Uses pydantic-settings for type-safe configuration.
"""

from functools import lru_cache
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_WEAK_SECRET_MARKERS = (
    "change-this",
    "changeme",
    "minioadmin",
    "password",
    "secret",
    "example",
    "yourdomain",
)


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
    # Deprecated — no runtime effect. Use app.cli.promote_admin instead.
    ADMIN_EMAILS: str = ""
    AVATAR_UPLOAD_DIR: str = "uploads/avatars"

    # ── Object storage (local / S3 / Cloudinary) ─────────────────
    STORAGE_BACKEND: str = "local"  # local | s3 | cloudinary
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "linguaielts"
    S3_REGION: str = "us-east-1"
    # Public URL prefix for browser (CDN, gateway /media/, or MinIO direct)
    S3_PUBLIC_BASE_URL: str = ""

    # Cloudinary (STORAGE_BACKEND=cloudinary) — quiz audio/images on CDN
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── Metrics ────────────────────────────────────────────────
    METRICS_ENABLED: bool = True
    # Bearer token required for GET /metrics when ENVIRONMENT=production
    METRICS_TOKEN: str = ""

    # ── ML preload ─────────────────────────────────────────────
    ML_PRELOAD_ON_STARTUP: bool | None = None
    # HuggingFace Model Repository for downloading model files at runtime
    HF_MODEL_REPO_ID: str = "phuc7/linguaielts-models"

    # ── History archive ──────────────────────────────────────────
    HISTORY_ARCHIVE_AFTER_DAYS: int = 365

    # ── Score forecast (NeuralProphet) ───────────────────────────
    FORECAST_ENABLED: bool = True
    FORECAST_MODEL_DIR: str = "models/forecast"
    FORECAST_LOOKBACK_DAYS: int = 30
    FORECAST_HORIZON_DAYS: int = 14
    FORECAST_MIN_DAYS: int = 14

    # ── Next-week band prediction (RandomForest, ielts_model) ────
    NEXT_WEEK_ENABLED: bool = True
    NEXT_WEEK_MODEL_PATH: str = "model/next_week_ielts.joblib"
    # Minimum weekly buckets of practice data required before predicting
    NEXT_WEEK_MIN_WEEKS: int = 2
    # How many recent weeks of score_history to feed the model
    NEXT_WEEK_LOOKBACK_WEEKS: int = 12

    # ── Auth cookies (refresh httpOnly + CSRF) ───────────────────
    AUTH_HTTPONLY_REFRESH: bool | None = None
    # When None, Secure cookies only if ENVIRONMENT=production (set false for local Docker over HTTP).
    AUTH_COOKIE_SECURE: bool | None = None
    # Comma-separated SPA origins that may skip double-submit CSRF (Origin/Referer check).
    # FRONTEND_ORIGIN is always included automatically.
    CSRF_TRUSTED_ORIGINS: str = ""

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
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = ""
    BREVO_API_KEY: str = ""
    BREVO_FROM: str = ""

    PLACEMENT_REQUIRED_AFTER: str = "2026-06-09T00:00:00+07:00"


    # ── Google OAuth ───────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # Registered redirect URI in Google Cloud Console
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/auth/google/callback"

    # ── Email verification ─────────────────────────────────────
    EMAIL_VERIFY_EXPIRE_MINUTES: int = 15
    REQUIRE_EMAIL_VERIFICATION: bool = True

    # ── ML / Speaking pipeline ────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    # Additional keys (comma-separated) — rotated when one hits quota/rate-limit.
    OPENROUTER_API_KEYS: str = ""
    # Must be a model slug that exists on OpenRouter (mistral-7b-instruct returns 404).
    OPENROUTER_FAST_MODEL: str = "google/gemini-2.0-flash-001"
    # Comma-separated free models tried when primary hits quota (see openrouter_client.py).
    OPENROUTER_FREE_MODELS: str = ""
    # When True (default in production), try :free models before paid primary.
    OPENROUTER_PREFER_FREE: bool | None = None
    PRON_MODEL_PATH: str = "model/pron_scorer_best.pt"
    # faster-whisper model id (e.g. large-v3, base, small)
    WHISPER_MODEL_SIZE: str = "large-v3"
    WHISPER_DEVICE: str = "cpu"
    # int8 on CPU saves RAM (~2–3 GB for large-v3); use float16 on GPU
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_CPU_THREADS: int = 4
    WHISPER_NUM_WORKERS: int = 1
    # When false, skip Whisper fallback only; videos with YouTube captions still work.
    # Defaults to ml_preload_on_startup when unset.
    WHISPER_ENABLED: bool | None = None

    # YouTube — optional residential proxy (Webshare / generic) for transcript-api on cloud VPS
    YOUTUBE_PROXY_URL: str = ""
    YOUTUBE_WEBSHARE_USERNAME: str = ""
    YOUTUBE_WEBSHARE_PASSWORD: str = ""

    # Supadata — YouTube transcript API (bypasses Oracle/cloud IP blocks)
    SUPADATA_API_KEY: str = ""

    # Apify — YouTube transcript actor fallback (https://apify.com/codepoetry/youtube-transcript-ai-scraper)
    APIFY_API_TOKEN: str = ""
    APIFY_YOUTUBE_TRANSCRIPT_ACTOR: str = "codepoetry~youtube-transcript-ai-scraper"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: Any) -> Any:
        """Railway/Heroku often provide postgresql:// — app needs postgresql+asyncpg://."""
        if not isinstance(value, str):
            return value
        url = value.strip()
        if url.startswith("postgres://"):
            url = f"postgresql+asyncpg://{url[len('postgres://'):]}"
        elif url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
            url = f"postgresql+asyncpg://{url[len('postgresql://'):]}"
        
        # asyncpg does not support sslmode parameter, but supports ssl
        # Replace sslmode= with ssl=
        if "?sslmode=" in url:
            url = url.replace("?sslmode=", "?ssl=")
        elif "&sslmode=" in url:
            url = url.replace("&sslmode=", "&ssl=")
            
        return url

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
    def whisper_enabled(self) -> bool:
        """Whisper fallback for videos without YouTube captions (heavy — off on small workers)."""
        if self.WHISPER_ENABLED is not None:
            return self.WHISPER_ENABLED
        return self.ml_preload_on_startup

    @property
    def auth_httponly_refresh(self) -> bool:
        if self.AUTH_HTTPONLY_REFRESH is not None:
            return self.AUTH_HTTPONLY_REFRESH
        return self.ENVIRONMENT == "production"

    @property
    def auth_cookie_secure(self) -> bool:
        if self.AUTH_COOKIE_SECURE is not None:
            return self.AUTH_COOKIE_SECURE
        return self.ENVIRONMENT == "production"

    @property
    def csrf_trusted_origins(self) -> frozenset[str]:
        """Origins allowed to skip double-submit CSRF via Origin/Referer validation."""
        origins: set[str] = set()
        for raw in (self.CSRF_TRUSTED_ORIGINS, self.FRONTEND_ORIGIN):
            for part in raw.split(","):
                origin = part.strip().rstrip("/")
                if origin:
                    origins.add(origin)
        if self.ENVIRONMENT != "production":
            origins.update(
                {
                    "http://localhost:5173",
                    "http://localhost:3000",
                    "http://127.0.0.1:5173",
                }
            )
        return frozenset(origins)

    @staticmethod
    def _looks_weak_secret(value: str, *, min_len: int = 32) -> bool:
        normalized = (value or "").strip().lower()
        if len(normalized) < min_len:
            return True
        return any(marker in normalized for marker in _WEAK_SECRET_MARKERS)

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT != "production":
            return self
        if self._looks_weak_secret(self.SECRET_KEY):
            raise ValueError(
                "SECRET_KEY is missing or uses a weak/default value. "
                "Generate one with: openssl rand -hex 32"
            )
        if self.METRICS_ENABLED and not (self.METRICS_TOKEN or "").strip():
            raise ValueError(
                "METRICS_TOKEN is required when METRICS_ENABLED=true in production."
            )
        if self.STORAGE_BACKEND.lower() == "s3":
            if self._looks_weak_secret(self.S3_SECRET_KEY, min_len=16):
                raise ValueError("S3_SECRET_KEY must be a strong secret in production.")
            if self._looks_weak_secret(self.S3_ACCESS_KEY, min_len=8):
                raise ValueError("S3_ACCESS_KEY must not use default credentials in production.")
        if self.STORAGE_BACKEND.lower() == "cloudinary":
            if not (self.CLOUDINARY_CLOUD_NAME or "").strip():
                raise ValueError("CLOUDINARY_CLOUD_NAME is required when STORAGE_BACKEND=cloudinary.")
            if not (self.CLOUDINARY_API_KEY or "").strip():
                raise ValueError("CLOUDINARY_API_KEY is required when STORAGE_BACKEND=cloudinary.")
            if self._looks_weak_secret(self.CLOUDINARY_API_SECRET, min_len=16):
                raise ValueError("CLOUDINARY_API_SECRET must be a strong secret in production.")
        db_url = self.DATABASE_URL.lower()
        if ":password@" in db_url or ":changeme@" in db_url:
            raise ValueError("DATABASE_URL must not use default/weak DB passwords in production.")
        return self


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance (singleton pattern)."""
    return Settings()


# Module-level singleton for convenience imports
settings = get_settings()
