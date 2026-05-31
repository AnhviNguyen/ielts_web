"""Initial schema — frozen baseline DDL (no live model import).

Revision ID: 20260524_initial
Revises:
Create Date: 2026-05-24

Tables/columns added in later revisions (002–005) are intentionally omitted here
so `alembic upgrade head` on a fresh database does not duplicate objects.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260524_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("full_name", sa.String(255)),
        sa.Column("avatar_url", sa.Text()),
        sa.Column("phone", sa.String(20)),
        sa.Column("bio", sa.Text()),
        sa.Column("target_band", sa.Float(), server_default="7"),
        sa.Column("exam_date", sa.Date()),
        sa.Column("streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("streak_freeze_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_activity_date", sa.Date()),
        sa.Column("xp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("daily_writing_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("daily_speaking_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tutor_questions_used_month", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_user_profiles_id", "user_profiles", ["id"])

    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_type", sa.String(20), nullable=False),
        sa.Column("quiz_id", sa.String(100)),
        sa.Column("status", sa.String(20), server_default="started", nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_practice_sessions_id", "practice_sessions", ["id"])
    op.create_index("ix_practice_sessions_user_id", "practice_sessions", ["user_id"])

    op.create_table(
        "history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quiz_id", sa.String(100)),
        sa.Column(
            "practice_session_id",
            sa.Integer(),
            sa.ForeignKey("practice_sessions.id", ondelete="SET NULL"),
        ),
        sa.Column("subject", sa.String(100)),
        sa.Column("score", sa.Integer()),
        sa.Column("total_questions", sa.Integer()),
        sa.Column("percentage", sa.Float()),
        sa.Column("band_score", sa.Float()),
        sa.Column("mode", sa.String(20)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("answers", sa.JSON()),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_history_id", "history", ["id"])
    op.create_index("ix_history_practice_session_id", "history", ["practice_session_id"])

    op.create_table(
        "progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("total_questions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed_questions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("percentage", sa.Float(), server_default="0", nullable=False),
        sa.Column("band_score", sa.Float()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "subject", name="uq_user_subject"),
    )
    op.create_index("ix_progress_id", "progress", ["id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "vocab_topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_vocab_topics_id", "vocab_topics", ["id"])
    op.create_index("ix_vocab_topics_user_id", "vocab_topics", ["user_id"])

    op.create_table(
        "vocab_words",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("vocab_topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("word", sa.String(200), nullable=False),
        sa.Column("phonetic", sa.String(200)),
        sa.Column("word_type", sa.String(100)),
        sa.Column("meaning_en", sa.Text()),
        sa.Column("meaning_vi", sa.Text()),
        sa.Column("example", sa.Text()),
        sa.Column("example_vi", sa.Text()),
        sa.Column("note", sa.Text()),
        sa.Column("mastery", sa.String(20), server_default="new", nullable=False),
        sa.Column("srs_ease", sa.Float(), server_default="2.5", nullable=False),
        sa.Column("srs_interval_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("srs_repetitions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("srs_next_review_at", sa.DateTime(timezone=True)),
        sa.Column("srs_last_review_at", sa.DateTime(timezone=True)),
        sa.Column("source_quiz_id", sa.String(100)),
        sa.Column("source_type", sa.String(20)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_vocab_words_id", "vocab_words", ["id"])
    op.create_index("ix_vocab_words_topic_id", "vocab_words", ["topic_id"])

    op.create_table(
        "system_vocab_topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("level", sa.String(50)),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_system_vocab_topics_id", "system_vocab_topics", ["id"])
    op.create_index("ix_system_vocab_topics_name", "system_vocab_topics", ["name"])

    op.create_table(
        "system_vocab_words",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("system_vocab_topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("word", sa.String(200), nullable=False),
        sa.Column("phonetic", sa.String(200)),
        sa.Column("word_type", sa.String(100)),
        sa.Column("meaning_en", sa.Text()),
        sa.Column("meaning_vi", sa.Text()),
        sa.Column("example", sa.Text()),
        sa.Column("example_vi", sa.Text()),
        sa.Column("tags", sa.JSON()),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_system_vocab_words_id", "system_vocab_words", ["id"])
    op.create_index("ix_system_vocab_words_topic_id", "system_vocab_words", ["topic_id"])

    op.create_table(
        "reading_annotations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("quiz_id", sa.String(100)),
        sa.Column("highlights", sa.JSON()),
        sa.Column("note", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_reading_annotations_id", "reading_annotations", ["id"])
    op.create_index("ix_reading_annotations_user_id", "reading_annotations", ["user_id"])
    op.create_index("ix_reading_annotations_session_id", "reading_annotations", ["session_id"])
    op.create_index("ix_reading_annotations_quiz_id", "reading_annotations", ["quiz_id"])

    op.create_table(
        "shadowing_videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), server_default="", nullable=False),
        sa.Column("level", sa.String(50), server_default="Intermediate", nullable=False),
        sa.Column("language", sa.String(10), server_default="en", nullable=False),
        sa.Column("source_url", sa.Text(), server_default="", nullable=False),
        sa.Column("transcript_source", sa.String(20), server_default="youtube", nullable=False),
        sa.Column("segments", sa.JSON(), server_default="[]", nullable=False),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_shadowing_videos_id", "shadowing_videos", ["id"])
    op.create_index("ix_shadowing_videos_video_id", "shadowing_videos", ["video_id"], unique=True)

    op.create_table(
        "shadowing_user_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("video_id", sa.String(20), nullable=False),
        sa.Column("display_title", sa.String(500)),
        sa.Column("display_level", sa.String(50)),
        sa.Column(
            "last_viewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "video_id", name="uq_shadowing_user_video"),
    )
    op.create_index("ix_shadowing_user_history_id", "shadowing_user_history", ["id"])
    op.create_index("ix_shadowing_user_history_user_id", "shadowing_user_history", ["user_id"])
    op.create_index("ix_shadowing_user_history_video_id", "shadowing_user_history", ["video_id"])

    op.create_table(
        "study_plan_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("plan_date", sa.Date()),
        sa.Column("focus_skill", sa.String(50), nullable=False),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), server_default="45", nullable=False),
        sa.Column("quiz_id", sa.String(100)),
        sa.Column("route_path", sa.String(200)),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_study_plan_tasks_id", "study_plan_tasks", ["id"])
    op.create_index("ix_study_plan_tasks_user_id", "study_plan_tasks", ["user_id"])


def downgrade() -> None:
    op.drop_table("study_plan_tasks")
    op.drop_table("shadowing_user_history")
    op.drop_table("shadowing_videos")
    op.drop_table("reading_annotations")
    op.drop_table("system_vocab_words")
    op.drop_table("system_vocab_topics")
    op.drop_table("vocab_words")
    op.drop_table("vocab_topics")
    op.drop_table("refresh_tokens")
    op.drop_table("progress")
    op.drop_table("history")
    op.drop_table("practice_sessions")
    op.drop_table("user_profiles")
    op.drop_table("users")
