"""
tests/unit/core/test_auth_cookies.py
──────────────────────────────────────
Unit tests đầy đủ cho app/core/auth_cookies.py.

Mở rộng từ tests/test_auth_cookies.py (4 tests cũ → giữ nguyên + bổ sung).

Bao phủ:
  CK-01  attach_auth_cookies (httponly mode) → refresh trong cookie, không trong body
  CK-02  attach_auth_cookies (non-httponly mode) → cả 2 token trong body JSON
  CK-03  attach_auth_cookies → csrf_token cookie được set (httpOnly=false)
  CK-04  read_refresh_token → ưu tiên cookie hơn body
  CK-05  read_refresh_token → fallback body khi không có cookie
  CK-06  read_refresh_token → trả về None khi cả 2 đều None/rỗng
  CK-07  validate_csrf → GET request bỏ qua (không raise)
  CK-08  validate_csrf → HEAD, OPTIONS bỏ qua (không raise)
  CK-09  validate_csrf → POST /auth/login bỏ qua (exempt)
  CK-10  validate_csrf → POST /auth/refresh bỏ qua (exempt)
  CK-11  validate_csrf → POST với header = cookie → pass
  CK-12  validate_csrf → POST header ≠ cookie → 403
  CK-13  validate_csrf → POST không có header → 403
  CK-14  validate_csrf → POST không có cookie → 403
  CK-15  validate_csrf → disabled khi auth_httponly_refresh=False (bỏ qua hoàn toàn)
  CK-16  clear_auth_cookies → xóa cả 2 cookie
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.core.auth_cookies import (
    CSRF_COOKIE,
    CSRF_HEADER,
    REFRESH_COOKIE,
    attach_auth_cookies,
    clear_auth_cookies,
    read_refresh_token,
    validate_csrf,
)
from app.schemas import Token


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def httponly_settings(monkeypatch):
    """Giả lập chế độ httpOnly refresh + CSRF bật."""
    cfg = SimpleNamespace(
        auth_httponly_refresh=True,
        auth_cookie_secure=False,
        ENVIRONMENT="development",
        REFRESH_TOKEN_EXPIRE_DAYS=7,
    )
    monkeypatch.setattr("app.core.auth_cookies.settings", cfg)
    return cfg


@pytest.fixture
def plain_settings(monkeypatch):
    """Giả lập chế độ plain: refresh token trả về trong body."""
    cfg = SimpleNamespace(
        auth_httponly_refresh=False,
        auth_cookie_secure=False,
        ENVIRONMENT="development",
        REFRESH_TOKEN_EXPIRE_DAYS=7,
    )
    monkeypatch.setattr("app.core.auth_cookies.settings", cfg)
    return cfg


def _make_token(access="acc-token", refresh="ref-token"):
    return Token(access_token=access, refresh_token=refresh, token_type="bearer")


def _make_post_request(path: str, header_csrf: str | None, cookie_csrf: str | None):
    req = MagicMock()
    req.method = "POST"
    req.url.path = path
    req.headers = {CSRF_HEADER: header_csrf} if header_csrf else {}
    req.cookies = {CSRF_COOKIE: cookie_csrf} if cookie_csrf else {}
    return req


# ---------------------------------------------------------------------------
# CK-01: httponly mode → refresh ở cookie, không ở body
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck01_attach_cookies_httponly_mode_refresh_in_cookie(httponly_settings):
    resp = attach_auth_cookies(_make_token())
    body = json.loads(resp.body)

    assert body["access_token"] == "acc-token"
    assert body["refresh_token"] is None       # không để lộ refresh trong body

    cookie_blob = " ".join(resp.headers.getlist("set-cookie")).lower()
    assert REFRESH_COOKIE in cookie_blob
    assert "httponly" in cookie_blob


# ---------------------------------------------------------------------------
# CK-02: non-httponly mode → cả 2 token trong body
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck02_attach_cookies_plain_mode_tokens_in_body(plain_settings):
    resp = attach_auth_cookies(_make_token())
    body = json.loads(resp.body)

    assert body["access_token"] == "acc-token"
    assert body["refresh_token"] == "ref-token"   # có trong body


# ---------------------------------------------------------------------------
# CK-03: httponly mode → csrf_token cookie được set với httpOnly=false
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck03_csrf_cookie_is_readable_by_js(httponly_settings):
    resp = attach_auth_cookies(_make_token())
    raw_cookies = resp.headers.getlist("set-cookie")
    csrf_cookies = [c for c in raw_cookies if CSRF_COOKIE in c]

    assert csrf_cookies, "csrf_token cookie phải được set"
    # csrf_token phải KHÔNG có httponly (JS cần đọc được)
    for c in csrf_cookies:
        assert "httponly" not in c.lower()


# ---------------------------------------------------------------------------
# CK-04: read_refresh_token → ưu tiên cookie
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck04_read_refresh_prefers_cookie():
    req = MagicMock()
    req.cookies = {REFRESH_COOKIE: "from-cookie"}
    result = read_refresh_token(req, body_token="from-body")
    assert result == "from-cookie"


# ---------------------------------------------------------------------------
# CK-05: read_refresh_token → fallback về body khi không có cookie
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck05_read_refresh_fallback_to_body():
    req = MagicMock()
    req.cookies = {}
    result = read_refresh_token(req, body_token="from-body")
    assert result == "from-body"


# ---------------------------------------------------------------------------
# CK-06: read_refresh_token → None khi cả 2 đều không có
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck06_read_refresh_returns_none_when_both_missing():
    req = MagicMock()
    req.cookies = {}
    assert read_refresh_token(req, body_token=None) is None


# ---------------------------------------------------------------------------
# CK-07: validate_csrf → GET request bị bỏ qua
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck07_get_request_skips_csrf(httponly_settings):
    req = MagicMock()
    req.method = "GET"
    req.url.path = "/users/me"
    validate_csrf(req)   # không raise


# ---------------------------------------------------------------------------
# CK-08: validate_csrf → HEAD và OPTIONS bỏ qua
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("method", ["HEAD", "OPTIONS"])
def test_ck08_safe_methods_skip_csrf(httponly_settings, method):
    req = MagicMock()
    req.method = method
    req.url.path = "/some/path"
    validate_csrf(req)   # không raise


# ---------------------------------------------------------------------------
# CK-09: validate_csrf → POST /auth/login là exempt
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("path", [
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/logout",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/auth/google/callback",
    "/auth/verify-email",
    "/auth/resend-verification",
    "/health",
])
def test_ck09_exempt_paths_skip_csrf(httponly_settings, path):
    req = _make_post_request(path, header_csrf=None, cookie_csrf=None)
    validate_csrf(req)   # không raise


# ---------------------------------------------------------------------------
# CK-10: validate_csrf → sub-path của exempt cũng bỏ qua
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck10_exempt_subpath_skipped(httponly_settings):
    req = _make_post_request("/auth/google/callback", header_csrf=None, cookie_csrf=None)
    validate_csrf(req)   # không raise


# ---------------------------------------------------------------------------
# CK-11: validate_csrf → header == cookie → pass
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck11_matching_csrf_tokens_pass(httponly_settings):
    token = "csrf-valid-token-abc123"
    req = _make_post_request("/users/me/profile", header_csrf=token, cookie_csrf=token)
    validate_csrf(req)   # không raise


# ---------------------------------------------------------------------------
# CK-12: validate_csrf → header ≠ cookie → 403
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck12_mismatched_csrf_tokens_raise_403(httponly_settings):
    req = _make_post_request("/users/me", header_csrf="header-val", cookie_csrf="cookie-val")
    with pytest.raises(HTTPException) as exc:
        validate_csrf(req)
    assert exc.value.status_code == 403
    assert "CSRF" in exc.value.detail


# ---------------------------------------------------------------------------
# CK-13: validate_csrf → POST thiếu header → 403
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck13_missing_csrf_header_raises_403(httponly_settings):
    req = _make_post_request("/practice/submit", header_csrf=None, cookie_csrf="some-token")
    with pytest.raises(HTTPException) as exc:
        validate_csrf(req)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# CK-14: validate_csrf → POST thiếu cookie → 403
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck14_missing_csrf_cookie_raises_403(httponly_settings):
    req = _make_post_request("/practice/submit", header_csrf="some-token", cookie_csrf=None)
    with pytest.raises(HTTPException) as exc:
        validate_csrf(req)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# CK-15: validate_csrf bị tắt khi auth_httponly_refresh=False
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck15_csrf_skipped_when_httponly_disabled(plain_settings):
    # Ngay cả POST với token sai vẫn không raise khi mode tắt
    req = _make_post_request("/users/me", header_csrf="wrong", cookie_csrf="different")
    validate_csrf(req)   # không raise


# ---------------------------------------------------------------------------
# CK-16: clear_auth_cookies → xóa đúng tên cookie
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_ck16_clear_auth_cookies_deletes_both(httponly_settings):
    resp = JSONResponse(content={})
    clear_auth_cookies(resp)

    raw_cookies = resp.headers.getlist("set-cookie")
    cookie_blob = " ".join(raw_cookies).lower()

    # FastAPI/Starlette set Max-Age=0 hoặc expires past khi delete
    assert REFRESH_COOKIE in cookie_blob
    assert CSRF_COOKIE in cookie_blob
