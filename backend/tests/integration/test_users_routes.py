import pytest
import io
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from sqlalchemy import select
from datetime import date, timezone, datetime

from app.db.models import User, UserProfile, Notification, StudyPlanTask
from app.core.security import hash_password

pytestmark = pytest.mark.integration


@pytest.fixture
async def authenticated_client(auth_client, make_profile, db_session):
    """Provide an authenticated client and ensure its user has a profile in the DB."""
    stmt = select(UserProfile).where(UserProfile.user_id == auth_client.user.id)
    res = await db_session.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        await make_profile(user_id=auth_client.user.id, full_name="Authenticated User")
        await db_session.commit()
    return auth_client


async def test_get_me_authenticated(authenticated_client):
    """Test GET /users/me with valid bearer token."""
    response = await authenticated_client.get("/users/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "authuser@example.com"
    assert data["role"] == "user"


async def test_get_me_unauthenticated(client):
    """Test GET /users/me without credentials returns 401."""
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_patch_me(authenticated_client, db_session):
    """Test updating user profile fields via PATCH /users/me."""
    payload = {
        "full_name": "Updated User Name",
        "bio": "New Bio Text",
        "target_band": 8.5,
    }
    response = await authenticated_client.patch("/users/me", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated User Name"
    assert data["bio"] == "New Bio Text"
    assert data["target_band"] == 8.5

    # Verify DB
    stmt = select(UserProfile).where(UserProfile.user_id == authenticated_client.user.id)
    res = await db_session.execute(stmt)
    profile = res.scalar_one()
    assert profile.full_name == "Updated User Name"


async def test_change_password_success(authenticated_client, db_session):
    """Test changing user password successfully."""
    authenticated_client.user.password_hash = hash_password("OldPassword123!")
    db_session.add(authenticated_client.user)
    await db_session.commit()

    payload = {
        "current_password": "OldPassword123!",
        "new_password": "NewPassword555!",
    }
    response = await authenticated_client.post("/users/me/change-password", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert "đổi mật khẩu thành công" in response.json()["message"]


async def test_change_password_incorrect_current(authenticated_client, db_session):
    """Test changing password fails when current password is wrong."""
    authenticated_client.user.password_hash = hash_password("OldPassword123!")
    db_session.add(authenticated_client.user)
    await db_session.commit()

    payload = {
        "current_password": "WrongOldPassword!",
        "new_password": "NewPassword555!",
    }
    response = await authenticated_client.post("/users/me/change-password", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("app.core.upload.validate_and_read_image")
@patch("app.core.storage.get_storage")
async def test_upload_avatar_success(mock_storage_getter, mock_validate_image, authenticated_client, db_session):
    """Test uploading an avatar image file."""
    mock_validate_image.return_value = (b"fake_image_bytes", "avatar.jpg")
    
    mock_storage = MagicMock()
    mock_storage.put_bytes.return_value = "http://test-storage/avatars/avatar.jpg"
    mock_storage_getter.return_value = mock_storage

    file_content = b"fake image content"
    files = {"file": ("avatar.jpg", file_content, "image/jpeg")}
    
    response = await authenticated_client.put("/users/me/avatar", files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Avatar uploaded successfully"

    # Verify DB profile updated
    stmt = select(UserProfile).where(UserProfile.user_id == authenticated_client.user.id)
    res = await db_session.execute(stmt)
    profile = res.scalar_one()
    assert profile.avatar_url == "http://test-storage/avatars/avatar.jpg"


async def test_activity_ping(authenticated_client):
    """Test pinging user activity updates streak."""
    response = await authenticated_client.post("/users/me/activity-ping")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "streak" in data


async def test_get_streak(authenticated_client):
    """Test fetching user activity streak."""
    response = await authenticated_client.get("/users/me/streak")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "streak" in data
    assert "longest_streak" in data


async def test_get_me_progress(authenticated_client):
    """Test fetching user skill progress stats."""
    response = await authenticated_client.get("/users/me/progress")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


async def test_get_me_stats(authenticated_client):
    """Test GET /users/me/stats."""
    response = await authenticated_client.get("/users/me/stats")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "streak" in data
    assert "xp" in data


async def test_get_badges(authenticated_client):
    """Test fetching user profile badges."""
    response = await authenticated_client.get("/users/me/badges")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "unlocked_count" in data


async def test_get_skill_radar(authenticated_client):
    """Test radar analytics."""
    response = await authenticated_client.get("/users/me/skill-radar")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "reading" in data
    assert "listening" in data


async def test_get_study_plan(authenticated_client):
    """Test study plan fetch."""
    response = await authenticated_client.get("/users/me/study-plan")
    assert response.status_code == status.HTTP_200_OK


async def test_notifications_endpoints(authenticated_client, db_session):
    """Test fetching list, reading and setting notifications."""
    notif = Notification(
        user_id=authenticated_client.user.id,
        type="test_alert",
        title="Hi",
        body="Hello World",
        is_read=False
    )
    db_session.add(notif)
    await db_session.commit()

    # List
    response = await authenticated_client.get("/users/me/notifications")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["items"]) >= 1

    # Read specific
    response = await authenticated_client.patch(f"/users/me/notifications/{notif.id}/read")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_read"] is True

    # Read all
    response = await authenticated_client.post("/users/me/notifications/read-all")
    assert response.status_code == status.HTTP_200_OK

    # Settings
    response = await authenticated_client.get("/users/me/notifications/settings")
    assert response.status_code == status.HTTP_200_OK


async def test_study_plan_generation(authenticated_client):
    """Test trigger generation of study plan."""
    response = await authenticated_client.post("/users/me/study-plan/generate")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "days" in data


@patch("app.routers.users.has_openrouter_keys", return_value=True)
@patch("app.routers.users.chat_completion")
async def test_dashboard_chat_success(mock_chat, mock_has_keys, authenticated_client):
    """Test chatbot coach response on dashboard."""
    mock_chat.return_value = ("Hello student, I am Catbot your coach.", "mock-gpt-model")

    payload = {
        "user_message": "Tell me my daily task",
        "history": []
    }
    response = await authenticated_client.post("/users/me/chat", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["reply"] == "Hello student, I am Catbot your coach."
