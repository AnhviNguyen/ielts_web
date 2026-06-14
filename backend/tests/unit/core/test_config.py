"""
tests/unit/core/test_config.py
──────────────────────────────
Unit tests cho app/core/config.py — Settings validation, property logic.

Bao phủ:
  CFG-01  Load settings thành công (dev mode)
  CFG-02  Production + SECRET_KEY yếu → ValueError
  CFG-03  Production + METRICS_ENABLED + thiếu METRICS_TOKEN → ValueError
  CFG-04  Production + DATABASE_URL dùng :password@ → ValueError
  CFG-05  DEBUG="release" → parse thành False
  CFG-06  DEBUG="dev" → parse thành True
  CFG-07  redis_required = True khi ENVIRONMENT=production
  CFG-08  redis_required = False khi ENVIRONMENT=development
  CFG-09  ml_preload_on_startup = False khi CELERY_ENABLED=True (dev)
  CFG-10  auth_httponly_refresh = True khi ENVIRONMENT=production
  CFG-11  auth_cookie_secure = True khi ENVIRONMENT=production
  CFG-12  REDIS_REQUIRED override tường minh
"""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings(**overrides):
    """Tạo Settings instance với env vars tối thiểu + overrides."""
    # Xây env dict mới (không đụng os.environ thật)
    base = {
        "SECRET_KEY": "a-very-strong-secret-key-that-is-at-least-32-chars-long",
        "ENVIRONMENT": "development",
        "DATABASE_URL": "postgresql+asyncpg://user:pwd@localhost:5432/testdb",
    }
    base.update(overrides)

    # Import Settings class (không dùng cached singleton)
    from pydantic_settings import BaseSettings
    from app.core.config import Settings

    # Override env vars trong process environment tạm thời
    old_env = {k: os.environ.get(k) for k in base}
    try:
        for k, v in base.items():
            os.environ[k] = str(v)
        # Tắt .env file để test không bị ảnh hưởng
        s = Settings(_env_file=None)
    finally:
        for k, old_v in old_env.items():
            if old_v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = old_v
    return s


# ---------------------------------------------------------------------------
# CFG-01: Load settings thành công trong dev mode
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg01_load_dev_settings():
    s = _make_settings()
    assert s.ENVIRONMENT == "development"
    assert s.APP_NAME == "LinguaIELTS API"
    assert s.SECRET_KEY != ""


# ---------------------------------------------------------------------------
# CFG-02: Production + SECRET_KEY yếu → ValueError
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("weak_key", [
    "changeme",
    "secret",
    "short",                  # < 32 chars
    "this-has-the-word-secret-in-it-but-is-long-enough",
])
def test_cfg02_production_weak_secret_key_raises(weak_key):
    with pytest.raises((ValueError, ValidationError)):
        _make_settings(ENVIRONMENT="production", SECRET_KEY=weak_key)


# ---------------------------------------------------------------------------
# CFG-03: Production + METRICS_ENABLED=true + METRICS_TOKEN rỗng → ValueError
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg03_production_metrics_missing_token_raises():
    with pytest.raises((ValueError, ValidationError)):
        _make_settings(
            ENVIRONMENT="production",
            METRICS_ENABLED="true",
            METRICS_TOKEN="",  # rỗng
            # SECRET_KEY mạnh
            SECRET_KEY="a" * 40,
        )


# ---------------------------------------------------------------------------
# CFG-04: Production + DATABASE_URL dùng :password@ → ValueError
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("bad_url", [
    "postgresql+asyncpg://user:password@localhost/db",
    "postgresql+asyncpg://admin:changeme@db:5432/prod",
])
def test_cfg04_production_weak_db_password_raises(bad_url):
    with pytest.raises((ValueError, ValidationError)):
        _make_settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 40,
            METRICS_ENABLED="false",
            DATABASE_URL=bad_url,
        )


# ---------------------------------------------------------------------------
# CFG-05: DEBUG="release" → False
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg05_debug_release_string_parsed_as_false():
    s = _make_settings(DEBUG="release")
    assert s.DEBUG is False


# ---------------------------------------------------------------------------
# CFG-06: DEBUG="dev" → True
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg06_debug_dev_string_parsed_as_true():
    s = _make_settings(DEBUG="dev")
    assert s.DEBUG is True


# ---------------------------------------------------------------------------
# CFG-07: redis_required = True khi ENVIRONMENT=production
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg07_redis_required_true_in_production():
    s = _make_settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 40,
        METRICS_ENABLED="false",
        DATABASE_URL="postgresql+asyncpg://user:str0ngpwd@localhost/prod",
    )
    assert s.redis_required is True


