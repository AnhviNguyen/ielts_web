"""Auth cookie + CSRF helpers."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.auth_cookies import attach_auth_cookies, read_refresh_token, validate_csrf
from app.schemas import Token


@pytest.fixture
def cookie_settings(monkeypatch):
    cfg = SimpleNamespace(
        auth_httponly_refresh=True,
        auth_cookie_secure=False,
        ENVIRONMENT="development",
        REFRESH_TOKEN_EXPIRE_DAYS=7,
        csrf_trusted_origins=frozenset({"http://localhost:5173"}),
    )
    monkeypatch.setattr("app.core.auth_cookies.settings", cfg)
    return cfg


def test_attach_auth_cookies_omits_refresh_in_body(cookie_settings):
    token = Token(access_token="acc", refresh_token="ref", token_type="bearer")
    response = attach_auth_cookies(token)
    import json

    body = json.loads(response.body)
    assert body["access_token"] == "acc"
    assert body["refresh_token"] is None
    cookie_headers = response.headers.getlist("set-cookie")
    cookie_blob = " ".join(cookie_headers).lower()
    assert "refresh_token" in cookie_blob
    assert "csrf_token" in cookie_blob


def test_read_refresh_token_prefers_cookie():
    request = MagicMock()
    request.cookies = {"refresh_token": "from-cookie"}
    assert read_refresh_token(request, "from-body") == "from-cookie"


def test_validate_csrf_rejects_mismatch(cookie_settings):
    request = MagicMock()
    request.method = "POST"
    request.url.path = "/users/me"
    request.headers = {"X-CSRF-Token": "abc"}
    request.cookies = {"csrf_token": "xyz"}
    with pytest.raises(HTTPException) as exc:
        validate_csrf(request)
    assert exc.value.status_code == 403


def test_validate_csrf_allows_exempt_login(cookie_settings):
    request = MagicMock()
    request.method = "POST"
    request.url.path = "/auth/login"
    request.headers = {}
    request.cookies = {}
    validate_csrf(request)


def test_validate_csrf_allows_trusted_origin_without_token(cookie_settings):
    request = MagicMock()
    request.method = "POST"
    request.url.path = "/users/me"
    request.headers = {"origin": "http://localhost:5173"}
    request.cookies = {}
    validate_csrf(request)


def test_validate_csrf_allows_trusted_referer_without_token(cookie_settings):
    request = MagicMock()
    request.method = "PUT"
    request.url.path = "/users/me"
    request.headers = {"referer": "http://localhost:5173/profile"}
    request.cookies = {}
    validate_csrf(request)


def test_validate_csrf_rejects_untrusted_origin_without_token(cookie_settings):
    request = MagicMock()
    request.method = "POST"
    request.url.path = "/users/me"
    request.headers = {"origin": "https://evil.example"}
    request.cookies = {}
    with pytest.raises(HTTPException) as exc:
        validate_csrf(request)
    assert exc.value.status_code == 403
