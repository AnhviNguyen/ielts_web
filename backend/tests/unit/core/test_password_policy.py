"""
tests/unit/core/test_password_policy.py
─────────────────────────────────────────
Unit tests cho app/core/password_policy.py — assert_password_strength.

Bao phủ:
  PWD-01  Password ≥10 ký tự, không phổ biến, không toàn số → pass
  PWD-02  Password < 10 ký tự → HTTP 400
  PWD-03  Password nằm trong blocklist ("password123") → HTTP 400
  PWD-04  Password toàn chữ số → HTTP 400
  PWD-05  Password đúng 10 ký tự → pass (biên dưới)
  PWD-06  Password có ký tự đặc biệt, đủ mạnh → pass
  PWD-07  Blocklist case-insensitive check ("PASSWORD123" lower nằm trong set)
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.password_policy import assert_password_strength


# ---------------------------------------------------------------------------
# PWD-01: Password hợp lệ — đủ dài, không phổ biến, không toàn số
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_pwd01_strong_password_passes():
    # Không raise exception
    assert_password_strength("MyStr0ngP@ss!")


# ---------------------------------------------------------------------------
# PWD-02: Password quá ngắn (< 10 ký tự) → HTTP 400
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("short_pwd", [
    "",          # rỗng
    "abc",       # 3 chars
    "Abc1234",   # 7 chars
    "Abc12345",  # 8 chars
    "Abc123456",  # 9 chars
])
def test_pwd02_short_password_raises_400(short_pwd):
    with pytest.raises(HTTPException) as exc:
        assert_password_strength(short_pwd)
    assert exc.value.status_code == 400
    assert "10" in exc.value.detail  # message đề cập đến độ dài


# ---------------------------------------------------------------------------
# PWD-03: Password nằm trong blocklist → HTTP 400
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("common_pwd", [
    "password",
    "password123",
    "123456789",
    "qwerty123",
    "admin123",
    "P@ssw0rd",       # có trong blocklist
    "P@ssword1",      # có trong blocklist
    "changeme",
])
def test_pwd03_common_password_raises_400(common_pwd):
    with pytest.raises(HTTPException) as exc:
        assert_password_strength(common_pwd)
    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# PWD-04: Password toàn chữ số → HTTP 400
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("digits_only", [
    # Chuỗi toàn số, đủ dài (≥10), không trong blocklist → chỉ bị chặn bởi isdigit() check
    "99887766554433",  # toàn số, không trong blocklist, dài đủ
    "11223344556677",  # toàn số, không trong blocklist
])
def test_pwd04_all_digits_password_raises_400(digits_only):
    with pytest.raises(HTTPException) as exc:
        assert_password_strength(digits_only)
    assert exc.value.status_code == 400



# ---------------------------------------------------------------------------
# PWD-05: Password đúng 10 ký tự → pass (edge case biên dưới)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_pwd05_exactly_10_chars_passes():
    # Không phổ biến, không toàn số
    assert_password_strength("abcdefghiJ")  # 10 chars


# ---------------------------------------------------------------------------
# PWD-06: Password có ký tự đặc biệt, rất mạnh → pass
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_pwd06_special_characters_passes():
    assert_password_strength("Tr@!nH@rdWork2026")


# ---------------------------------------------------------------------------
# PWD-07: Blocklist check case-insensitive (lower() match)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_pwd07_blocklist_is_case_insensitive():
    # "password" in blocklist; "PASSWORD123".lower() == "password123" ∈ blocklist
    with pytest.raises(HTTPException) as exc:
        assert_password_strength("PASSWORD123")
    assert exc.value.status_code == 400