# ---------------------------------------------------------------------------
# CFG-08: redis_required = False khi ENVIRONMENT=development
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg08_redis_required_false_in_development():
    s = _make_settings(ENVIRONMENT="development")
    assert s.redis_required is False


# ---------------------------------------------------------------------------
# CFG-09: ml_preload_on_startup = False khi CELERY_ENABLED=True (dev)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg09_ml_preload_disabled_when_celery_enabled():
    s = _make_settings(CELERY_ENABLED="true")
    assert s.ml_preload_on_startup is False


# ---------------------------------------------------------------------------
# CFG-10: auth_httponly_refresh property = True khi AUTH_HTTPONLY_REFRESH is None + production
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg10_auth_httponly_refresh_true_in_production():
    """Kiểm tra property logic trực tiếp mà không phụ thuộc vào .env."""
    from app.core.config import Settings

    # Tạo Settings instance riêng biệt với giá trị cụ thể
    s = _make_settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 40,
        METRICS_ENABLED="false",
        DATABASE_URL="postgresql+asyncpg://user:str0ngpwd@localhost/prod",
    )
    # Kiểm tra property logic dựa trục tiếp vào AUTH_HTTPONLY_REFRESH vs ENVIRONMENT
    if s.AUTH_HTTPONLY_REFRESH is None:
        # Property phải fallback vào ENVIRONMENT = production → True
        assert s.auth_httponly_refresh is True
    else:
        # .env đặt tường minh — property phản chiếu giá trị đó
        assert s.auth_httponly_refresh == s.AUTH_HTTPONLY_REFRESH


# CFG-10b: kiểm tra property logic truyền thống bằng namespace
@pytest.mark.unit
def test_cfg10b_auth_httponly_refresh_property_logic():
    """Test property logic độc lập khỏi Settings init bằng SimpleNamespace."""
    from types import SimpleNamespace
    from app.core.config import Settings

    # Giả lập Settings instance thuần túy
    fake = SimpleNamespace(
        AUTH_HTTPONLY_REFRESH=None,
        ENVIRONMENT="production",
    )
    # Gọi property logic trực tiếp
    result = Settings.auth_httponly_refresh.fget(fake)
    assert result is True

    # Khi AUTH_HTTPONLY_REFRESH = False thì luôn False bất kể ENVIRONMENT
    fake2 = SimpleNamespace(AUTH_HTTPONLY_REFRESH=False, ENVIRONMENT="production")
    result2 = Settings.auth_httponly_refresh.fget(fake2)
    assert result2 is False


# ---------------------------------------------------------------------------
# CFG-11: auth_cookie_secure property logic
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg11_auth_cookie_secure_true_in_production():
    s = _make_settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 40,
        METRICS_ENABLED="false",
        DATABASE_URL="postgresql+asyncpg://user:str0ngpwd@localhost/prod",
    )
    if s.AUTH_COOKIE_SECURE is None:
        assert s.auth_cookie_secure is True
    else:
        assert s.auth_cookie_secure == s.AUTH_COOKIE_SECURE


@pytest.mark.unit
def test_cfg11b_auth_cookie_secure_property_logic():
    from types import SimpleNamespace
    from app.core.config import Settings

    # None + production → True
    fake = SimpleNamespace(AUTH_COOKIE_SECURE=None, ENVIRONMENT="production")
    assert Settings.auth_cookie_secure.fget(fake) is True

    # None + development → False
    fake2 = SimpleNamespace(AUTH_COOKIE_SECURE=None, ENVIRONMENT="development")
    assert Settings.auth_cookie_secure.fget(fake2) is False

    # Explicit False → luôn False
    fake3 = SimpleNamespace(AUTH_COOKIE_SECURE=False, ENVIRONMENT="production")
    assert Settings.auth_cookie_secure.fget(fake3) is False


# ---------------------------------------------------------------------------
# CFG-12: REDIS_REQUIRED tường minh override
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_cfg12_redis_required_explicit_override():
    # Dù ENVIRONMENT=development nhưng REDIS_REQUIRED=true → phải True
    s = _make_settings(REDIS_REQUIRED="true")
    assert s.redis_required is True

    # Dù ENVIRONMENT=development, REDIS_REQUIRED=false → False
    s2 = _make_settings(REDIS_REQUIRED="false")
    assert s2.redis_required is False
