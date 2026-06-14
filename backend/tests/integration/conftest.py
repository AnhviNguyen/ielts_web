"""
tests/integration/conftest.py
──────────────────────────────
Shared fixtures cho toàn bộ integration tests (Tầng 2+).

Chiến lược test database:
  - Dùng PostgreSQL test DB riêng: LinguaIELTS_test
    (URL = DATABASE_URL nhưng thay DB name thành LinguaIELTS_test)
  - Scope "session": tạo engine + tất cả tables 1 lần/test session
  - Scope "function": mỗi test chạy trong transaction riêng, rollback sau khi xong
    → Không cần truncate, không ảnh hưởng test khác (DB isolation)

Fixtures hierarchy:
  engine          (scope=session) — async engine kết nối test DB
  create_tables   (scope=session) — create_all / drop_all
  db_session      (scope=function) — transaction mới + rollback sau mỗi test
  user_repo       (scope=function) — UserRepository(db_session)
  profile_repo    (scope=function) — ProfileRepository(db_session)
  history_repo    (scope=function) — HistoryRepository(db_session)
  vocab_repo      (scope=function) — VocabRepository(db_session)
"""

from __future__ import annotations

import os
import re

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Xây test DATABASE_URL từ biến môi trường (thay DB name → _test)
# ---------------------------------------------------------------------------

def _test_db_url() -> str:
    """
    Lấy DATABASE_URL từ env (đã được .env nạp khi backend khởi động) và thay
    tên database thành <name>_test.

    Ví dụ:
        postgresql+asyncpg://postgres:root@localhost:5432/LinguaIELTS
        →  postgresql+asyncpg://postgres:root@localhost:5432/LinguaIELTS_test
    """
    # Ưu tiên biến TEST_DATABASE_URL nếu được set tường minh
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        return url

    # Fallback: lấy từ settings (nạp .env)
    from app.core.config import settings
    base_url = settings.DATABASE_URL

    # Thay tên DB: pattern /dbname hoặc /dbname?params
    # Regex: khớp tên DB sau dấu / cuối cùng trước ? hoặc cuối chuỗi
    test_url = re.sub(
        r"(/[^/?]+)(\?.*)?$",
        lambda m: m.group(1) + "_test" + (m.group(2) or ""),
        base_url,
    )
    return test_url


TEST_DB_URL = _test_db_url()


# ---------------------------------------------------------------------------
# engine — session scope
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Tạo async engine cho test DB (dùng chung cho toàn session)."""
    eng = create_async_engine(
        TEST_DB_URL,
        echo=False,           # tắt SQL log để output gọn
        pool_pre_ping=True,
    )
    yield eng
    await eng.dispose()


# ---------------------------------------------------------------------------
# create_tables — session scope
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def create_tables(engine):
    """
    Tạo toàn bộ bảng trong test DB trước khi chạy tests,
    drop tất cả sau khi session kết thúc.

    Lưu ý: Import Base SAU KHI settings đã được cấu hình.
    """
    from app.db.database import Base
    # Import tất cả models để Base metadata biết về chúng
    import app.db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# db_session — function scope (transaction + rollback)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session(engine, create_tables) -> AsyncSession:
    """
    Cung cấp AsyncSession cho mỗi test case.

    Cơ chế isolation:
      1. Mở connection + bắt đầu outer transaction (SAVEPOINT)
      2. Tạo session bind vào connection đó
      3. Sau khi test xong → rollback outer transaction
         → tất cả data của test bị xóa, không ảnh hưởng test tiếp theo

    Đây là pattern "nested transaction rollback" — không cần truncate.
    """
    async with engine.connect() as conn:
        # Bắt đầu transaction bao ngoài
        await conn.begin()

        # Session dùng nested transaction (savepoint) bên trong
        session_factory = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with session_factory() as session:
            yield session
            # Không commit — data sẽ bị rollback cùng outer transaction

        # Rollback outer transaction → xóa sạch data test
        await conn.rollback()


# ---------------------------------------------------------------------------
# Repository fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def user_repo(db_session):
    """UserRepository bound to the test session."""
    from app.repositories.user_repository import UserRepository
    return UserRepository(db_session)


@pytest_asyncio.fixture
async def profile_repo(db_session):
    """ProfileRepository bound to the test session."""
    from app.repositories.profile_repository import ProfileRepository
    return ProfileRepository(db_session)


@pytest_asyncio.fixture
async def history_repo(db_session):
    """HistoryRepository bound to the test session."""
    from app.repositories.history_repository import HistoryRepository
    return HistoryRepository(db_session)


@pytest_asyncio.fixture
async def vocab_repo(db_session):
    """VocabRepository bound to the test session."""
    from app.repositories.vocab_repository import VocabRepository
    return VocabRepository(db_session)


# ---------------------------------------------------------------------------
# Helper factories (tạo data test nhanh)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def make_user(user_repo):
    """
    Factory để tạo User trong test.

    Dùng:
        user = await make_user()                       # user mặc định
        admin = await make_user(email="a@b.com", role="admin")
    """
    _counter = [0]

    async def _factory(
        email: str | None = None,
        password_hash: str = "hashed_password_placeholder",
        role: str = "user",
        is_verified: bool = True,
        auth_provider: str = "email",
        google_id: str | None = None,
    ):
        _counter[0] += 1
        _email = email or f"testuser{_counter[0]}@example.com"
        return await user_repo.create(
            email=_email,
            password_hash=password_hash,
            role=role,
            is_verified=is_verified,
            auth_provider=auth_provider,
            google_id=google_id,
        )

    return _factory


@pytest_asyncio.fixture
async def make_profile(profile_repo):
    """Factory để tạo UserProfile cho một user_id."""
    async def _factory(user_id: int, full_name: str | None = None):
        return await profile_repo.create_empty(user_id=user_id, full_name=full_name)
    return _factory


@pytest_asyncio.fixture
async def client(db_session):
    """Async httpx client with overridden database dependency."""
    from httpx import AsyncClient
    from app.main import app
    from app.db.database import get_db
    from app.core.rate_limit import limiter

    # Disable rate limits during testing
    limiter.enabled = False

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def auth_client(client, make_user, db_session):
    """Returns an authenticated client for a standard user."""
    from app.core.security import create_access_token
    user = await make_user(email="authuser@example.com", role="user", is_verified=True)
    await db_session.flush()
    token = create_access_token(subject=user.id)
    client.headers["Authorization"] = f"Bearer {token}"
    client.user = user
    return client


@pytest_asyncio.fixture
async def admin_client(client, make_user, db_session):
    """Returns an authenticated client for an admin user."""
    from app.core.security import create_access_token
    user = await make_user(email="adminuser@example.com", role="admin", is_verified=True)
    await db_session.flush()
    token = create_access_token(subject=user.id)
    client.headers["Authorization"] = f"Bearer {token}"
    client.user = user
    return client
