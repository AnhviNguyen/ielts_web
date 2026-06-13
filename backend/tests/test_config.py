"""Tests for Settings env normalization."""

from app.core.config import Settings

_SECRET = "a" * 32


def test_database_url_converts_postgresql_scheme():
    s = Settings(
        SECRET_KEY=_SECRET,
        DATABASE_URL="postgresql://user:pass@host:5432/railway",
    )
    assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/railway"


def test_database_url_converts_postgres_scheme():
    s = Settings(
        SECRET_KEY=_SECRET,
        DATABASE_URL="postgres://user:pass@host:5432/railway",
    )
    assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/railway"


def test_database_url_keeps_asyncpg_driver():
    url = "postgresql+asyncpg://user:pass@host:5432/linguaielts"
    s = Settings(SECRET_KEY=_SECRET, DATABASE_URL=url)
    assert s.DATABASE_URL == url


def test_database_url_keeps_sqlite():
    url = "sqlite+aiosqlite:///./linguaielts.db"
    s = Settings(SECRET_KEY=_SECRET, DATABASE_URL=url)
    assert s.DATABASE_URL == url
