"""Add performance indexes for history, profiles, vocab, practice sessions.

Revision ID: 001_add_indexes
Revises: 20260524_initial
Create Date: 2026-05-24

"""

from typing import Sequence, Union

from alembic import op

revision: str = "001_add_indexes"
down_revision: Union[str, None] = "20260524_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # if_not_exists: indexes may already exist from create_all in 20260524_initial
    op.create_index(
        "idx_history_user_date",
        "history",
        ["user_id", "completed_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_history_user_subject",
        "history",
        ["user_id", "subject"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_user_profiles_xp",
        "user_profiles",
        ["xp"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_vocab_words_topic_srs",
        "vocab_words",
        ["topic_id", "srs_next_review_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_practice_sessions_user",
        "practice_sessions",
        ["user_id", "started_at"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("idx_practice_sessions_user", table_name="practice_sessions")
    op.drop_index("idx_vocab_words_topic_srs", table_name="vocab_words")
    op.drop_index("idx_user_profiles_xp", table_name="user_profiles")
    op.drop_index("idx_history_user_subject", table_name="history")
    op.drop_index("idx_history_user_date", table_name="history")
