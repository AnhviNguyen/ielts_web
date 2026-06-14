"""
tests/integration/db/test_models_cascade.py
─────────────────────────────────────────────
Integration tests for SQLAlchemy ORM models, constraints, and cascade delete rules (DB-01 to DB-06).
Runs against the PostgreSQL test database to verify real database constraints.
"""

import pytest
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.db.models import (
    User,
    UserProfile,
    Progress,
    History,
    RefreshToken,
    ShadowingUserHistory,
    ScoreHistory,
)

pytestmark = pytest.mark.integration


async def test_db01_create_user_with_profile_relationship(db_session):
    """
    DB-01: Tạo User -> UserProfile tự động lưu qua relationship.
    """
    user = User(
        email="cascade_relationship@example.com",
        password_hash="some_hash",
        role="user",
        is_verified=True,
    )
    profile = UserProfile(full_name="Test Cascade User")
    user.profile = profile

    db_session.add(user)
    await db_session.flush()

    # Verify that the user was assigned an ID, and the profile was also persisted and linked automatically
    assert user.id is not None
    assert profile.id is not None
    assert profile.user_id == user.id

    # Fetch from DB to verify
    stmt = select(User).where(User.id == user.id)
    res = await db_session.execute(stmt)
    db_user = res.scalar_one_or_none()
    assert db_user is not None
    assert db_user.profile is not None
    assert db_user.profile.full_name == "Test Cascade User"


async def test_db02_cascade_delete_user(db_session):
    """
    DB-02: Xóa User -> cascade xóa UserProfile, History, Progress, RefreshToken.
    """
    # 1. Setup User and all dependent objects
    user = User(
        email="user_to_delete@example.com",
        password_hash="some_hash",
    )
    profile = UserProfile(full_name="Deleted User Profile")
    user.profile = profile

    progress = Progress(subject="Reading", total_questions=40, completed_questions=20, percentage=50.0)
    user.progress.append(progress)

    history = History(subject="Reading", score=20, total_questions=40, percentage=50.0)
    user.history.append(history)

    token = RefreshToken(token_hash="some_unique_token_hash", expires_at=datetime.now(timezone.utc))
    user.refresh_tokens.append(token)

    db_session.add(user)
    await db_session.flush()

    user_id = user.id
    profile_id = profile.id
    progress_id = progress.id
    history_id = history.id
    token_id = token.id

    # Verify everything exists before delete
    assert (await db_session.get(User, user_id)) is not None
    assert (await db_session.get(UserProfile, profile_id)) is not None
    assert (await db_session.get(Progress, progress_id)) is not None
    assert (await db_session.get(History, history_id)) is not None
    assert (await db_session.get(RefreshToken, token_id)) is not None

    # 2. Delete the user
    await db_session.delete(user)
    await db_session.flush()

    # 3. Verify all associated records are deleted (cascade)
    assert (await db_session.get(User, user_id)) is None
    assert (await db_session.get(UserProfile, profile_id)) is None
    assert (await db_session.get(Progress, progress_id)) is None
    assert (await db_session.get(History, history_id)) is None
    assert (await db_session.get(RefreshToken, token_id)) is None


async def test_db03_unique_constraint_email(db_session):
    """
    DB-03: UniqueConstraint email trùng raises IntegrityError.
    """
    user1 = User(email="duplicate@example.com", password_hash="hash")
    db_session.add(user1)
    await db_session.flush()

    user2 = User(email="duplicate@example.com", password_hash="another_hash")
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_db04_unique_constraint_progress_user_subject(db_session):
    """
    DB-04: UniqueConstraint (user_id, subject) trong Progress.
    """
    user = User(email="progress_uniq@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    progress1 = Progress(user_id=user.id, subject="Listening")
    progress2 = Progress(user_id=user.id, subject="Listening")

    db_session.add_all([progress1, progress2])

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_db05_foreign_key_constraint_history_nonexistent_user(db_session):
    """
    DB-05: ForeignKey constraint: tạo History với user_id không tồn tại.
    """
    history = History(user_id=999999, subject="Writing", score=6)
    db_session.add(history)

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_db06_unique_constraint_shadowing_user_video(db_session):
    """
    DB-06: ShadowingUserHistory unique (user_id, video_id).
    """
    user = User(email="shadow_uniq@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    history1 = ShadowingUserHistory(user_id=user.id, video_id="vid123")
    history2 = ShadowingUserHistory(user_id=user.id, video_id="vid123")

    db_session.add_all([history1, history2])

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_db07_unique_constraint_score_history_user_skill_ds(db_session):
    """
    SH-02: UniqueConstraint (user_id, skill, ds) in ScoreHistory.
    """
    user = User(email="score_uniq@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    today = date.today()
    sh1 = ScoreHistory(user_id=user.id, skill="Reading", ds=today, y=7.5)
    sh2 = ScoreHistory(user_id=user.id, skill="Reading", ds=today, y=8.0)

    db_session.add_all([sh1, sh2])

    with pytest.raises(IntegrityError):
        await db_session.flush()
