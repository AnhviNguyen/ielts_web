"""Tests for Whisper feature flag."""

from app.core.config import Settings

_SECRET = "a" * 32


def test_whisper_enabled_follows_ml_preload_when_unset():
    s = Settings(
        _env_file=None,
        SECRET_KEY=_SECRET,
        ENVIRONMENT="production",
        METRICS_TOKEN="metrics-token-for-test",
        DATABASE_URL="postgresql+asyncpg://linguaielts:secure-production-pass@localhost:5432/linguaielts",
        WHISPER_ENABLED=None,
    )
    assert s.ml_preload_on_startup is False
    assert s.whisper_enabled is False


def test_whisper_enabled_explicit_false():
    s = Settings(
        SECRET_KEY=_SECRET,
        ENVIRONMENT="development",
        ML_PRELOAD_ON_STARTUP=True,
        WHISPER_ENABLED=False,
    )
    assert s.whisper_enabled is False


def test_whisper_enabled_explicit_true():
    s = Settings(
        SECRET_KEY=_SECRET,
        ENVIRONMENT="production",
        ML_PRELOAD_ON_STARTUP=False,
        WHISPER_ENABLED=True,
        METRICS_TOKEN="metrics-token-for-test",
    )
    assert s.whisper_enabled is True
