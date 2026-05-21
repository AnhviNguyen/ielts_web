"""
migrate_add_missing_columns.py
──────────────────────────────
Adds columns that exist in the ORM models but are missing in the live
PostgreSQL database (schema drift from incremental model updates).

Run once:
    python migrate_add_missing_columns.py
"""

import asyncio
import re
import sys

from app.core.config import settings


async def run_migration():
    # Convert SQLAlchemy async URL to plain asyncpg DSN
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        print("SQLite detected — SQLite auto-creates columns on startup. Nothing to do.")
        return

    # asyncpg uses postgresql:// (no +asyncpg driver prefix)
    dsn = re.sub(r"^postgresql\+asyncpg", "postgresql", db_url)
    dsn = re.sub(r"^postgres\+asyncpg", "postgresql", dsn)

    try:
        import asyncpg
    except ImportError:
        print("asyncpg not installed — install it with: pip install asyncpg")
        sys.exit(1)

    conn = await asyncpg.connect(dsn)
    print(f"Connected to: {dsn.split('@')[-1]}")

    # Each tuple: (table, column, type_definition)
    MIGRATIONS = [
        # user_profiles — columns added after initial schema
        ("user_profiles", "longest_streak",              "INTEGER NOT NULL DEFAULT 0"),
        ("user_profiles", "streak_freeze_count",         "INTEGER NOT NULL DEFAULT 0"),
        ("user_profiles", "last_activity_date",          "DATE"),
        ("user_profiles", "daily_writing_used",          "INTEGER NOT NULL DEFAULT 0"),
        ("user_profiles", "daily_speaking_used",         "INTEGER NOT NULL DEFAULT 0"),
        ("user_profiles", "tutor_questions_used_month",  "INTEGER NOT NULL DEFAULT 0"),
        # history — columns added after initial schema
        ("history", "band_score",       "FLOAT"),
        ("history", "mode",             "VARCHAR(20)"),
        ("history", "duration_seconds", "INTEGER"),
        ("history", "practice_session_id", "INTEGER"),
        # progress — band_score column
        ("progress", "band_score", "FLOAT"),
        # study_plan_tasks — new table (create_all handles this, but include as safety)
    ]

    for table, column, col_type in MIGRATIONS:
        try:
            await conn.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type};"
            )
            print(f"  OK  {table}.{column}")
        except Exception as exc:
            print(f"  ERR {table}.{column}: {exc}")

    # Ensure study_plan_tasks table exists (safe — IF NOT EXISTS)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS study_plan_tasks (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            day_number       INTEGER NOT NULL,
            plan_date        DATE,
            focus_skill      VARCHAR(50) NOT NULL,
            task_description TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL DEFAULT 45,
            quiz_id          VARCHAR(100),
            route_path       VARCHAR(200),
            is_completed     BOOLEAN NOT NULL DEFAULT FALSE,
            completed_at     TIMESTAMPTZ,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    print("  OK  study_plan_tasks table (created or already exists)")

    # New: vocab topics
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS vocab_topics (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name       VARCHAR(200) NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    print("  OK  vocab_topics table")

    # New: vocab words
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS vocab_words (
            id         SERIAL PRIMARY KEY,
            topic_id   INTEGER NOT NULL REFERENCES vocab_topics(id) ON DELETE CASCADE,
            word       VARCHAR(200) NOT NULL,
            phonetic   VARCHAR(200),
            word_type  VARCHAR(100),
            meaning_vi TEXT,
            example    TEXT,
            example_vi TEXT,
            note       TEXT,
            mastery    VARCHAR(20) NOT NULL DEFAULT 'new',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    print("  OK  vocab_words table")

    VOCAB_WORD_COLS = [
        ("vocab_words", "meaning_en", "TEXT"),
        ("vocab_words", "source_type", "VARCHAR(30)"),
        ("vocab_words", "source_quiz_id", "VARCHAR(100)"),
        ("vocab_words", "srs_ease", "FLOAT NOT NULL DEFAULT 2.5"),
        ("vocab_words", "srs_interval_days", "INTEGER NOT NULL DEFAULT 0"),
        ("vocab_words", "srs_repetitions", "INTEGER NOT NULL DEFAULT 0"),
        ("vocab_words", "srs_next_review_at", "TIMESTAMPTZ"),
        ("vocab_words", "srs_last_review_at", "TIMESTAMPTZ"),
    ]
    for table, column, col_type in VOCAB_WORD_COLS:
        try:
            await conn.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type};"
            )
            print(f"  OK  {table}.{column}")
        except Exception as exc:
            print(f"  ERR {table}.{column}: {exc}")

    # New: reading annotations
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS reading_annotations (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_id VARCHAR(100) NOT NULL,
            quiz_id    VARCHAR(100),
            highlights JSONB,
            note       TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_reading_annotations_session ON reading_annotations(session_id);
    """)
    print("  OK  reading_annotations table")

    await conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run_migration())
