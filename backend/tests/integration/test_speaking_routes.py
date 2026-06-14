import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from sqlalchemy import select

from app.db.models import History
from tests.integration.test_users_routes import authenticated_client

pytestmark = pytest.mark.integration


@patch("app.routers.speaking.has_openrouter_keys", return_value=True)
@patch("app.routers.speaking.chat_completion")
async def test_speaking_chat_success(mock_chat, mock_has_keys, authenticated_client):
    """Test speaking coach chat endpoint."""
    mock_chat.return_value = ("Hello, this is CatbotSpeaking.", "mock-model")
    
    payload = {
        "question_text": "Describe a book you read.",
        "user_message": "I read Harry Potter.",
        "history": []
    }
    response = await authenticated_client.post("/speaking/chat", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["reply"] == "Hello, this is CatbotSpeaking."


@patch("app.routers.speaking.OPENROUTER_KEY", "fake_key")
@patch("app.routers.speaking._call_language_cards")
async def test_analyze_language_success(mock_call_cards, authenticated_client):
    """Test vocabulary/grammar analysis from text transcript."""
    mock_call_cards.return_value = {
        "grammar_analysis": {
            "score": 6.5,
            "errors": [
                {
                    "text": "I loves coding.",
                    "error_type": "subject-verb agreement",
                    "correction": "I love coding.",
                    "explanation": "Subject I takes base form."
                }
            ]
        },
        "vocabulary_analysis": {
            "score": 7.0,
            "weak_words": [{"text": "coding", "reason": "repeated"}],
            "strong_words": [],
            "replacements": []
        }
    }

    payload = {
        "transcript": "I loves coding.",
        "question_text": "What do you like to do?"
    }
    response = await authenticated_client.post("/speaking/analyze-language", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["llm_generated"] is True
    assert "grammar_analysis" in data
    assert "vocabulary_analysis" in data
    assert data["grammar_analysis"]["score"] == 6.5


@patch("app.routers.speaking.evaluate_speaking_core")
@patch("app.routers.speaking.read_upload_limited")
async def test_evaluate_speaking_success(
    mock_read_upload, mock_eval_core, authenticated_client
):
    """Test uploading speaking audio and receiving evaluation."""
    mock_read_upload.return_value = b"fake_audio_bytes"
    mock_eval_core.return_value = {
        "overall_band": 7.0,
        "grammar_score": 6.5,
        "vocabulary_score": 7.0,
        "coherence_score": 7.0,
        "pronunciation_total": 7.5,
        "transcript": "Hello world.",
        "overall_comment": "Good job."
    }

    file_content = b"fake webm file"
    files = {
        "file": ("audio.webm", file_content, "audio/webm")
    }
    data = {
        "question_text": "Describe your hometown.",
        "persist_result": "false"
    }
    
    response = await authenticated_client.post("/speaking/evaluate", files=files, data=data)
    assert response.status_code == status.HTTP_200_OK
    res_json = response.json()
    assert res_json["overall_band"] == 7.0
    assert res_json["transcript"] == "Hello world."


async def test_speaking_attempt_summary_empty(authenticated_client):
    """Test getting attempt summary when no history exists."""
    response = await authenticated_client.get("/speaking/attempt-summary?quiz_id=999")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["average"] is None
    assert data["quiz_id"] == "999"


async def test_speaking_attempt_summary_with_data(authenticated_client, db_session):
    """Test retrieving speaking attempt summary from database history."""
    # Insert a speaking attempt history manually
    history = History(
        user_id=authenticated_client.user.id,
        quiz_id="101",
        subject="Speaking",
        score=7,
        total_questions=10,
        percentage=70.0,
        band_score=7.0,
        answers={
            "attempt_id": "attempt_xyz",
            "question_id": "q1",
            "question_text": "Hometown",
            "band_estimate": 7.0,
            "grammar_score": 7.0,
            "vocabulary_score": 7.0,
            "coherence_score": 7.0,
            "pronunciation_total": 7.0,
            "overall_comment": "Excellent"
        }
    )
    db_session.add(history)
    await db_session.commit()

    response = await authenticated_client.get("/speaking/attempt-summary?quiz_id=101&attempt_id=attempt_xyz")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["band_estimate"] == 7.0
    assert data["average"]["band_estimate"] == 7.0
