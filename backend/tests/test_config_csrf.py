"""Tests for CSRF trusted origins in Settings."""

from app.core.config import Settings

_SECRET = "a" * 32


def test_csrf_trusted_origins_includes_frontend_origin():
    s = Settings(
        SECRET_KEY=_SECRET,
        FRONTEND_ORIGIN="https://app.example.com",
        CSRF_TRUSTED_ORIGINS="https://cdn.example.com",
        ENVIRONMENT="production",
        METRICS_TOKEN="metrics-token-for-test-only",
    )
    assert "https://app.example.com" in s.csrf_trusted_origins
    assert "https://cdn.example.com" in s.csrf_trusted_origins


def test_csrf_trusted_origins_includes_localhost_in_dev():
    s = Settings(
        SECRET_KEY=_SECRET,
        FRONTEND_ORIGIN="http://localhost:5173",
        ENVIRONMENT="development",
    )
    assert "http://localhost:5173" in s.csrf_trusted_origins
