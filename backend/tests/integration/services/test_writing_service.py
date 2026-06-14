"""
tests/integration/services/test_writing_service.py
────────────────────────────────────────────────────
Integration tests for WritingService.
Verifies essay evaluation, validation, fallback handling, and daily count tracking.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import User, History, UserProfile
from app.services.writing_service import WritingService
from app.schemas import WritingSubmitRequest

pytestmark = pytest.mark.integration


@pytest.fixture
def writing_service(db_session):
    return WritingService(db_session)


@pytest.fixture
def mock_ai_response():
    return {
        "overall_band": 7.5,
        "task_achievement": 7.5,
        "coherence_cohesion": 8.0,
        "lexical_resource": 7.0,
        "grammar_accuracy": 7.5,
        "word_count_comment": "Excellent length.",
        "strengths": ["Clear introduction", "Good structure"],
        "improvements": ["Vary your sentence structure a bit more"],
        "summary": "Great essay.",
        "grammar": {
            "band": 7.5,
            "errors": [{"original": "they is", "correction": "they are", "rule": "subject-verb agreement", "severity": "major"}],
            "tips": ["Pay attention to verb forms"]
        },
        "vocabulary": {
            "band": 7.0,
            "weak_words": [{"word": "bad", "better": "detrimental", "reason": "more formal"}],
            "upgrades": ["detrimental"],
            "tips": ["Use academic synonyms"]
        },
        "paragraph_allocation": {
            "structure_ok": True,
            "sections": [
                {"name": "Introduction", "recommended_words": "50", "your_words": 45, "feedback": "Good intro"},
                {"name": "Body 1", "recommended_words": "100", "your_words": 110, "feedback": "Excellent body paragraphs"}
            ],
            "tips": ["Keep sections balanced"]
        },
        "model_paragraph": {
            "focus": "Body 1",
            "weak_excerpt": "this was bad.",
            "improved_text": "this was detrimental.",
            "explanation": "upgraded adjective.",
            "expected_band_gain": "+0.5"
        }
    }


# ---------------------------------------------------------------------------
# WS-01: Submit with AI Evaluator (Happy Path)
# ---------------------------------------------------------------------------

@patch("app.services.writing_service.has_openrouter_keys", return_value=True)
@patch("app.services.writing_service.chat_completion_json")
async def test_ws01_submit_happy_path_with_ai(
    mock_chat, mock_has_keys, mock_ai_response, writing_service, db_session, make_user
):
    """
    WS-01: Submit writing with AI evaluation -> saves history, increments count, returns bands.
    """
    user = await make_user(email="writing_student@example.com")
    mock_chat.return_value = (mock_ai_response, "mock-model")

    # Essay must be >= 20 words
    essay_text = " ".join(["hello"] * 25)
    payload = WritingSubmitRequest(
        topic_id=101,
        task_type=2,
        essay_text=essay_text,
        word_count=25,
        duration_seconds=600,
        prompt_text="Discuss the pros and cons of coding.",
    )

    resp = await writing_service.submit(user, payload)
    assert resp.band_score == 7.5
    assert resp.xp_earned > 0
    assert resp.evaluation["overall_band"] == 7.5
    assert resp.evaluation["llm_generated"] is True

    # Check history saved
    stmt = select(History).where(History.id == resp.history_id)
    res = await db_session.execute(stmt)
    history_row = res.scalar_one_or_none()
    assert history_row is not None
    assert history_row.user_id == user.id
    assert history_row.band_score == 7.5
    assert history_row.answers["essay_text"] == essay_text

    # Check daily counter incremented
    stmt_profile = select(UserProfile).where(UserProfile.user_id == user.id)
    res_profile = await db_session.execute(stmt_profile)
    profile = res_profile.scalar_one()
    assert profile.daily_writing_used == 1


# ---------------------------------------------------------------------------
# WS-02: Submit short essay
# ---------------------------------------------------------------------------

async def test_ws02_submit_too_short_raises_400(writing_service, make_user):
    """
    WS-02: Submit writing < 20 words -> Raise 400.
    """
    user = await make_user(email="short_essay@example.com")
    payload = WritingSubmitRequest(
        topic_id=102,
        task_type=1,
        essay_text="This is a short essay.",
        word_count=5,
        duration_seconds=100,
    )

    with pytest.raises(HTTPException) as exc_info:
        await writing_service.submit(user, payload)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Bài viết quá ngắn" in exc_info.value.detail


# ---------------------------------------------------------------------------
# WS-03: Fallback when AI keys are missing
# ---------------------------------------------------------------------------

@patch("app.services.writing_service.has_openrouter_keys", return_value=False)
async def test_ws03_submit_fallback_path(mock_has_keys, writing_service, db_session, make_user):
    """
    WS-03: AI keys missing -> fallback to rule-based evaluation.
    """
    user = await make_user(email="fallback_student@example.com")
    essay_text = " ".join(["apple"] * 160)
    payload = WritingSubmitRequest(
        topic_id=103,
        task_type=1,
        essay_text=essay_text,
        word_count=160,
        duration_seconds=300,
    )

    resp = await writing_service.submit(user, payload)
    assert resp.band_score > 0
    assert resp.evaluation["llm_generated"] is False
    assert "Chấm điểm ước lượng" in resp.evaluation["summary"]


# ---------------------------------------------------------------------------
# WS-04: Daily limit increment behavior
# ---------------------------------------------------------------------------

@patch("app.services.writing_service.has_openrouter_keys", return_value=False)
async def test_ws04_daily_writing_used_incremented(mock_has_keys, writing_service, db_session, make_user):
    """
    WS-04: Multiple submissions increment the counter correctly.
    """
    user = await make_user(email="multiple_submissions@example.com")
    essay_text = " ".join(["hello"] * 30)
    payload = WritingSubmitRequest(
        topic_id=104,
        task_type=2,
        essay_text=essay_text,
        word_count=30,
        duration_seconds=120,
    )

    await writing_service.submit(user, payload)
    await writing_service.submit(user, payload)

    stmt_profile = select(UserProfile).where(UserProfile.user_id == user.id)
    res_profile = await db_session.execute(stmt_profile)
    profile = res_profile.scalar_one()
    assert profile.daily_writing_used == 2


# ---------------------------------------------------------------------------
# WS-05: Get result
# ---------------------------------------------------------------------------

@patch("app.services.writing_service.has_openrouter_keys", return_value=False)
async def test_ws05_get_result(mock_has_keys, writing_service, make_user):
    """
    WS-05: Retrieve results successfully, or raises 404 for incorrect id/subject.
    """
    user = await make_user(email="retrieve@example.com")
    essay_text = " ".join(["hello"] * 30)
    payload = WritingSubmitRequest(
        topic_id=105,
        task_type=2,
        essay_text=essay_text,
        word_count=30,
        duration_seconds=120,
    )

    resp = await writing_service.submit(user, payload)

    # 1. Retrieve successfully
    result = await writing_service.get_result(user, resp.history_id)
    assert result["history_id"] == resp.history_id
    assert result["essay_text"] == essay_text

    # 2. Nonexistent history id raises 404
    with pytest.raises(HTTPException) as exc_info:
        await writing_service.get_result(user, 99999)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    # 3. Access by different user raises 404 (isolation check)
    another_user = await make_user(email="another_retrieve@example.com")
    with pytest.raises(HTTPException) as exc_info:
        await writing_service.get_result(another_user, resp.history_id)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
