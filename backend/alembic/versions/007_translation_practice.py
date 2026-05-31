"""007 – Add translation practice tables

Revision ID: 007
Revises: 006
Create Date: 2026-05-30
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "007_translation_practice"
down_revision = "006_google_oauth_email_verify"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "translation_steps" not in tables:
        op.create_table(
            "translation_steps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("badge_label", sa.String(30), nullable=True),
            sa.Column("badge_color", sa.String(20), nullable=False, server_default="gray"),
            sa.Column("icon_emoji", sa.String(10), nullable=False, server_default="📝"),
        )

    if "translation_topics" not in tables:
        op.create_table(
            "translation_topics",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("step_id", sa.Integer(), sa.ForeignKey("translation_steps.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
        )
        op.create_index("ix_translation_topics_step_id", "translation_topics", ["step_id"])

    if "translation_sentences" not in tables:
        op.create_table(
            "translation_sentences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("topic_id", sa.Integer(), sa.ForeignKey("translation_topics.id", ondelete="CASCADE"), nullable=False),
            sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("vietnamese", sa.Text(), nullable=False),
            sa.Column("english", sa.Text(), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=True),
        )
        op.create_index("ix_translation_sentences_topic_id", "translation_sentences", ["topic_id"])

    if "translation_attempts" not in tables:
        op.create_table(
            "translation_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sentence_id", sa.Integer(), sa.ForeignKey("translation_sentences.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_translation", sa.Text(), nullable=False),
            sa.Column("score", sa.Float(), nullable=True),
            sa.Column("feedback", sa.Text(), nullable=True),
            sa.Column("model_answer", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_translation_attempts_user_id", "translation_attempts", ["user_id"])
        op.create_index("ix_translation_attempts_sentence_id", "translation_attempts", ["sentence_id"])


def downgrade() -> None:
    op.drop_table("translation_attempts")
    op.drop_table("translation_sentences")
    op.drop_table("translation_topics")
    op.drop_table("translation_steps")
