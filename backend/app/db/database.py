"""
app/db/database.py
───────────────────
Async SQLAlchemy engine and session factory.
Provides `get_db` dependency for FastAPI route injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ───────────────────────────────────────────────────────────────────
if settings.DATABASE_URL.startswith("sqlite+aiosqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    connect_args: dict = {}
    if settings.PGBOUNCER_ENABLED:
        connect_args["statement_cache_size"] = 0
    pool_size = 5 if settings.PGBOUNCER_ENABLED else 10
    max_overflow = 10 if settings.PGBOUNCER_ENABLED else 20
    engine_kwargs: dict = {
        "echo": settings.DEBUG,
        "pool_pre_ping": True,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_recycle": 300,
    }
    if connect_args:
        engine_kwargs["connect_args"] = connect_args
    engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# ── Session factory ──────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep objects usable after commit
)


# ── Base class for all ORM models ────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ───────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session and ensure it is closed after the request.
    Use as: `db: AsyncSession = Depends(get_db)`
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
