"""
tests/integration/db/test_user_repository.py
─────────────────────────────────────────────
Integration tests cho UserRepository — thao tác CRUD với PostgreSQL thật.

Bao phủ:
  USR-01  create() → user được persist, id được gán
  USR-02  get_by_id() → tìm thấy user vừa tạo
  USR-03  get_by_id() với id không tồn tại → None
  USR-04  get_by_email() → tìm thấy đúng user
  USR-05  get_by_email() với email không tồn tại → None
  USR-06  Email unique constraint → IntegrityError khi tạo 2 user cùng email
  USR-07  get_by_google_id() → tìm thấy user OAuth
  USR-08  get_by_google_id() với google_id không tồn tại → None
  USR-09  mark_verified() → is_verified = True
  USR-10  update_google_id() → google_id được cập nhật
  USR-11  update_password_hash() → password_hash được cập nhật
  USR-12  create() với role="admin" → role được lưu đúng
  USR-13  create() với auth_provider="google" → auth_provider đúng
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# USR-01: create() → user được persist với id tự tăng
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr01_create_user_returns_with_id(make_user):
    user = await make_user()

    assert user.id is not None
    assert user.id > 0
    assert user.email.endswith("@example.com")
    assert user.role == "user"
    assert user.is_active is True
    assert user.is_verified is True


# ---------------------------------------------------------------------------
# USR-02: get_by_id() → tìm thấy user vừa tạo
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr02_get_by_id_returns_correct_user(user_repo, make_user):
    user = await make_user(email="findme@example.com")

    fetched = await user_repo.get_by_id(user.id)

    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.email == "findme@example.com"


# ---------------------------------------------------------------------------
# USR-03: get_by_id() với id không tồn tại → None
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr03_get_by_id_nonexistent_returns_none(user_repo):
    result = await user_repo.get_by_id(99999999)
    assert result is None


# ---------------------------------------------------------------------------
# USR-04: get_by_email() → tìm thấy đúng user
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr04_get_by_email_returns_correct_user(user_repo, make_user):
    await make_user(email="alpha@example.com")
    await make_user(email="beta@example.com")

    found = await user_repo.get_by_email("alpha@example.com")

    assert found is not None
    assert found.email == "alpha@example.com"


# ---------------------------------------------------------------------------
# USR-05: get_by_email() với email không tồn tại → None
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr05_get_by_email_nonexistent_returns_none(user_repo):
    result = await user_repo.get_by_email("ghost@nowhere.com")
    assert result is None


# ---------------------------------------------------------------------------
# USR-06: Email unique constraint → IntegrityError khi duplicate
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr06_duplicate_email_raises_integrity_error(user_repo):
    await user_repo.create(
        email="dup@example.com",
        password_hash="hash1",
    )

    with pytest.raises(IntegrityError):
        await user_repo.create(
            email="dup@example.com",
            password_hash="hash2",
        )


# ---------------------------------------------------------------------------
# USR-07: get_by_google_id() → tìm thấy user OAuth
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr07_get_by_google_id_returns_user(user_repo, make_user):
    await make_user(
        email="oauth@example.com",
        google_id="google-uid-abc123",
        auth_provider="google",
    )

    found = await user_repo.get_by_google_id("google-uid-abc123")

    assert found is not None
    assert found.google_id == "google-uid-abc123"
    assert found.auth_provider == "google"


# ---------------------------------------------------------------------------
# USR-08: get_by_google_id() với google_id không tồn tại → None
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr08_get_by_google_id_nonexistent_returns_none(user_repo):
    result = await user_repo.get_by_google_id("nonexistent-google-id")
    assert result is None


# ---------------------------------------------------------------------------
# USR-09: mark_verified() → is_verified thay đổi thành True
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr09_mark_verified_sets_is_verified_true(user_repo):
    user = await user_repo.create(
        email="unverified@example.com",
        password_hash="hash",
        is_verified=False,
    )
    assert user.is_verified is False

    updated = await user_repo.mark_verified(user)

    assert updated.is_verified is True
    assert updated.id == user.id


# ---------------------------------------------------------------------------
# USR-10: update_google_id() → google_id được cập nhật
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr10_update_google_id_persisted(user_repo, make_user):
    user = await make_user(email="nooauth@example.com")
    assert user.google_id is None

    updated = await user_repo.update_google_id(user, "new-google-id-xyz")

    assert updated.google_id == "new-google-id-xyz"
    assert updated.id == user.id

    # Verify bằng cách fetch lại từ DB
    refetched = await user_repo.get_by_id(user.id)
    assert refetched.google_id == "new-google-id-xyz"


# ---------------------------------------------------------------------------
# USR-11: update_password_hash() → password_hash được cập nhật
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr11_update_password_hash_persisted(user_repo, make_user):
    user = await make_user(email="changepwd@example.com", password_hash="old-hash")

    updated = await user_repo.update_password_hash(user, "new-strong-hash")

    assert updated.password_hash == "new-strong-hash"
    # Verify từ DB
    refetched = await user_repo.get_by_id(user.id)
    assert refetched.password_hash == "new-strong-hash"


# ---------------------------------------------------------------------------
# USR-12: create() với role="admin" → role được lưu đúng
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr12_create_admin_role_persisted(user_repo):
    admin = await user_repo.create(
        email="admin@example.com",
        password_hash="hash",
        role="admin",
    )

    assert admin.role == "admin"
    refetched = await user_repo.get_by_id(admin.id)
    assert refetched.role == "admin"


# ---------------------------------------------------------------------------
# USR-13: create() với auth_provider="google" → lưu đúng
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_usr13_create_google_provider_persisted(user_repo):
    user = await user_repo.create(
        email="guser@example.com",
        password_hash="",
        auth_provider="google",
        google_id="gid-456",
    )

    assert user.auth_provider == "google"
    assert user.google_id == "gid-456"
