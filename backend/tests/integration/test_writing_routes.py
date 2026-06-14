import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from sqlalchemy import select

from app.db.models import History
from tests.integration.test_users_routes import authenticated_client

pytestmark = pytest.mark.integration


async def test_list_writing_topics_success(authenticated_client):
    """Test getting published writing topics list."""
    response = await authenticated_client.get("/writing/topics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == 0
    assert "items" in data["data"]


async def test_get_writing_topic_success(authenticated_client):
    """Test retrieving writing topic detail."""
    # 1. Fetch list of topics
    list_response = await authenticated_client.get("/writing/topics")
    assert list_response.status_code == status.HTTP_200_OK
    list_data = list_response.json()
    items = list_data["data"]["items"]
    assert len(items) > 0, "No writing topics found in mock data"
    first_topic_id = items[0]["id"]

    # 2. Get details for the first topic
    response = await authenticated_client.get(f"/writing/topics/{first_topic_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["code"] == 0
    assert data["data"] is not None


@patch("app.routers.writing.has_openrouter_keys", return_value=True)
@patch("app.routers.writing.chat_completion")
async def test_writing_chat_success(mock_chat, mock_has_keys, authenticated_client):
    """Test writing coach chat endpoint."""
    mock_chat.return_value = ("Hello, this is CatbotWriting.", "mock-model")

    payload = {
        "prompt_text": "Write about technology.",
        "user_message": "How to structure intro?",
        "history": []
    }
    response = await authenticated_client.post("/writing/chat", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["reply"] == "Hello, this is CatbotWriting."


@patch("app.services.writing_service.has_openrouter_keys", return_value=True)
@patch("app.services.writing_service.chat_completion_json")
async def test_submit_writing_essay_success(
    mock_chat_json, mock_has_keys, authenticated_client, db_session
):
    """Test submitting a writing essay response."""
    mock_chat_json.return_value = (
        {
            "overall_band": 7.0,
            "task_achievement": 7.0,
            "coherence_cohesion": 7.0,
            "lexical_resource": 7.0,
            "grammar_accuracy": 7.0,
            "word_count_comment": "Perfect length.",
            "strengths": ["Clear essay structure"],
            "improvements": ["Enhance vocabulary choice"],
            "summary": "Solid essay.",
            "grammar": {"band": 7.0, "errors": [], "tips": []},
            "vocabulary": {"band": 7.0, "weak_words": [], "upgrades": [], "tips": []},
            "paragraph_allocation": {"structure_ok": True, "sections": [], "tips": []},
            "model_paragraph": {
                "focus": "Body 1",
                "weak_excerpt": "...",
                "improved_text": "...",
                "explanation": "...",
                "expected_band_gain": "+0.5"
            }
        },
        "mock-model"
    )

    # Fetch valid topic ID
    list_response = await authenticated_client.get("/writing/topics")
    list_data = list_response.json()
    first_topic_id = list_data["data"]["items"][0]["id"]

    # Essay word count must be >= 20 words
    essay_text = " ".join(["hello"] * 30)
    payload = {
        "topic_id": first_topic_id,
        "task_type": 2,
        "essay_text": essay_text,
        "word_count": 30,
        "duration_seconds": 600,
        "prompt_text": "Some writing prompt"
    }

    response = await authenticated_client.post("/writing/submit", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["band_score"] == 7.0
    assert "history_id" in data
    assert "evaluation" in data

    # Retrieve result using the history id
    history_id = data["history_id"]
    res_response = await authenticated_client.get(f"/writing/result/{history_id}")
    assert res_response.status_code == status.HTTP_200_OK
    assert res_response.json()["essay_text"] == essay_text
