"""008 – Conversation practice tables"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "008_conversation_practice"
down_revision = "007_translation_practice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "conversation_topics" not in tables:
        op.create_table(
            "conversation_topics",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("level", sa.String(20), nullable=False, server_default="beginner"),
            sa.Column("icon_emoji", sa.String(10), nullable=False, server_default="💬"),
            sa.Column("ai_role", sa.String(300), nullable=False),
            sa.Column("user_role", sa.String(300), nullable=False),
            sa.Column("scenario", sa.Text(), nullable=False),
            sa.Column("opening_line", sa.Text(), nullable=False),
            sa.Column("vocabulary", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if "conversation_sessions" not in tables:
        op.create_table(
            "conversation_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("topic_id", sa.Integer(), sa.ForeignKey("conversation_topics.id", ondelete="CASCADE"), nullable=False),
            sa.Column("history", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("feedback", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_conversation_sessions_user_id", "conversation_sessions", ["user_id"])
        op.create_index("ix_conversation_sessions_topic_id", "conversation_sessions", ["topic_id"])


def downgrade() -> None:
    op.drop_table("conversation_sessions")
    op.drop_table("conversation_topics")
