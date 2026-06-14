"""
tests/unit/core/test_security.py
─────────────────────────────────
Unit tests cho app/core/security.py — JWT, password hashing, token helpers.

Mở rộng từ tests/test_security.py (chỉ có 1 test).

Bao phủ:
  SEC-01  hash_password + verify_password → thành công
  SEC-02  verify_password sai password → False
  SEC-03  create_access_token → decode được sub và type
  SEC-04  create_access_token → token hết hạn ngay lập tức → decode_access_token = None
  SEC-05  Token bị giả mạo (sai signature) → decode_access_token = None
  SEC-06  create_refresh_token → type == "refresh", decode_token trả về payload
  SEC-07  decode_access_token trả về None nếu type != "access"
  SEC-08  hash_token trả về SHA-256 hex string nhất quán
  SEC-09  hash_token khác nhau với input khác nhau
  SEC-10  verify_password với hash corrupt không raise exception, trả về False
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


# ---------------------------------------------------------------------------
# SEC-01: hash + verify thành công
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec01_hash_and_verify_success():
    plain = "MyStr0ngP@ssword!"
    hashed = hash_password(plain)
    assert hashed != plain          # phải được hash
    assert verify_password(plain, hashed) is True


# ---------------------------------------------------------------------------
# SEC-02: verify_password sai password → False
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec02_verify_wrong_password_returns_false():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


# ---------------------------------------------------------------------------
# SEC-03: create_access_token → decode được sub và type chính xác
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec03_access_token_contains_correct_claims():
    user_id = 42
    token = create_access_token(subject=user_id)
    sub = decode_access_token(token)
    assert sub == str(user_id)

    # Kiểm tra type claim qua decode_token
    payload = decode_token(token)
    assert payload is not None
    assert payload["type"] == "access"
    assert payload["sub"] == str(user_id)


# ---------------------------------------------------------------------------
# SEC-04: Token hết hạn ngay lập tức → decode_access_token trả về None
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec04_expired_access_token_returns_none():
    token = create_access_token(
        subject=1,
        expires_delta=timedelta(seconds=-1),  # đã hết hạn
    )
    assert decode_access_token(token) is None


# ---------------------------------------------------------------------------
# SEC-05: Token bị giả mạo (sai signature) → decode trả về None
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec05_tampered_token_returns_none():
    token = create_access_token(subject=99)
    # Giả mạo bằng cách thay ký tự cuối
    tampered = token[:-4] + "XXXX"
    assert decode_access_token(tampered) is None


# ---------------------------------------------------------------------------
# SEC-06: create_refresh_token → type == "refresh"
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec06_refresh_token_has_correct_type():
    token = create_refresh_token(subject=7)
    payload = decode_token(token)
    assert payload is not None
    assert payload["type"] == "refresh"
    assert payload["sub"] == "7"


# ---------------------------------------------------------------------------
# SEC-07: decode_access_token trả về None nếu type != "access"
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec07_refresh_token_rejected_by_decode_access_token():
    refresh_token = create_refresh_token(subject=5)
    # decode_access_token phải từ chối token có type="refresh"
    result = decode_access_token(refresh_token)
    assert result is None


# ---------------------------------------------------------------------------
# SEC-08: hash_token trả về SHA-256 hex string nhất quán
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec08_hash_token_is_deterministic():
    raw = "some-random-refresh-token-string"
    h1 = hash_token(raw)
    h2 = hash_token(raw)
    assert h1 == h2
    assert len(h1) == 64        # SHA-256 → 64 hex chars
    assert h1.isalnum()         # chỉ có hex chars


# ---------------------------------------------------------------------------
# SEC-09: hash_token khác nhau với input khác nhau
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec09_different_inputs_give_different_hashes():
    h1 = hash_token("token-abc")
    h2 = hash_token("token-xyz")
    assert h1 != h2


# ---------------------------------------------------------------------------
# SEC-10: verify_password với hash corrupt không raise exception
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec10_corrupt_hash_does_not_raise():
    result = verify_password("any-password", "not-a-valid-hash-string")
    assert result is False


# ---------------------------------------------------------------------------
# SEC-11: create_access_token với subject là string
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec11_access_token_with_string_subject():
    token = create_access_token(subject="user-uuid-abc123")
    sub = decode_access_token(token)
    assert sub == "user-uuid-abc123"


# ---------------------------------------------------------------------------
# SEC-12: decode_token với string rỗng → None (không crash)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_sec12_decode_empty_string_returns_none():
    assert decode_token("") is None
    assert decode_access_token("") is None
