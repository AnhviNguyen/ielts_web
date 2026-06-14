import pytest
from fastapi import status
from sqlalchemy import select

from app.db.models import UserProfile, History, PracticeSession
from tests.integration.test_users_routes import authenticated_client

pytestmark = pytest.mark.integration


async def test_practice_reading_session_success(authenticated_client):
    """Test initializing a reading practice session."""
    response = await authenticated_client.get("/practice/reading/session")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "session_id" in data
    assert data["subject"] == "reading"
    assert "quiz" in data


async def test_practice_listening_session_success(authenticated_client):
    """Test initializing a listening practice session."""
    response = await authenticated_client.get("/practice/listening/session")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "session_id" in data
    assert data["subject"] == "listening"
    assert "quiz" in data


async def test_practice_submit_reading(authenticated_client, db_session):
    """Test submitting a reading practice session answer sheet."""
    # 1. Create session
    resp_sess = await authenticated_client.get("/practice/reading/session")
    assert resp_sess.status_code == status.HTTP_200_OK
    sess_data = resp_sess.json()
    session_id = sess_data["session_id"]
    quiz = sess_data["quiz"]
    
    # 2. Extract first question ID
    q_id = None
    for part in quiz.get("parts", []):
        for qset in part.get("question_sets", []):
            for q in qset.get("questions", []):
                q_id = q.get("id")
                break
            if q_id:
                break
        if q_id:
            break

    # 3. Submit
    answers = {}
    if q_id:
        answers[str(q_id)] = "mocked_answer"

    payload = {
        "session_id": session_id,
        "answers": answers,
        "duration_seconds": 120
    }
    response = await authenticated_client.post("/practice/reading/submit", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["session_id"] == session_id
    assert "score" in data
    assert "estimated_band" in data

    # 4. Verify DB
    stmt = select(PracticeSession).where(PracticeSession.id == session_id)
    res = await db_session.execute(stmt)
    sess_db = res.scalar_one()
    assert sess_db.status == "submitted"


async def test_practice_submit_listening(authenticated_client, db_session):
    """Test submitting a listening practice session answer sheet."""
    # 1. Create session
    resp_sess = await authenticated_client.get("/practice/listening/session")
    sess_data = resp_sess.json()
    session_id = sess_data["session_id"]
    quiz = sess_data["quiz"]
    
    # 2. Extract first question ID
    q_id = None
    for part in quiz.get("parts", []):
        for qset in part.get("question_sets", []):
            for q in qset.get("questions", []):
                q_id = q.get("id")
                break
            if q_id:
                break
        if q_id:
            break

    # 3. Submit
    answers = {}
    if q_id:
        answers[str(q_id)] = "mocked_answer"

    payload = {
        "session_id": session_id,
        "answers": answers,
        "duration_seconds": 150
    }
    response = await authenticated_client.post("/practice/listening/submit", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["session_id"] == session_id
    assert "score" in data


async def test_practice_check_answer(authenticated_client):
    """Test checking a single answer dynamically."""
    # 1. Create session
    resp_sess = await authenticated_client.get("/practice/reading/session")
    sess_data = resp_sess.json()
    session_id = sess_data["session_id"]
    quiz = sess_data["quiz"]

    # 2. Extract first question ID
    q_id = None
    for part in quiz.get("parts", []):
        for qset in part.get("question_sets", []):
            for q in qset.get("questions", []):
                q_id = q.get("id")
                break
            if q_id:
                break
        if q_id:
            break

    assert q_id is not None, "Quiz has no questions"

    payload = {
        "session_id": session_id,
        "question_id": q_id,
        "user_answer": "random_guess"
    }
    response = await authenticated_client.post("/practice/check-answer", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "is_correct" in data
    assert "correct_answer" in data or "correct_answers" in data
