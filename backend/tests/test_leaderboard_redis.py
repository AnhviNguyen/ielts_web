"""Unit tests for Redis ZSET leaderboard helpers (no live Redis required)."""

from unittest.mock import patch

from app.core.leaderboard_redis import (
    XP_ZSET_KEY,
    get_rank,
    get_top,
    sync_user_xp,
    zset_size,
)


@patch("app.core.leaderboard_redis.cache")
def test_sync_user_xp(mock_cache):
    sync_user_xp(42, 150)
    mock_cache.zadd.assert_called_once_with(XP_ZSET_KEY, {"42": 150.0})


@patch("app.core.leaderboard_redis.cache")
def test_get_top(mock_cache):
    mock_cache.zrevrange_with_scores.return_value = [("1", 500.0), ("2", 300.0)]
    assert get_top(10) == [(1, 500), (2, 300)]


@patch("app.core.leaderboard_redis.cache")
def test_get_rank(mock_cache):
    mock_cache.zrevrank.return_value = 4
    assert get_rank(7) == 5


@patch("app.core.leaderboard_redis.cache")
def test_zset_size(mock_cache):
    mock_cache.zcard.return_value = 12
    assert zset_size() == 12
