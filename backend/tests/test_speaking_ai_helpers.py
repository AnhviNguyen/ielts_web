"""Tests for speaking AI JSON parsing."""

from app.services.speaking_ai_helpers import _parse_ai_json, _safe_score_0_9


def test_parse_ai_json_strips_markdown_fence():
    raw = '```json\n{"grammar_score": 6.5, "vocabulary_score": 7}\n```'
    data = _parse_ai_json(raw)
    assert data["grammar_score"] == 6.5


def test_safe_score_clamps():
    assert _safe_score_0_9(12) == 9.0
    assert _safe_score_0_9(-1) == 0.0
    assert _safe_score_0_9("6.5") == 6.5
