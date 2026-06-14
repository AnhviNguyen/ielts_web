"""
tests/unit/core/test_rate_limit.py
────────────────────────────────────
Unit tests cho app/core/rate_limit.py — _client_ip key function.

Lưu ý: slowapi/rate_limit middleware test thực sự cần integration test với
HTTP client. Tầng này chỉ test hàm _client_ip thuần.

Bao phủ:
  RL-01  IP trực tiếp (không qua proxy) → trả về IP đó
  RL-02  Từ private/proxy network + X-Forwarded-For → trả về forwarded IP
  RL-03  X-Forwarded-For có nhiều IP (chain) → lấy IP đầu tiên
  RL-04  X-Forwarded-For không hợp lệ (string rác) → fallback về peer IP
  RL-05  Không có client host → trả về "unknown"
  RL-06  Peer IP hợp lệ nhưng không phải trusted proxy → bỏ qua X-Forwarded-For
  RL-07  rate_limit_exceeded_handler trả về 429 JSON
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# Import private function cần test
from app.core.rate_limit import _client_ip, rate_limit_exceeded_handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(peer_ip: str | None, forwarded_for: str | None = None):
    """Tạo mock Request với peer IP và header tùy chọn."""
    req = MagicMock()
    if peer_ip is None:
        req.client = None
    else:
        req.client = MagicMock()
        req.client.host = peer_ip

    headers = {}
    if forwarded_for is not None:
        headers["x-forwarded-for"] = forwarded_for
    req.headers = headers
    return req


# ---------------------------------------------------------------------------
# RL-01: Peer IP công khai → trả về IP đó (không dùng X-Forwarded-For)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_rl01_public_peer_ip_returned_directly():
    req = _make_request("203.0.113.1", forwarded_for="10.0.0.5")
    ip = _client_ip(req)
    # 203.0.113.1 không phải private → không tin X-Forwarded-For
    assert ip == "203.0.113.1"


# ---------------------------------------------------------------------------
# RL-02: Peer từ mạng nội bộ + X-Forwarded-For → lấy IP forwarded
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.parametrize("private_peer", [
    "127.0.0.1",
    "10.0.0.1",
    "172.16.0.1",
    "192.168.1.100",
])
def test_rl02_trusted_proxy_uses_forwarded_for(private_peer):
    req = _make_request(private_peer, forwarded_for="203.0.113.42")
    ip = _client_ip(req)
    assert ip == "203.0.113.42"


# ---------------------------------------------------------------------------
# RL-03: X-Forwarded-For chuỗi nhiều IP → lấy IP đầu tiên
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_rl03_forwarded_for_chain_takes_first():
    req = _make_request("127.0.0.1", forwarded_for="1.2.3.4, 5.6.7.8, 9.10.11.12")
    ip = _client_ip(req)
    assert ip == "1.2.3.4"


# ---------------------------------------------------------------------------
# RL-04: X-Forwarded-For không hợp lệ → fallback về peer IP
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_rl04_invalid_forwarded_for_falls_back_to_peer():
    req = _make_request("10.0.0.1", forwarded_for="not-a-valid-ip")
    ip = _client_ip(req)
    # fallback về peer
    assert ip == "10.0.0.1"


# ---------------------------------------------------------------------------
# RL-05: Không có client → trả về "unknown"
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_rl05_no_client_returns_unknown():
    req = _make_request(peer_ip=None)
    ip = _client_ip(req)
    assert ip == "unknown"


# ---------------------------------------------------------------------------
# RL-06: Peer công khai → X-Forwarded-For bị bỏ qua (không trust)
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_rl06_public_peer_ignores_forwarded_for():
    req = _make_request("8.8.8.8", forwarded_for="192.168.1.1")
    ip = _client_ip(req)
    # 8.8.8.8 không nằm trong trusted range → dùng peer, không dùng X-Forwarded-For
    assert ip == "8.8.8.8"


# ---------------------------------------------------------------------------
# RL-07: rate_limit_exceeded_handler trả về 429 + JSON đúng format
# ---------------------------------------------------------------------------
@pytest.mark.unit
@pytest.mark.asyncio
async def test_rl07_rate_limit_exceeded_handler_returns_429():
    req = MagicMock()
    exc = MagicMock()   # RateLimitExceeded mock

    response = await rate_limit_exceeded_handler(req, exc)

    assert response.status_code == 429
    import json
    body = json.loads(response.body)
    assert "detail" in body
