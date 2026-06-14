import pytest
from fastapi import status
from sqlalchemy import select

from app.db.models import User, UserProfile
from tests.integration.test_users_routes import authenticated_client

pytestmark = pytest.mark.integration


@pytest.fixture
async def authenticated_admin_client(admin_client, make_profile, db_session):
    """Provide an authenticated admin client and ensure its user has a profile in the DB."""
    stmt = select(UserProfile).where(UserProfile.user_id == admin_client.user.id)
    res = await db_session.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        await make_profile(user_id=admin_client.user.id, full_name="Admin User")
        await db_session.commit()
    return admin_client


async def test_admin_access_control_forbidden_for_user(authenticated_client):
    """Ensure standard users cannot access admin endpoints."""
    endpoints = [
        ("GET", "/admin/overview"),
        ("GET", "/admin/users"),
        ("GET", "/admin/leaderboard"),
        ("GET", "/admin/leaderboard/anomalies"),
    ]
    for method, path in endpoints:
        if method == "GET":
            response = await authenticated_client.get(path)
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_admin_get_overview(authenticated_admin_client):
    """Test getting admin dashboard overview stats."""
    response = await authenticated_admin_client.get("/admin/overview")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "average_band_by_skill" in data


async def test_admin_list_users(authenticated_admin_client, make_user, make_profile, db_session):
    """Test listing users in the admin panel."""
    # Create another user to list
    other_user = await make_user(email="other_list@example.com")
    await make_profile(user_id=other_user.id, full_name="Other Listed User")
    await db_session.commit()

    response = await authenticated_admin_client.get("/admin/users")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 2  # Admin user + other user


async def test_admin_create_user(authenticated_admin_client, db_session):
    """Test creating a new user through the admin panel."""
    payload = {
        "email": "admincreated@example.com",
        "password": "Password123!",
        "full_name": "Created By Admin",
        "role": "user",
        "is_verified": True
    }
    response = await authenticated_admin_client.post("/admin/users", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "admincreated@example.com"
    assert data["role"] == "user"

    # Verify DB
    stmt = select(User).where(User.email == "admincreated@example.com")
    res = await db_session.execute(stmt)
    user = res.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is True


async def test_admin_get_user_detail(authenticated_admin_client, make_user, make_profile, db_session):
    """Test retrieving user details via admin endpoint."""
    user = await make_user(email="detail_target@example.com")
    await make_profile(user_id=user.id, full_name="Detail Target")
    await db_session.commit()

    response = await authenticated_admin_client.get(f"/admin/users/{user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "detail_target@example.com"
    assert data["full_name"] == "Detail Target"


async def test_admin_update_user_status(authenticated_admin_client, make_user, make_profile, db_session):
    """Test locking/unlocking user account."""
    user = await make_user(email="status_target@example.com")
    await make_profile(user_id=user.id, full_name="Status Target")
    await db_session.commit()

    # Lock user
    payload = {
        "is_active": False,
        "lock_reason": "Violation"
    }
    response = await authenticated_admin_client.patch(f"/admin/users/{user.id}/status", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is False
    assert data["lock_reason"] == "Violation"

    # Unlock user
    payload = {
        "is_active": True,
        "lock_reason": None
    }
    response = await authenticated_admin_client.patch(f"/admin/users/{user.id}/status", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is True
    assert data["lock_reason"] is None


async def test_admin_update_user_role(authenticated_admin_client, make_user, make_profile, db_session):
    """Test changing user role to admin."""
    user = await make_user(email="role_target@example.com", role="user")
    await make_profile(user_id=user.id, full_name="Role Target")
    await db_session.commit()

    payload = {"role": "admin"}
    response = await authenticated_admin_client.patch(f"/admin/users/{user.id}/role", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["role"] == "admin"


async def test_admin_reset_xp_streak(authenticated_admin_client, make_user, make_profile, db_session):
    """Test resetting user metrics."""
    user = await make_user(email="reset_target@example.com")
    profile = await make_profile(user_id=user.id, full_name="Reset Target")
    profile.xp = 500
    profile.streak = 10
    db_session.add(profile)
    await db_session.commit()

    payload = {
        "reset_xp": True,
        "reset_streak": True
    }
    response = await authenticated_admin_client.post(f"/admin/users/{user.id}/reset-xp-streak", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["xp"] == 0
    assert data["streak"] == 0


async def test_admin_leaderboard_endpoints(authenticated_admin_client):
    """Test fetching leaderboards and anomalies."""
    # Leaderboard
    response = await authenticated_admin_client.get("/admin/leaderboard")
    assert response.status_code == status.HTTP_200_OK
    assert "items" in response.json()

    # Anomalies
    response = await authenticated_admin_client.get("/admin/leaderboard/anomalies")
    assert response.status_code == status.HTTP_200_OK
    assert "items" in response.json()


async def test_admin_content_endpoints(authenticated_admin_client):
    """Test fetching list of mock tests and writing topics."""
    # Mock tests
    response = await authenticated_admin_client.get("/admin/content/mock-tests")
    assert response.status_code == status.HTTP_200_OK
    assert "items" in response.json()

    # Writing topics
    response = await authenticated_admin_client.get("/admin/content/writing-topics")
    assert response.status_code == status.HTTP_200_OK
    assert "items" in response.json()
