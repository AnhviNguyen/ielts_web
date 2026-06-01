"""Soft archive flags for admin-managed practice content.

Revision ID: 009_admin_content_soft_archive
Revises: 008_conversation_practice
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "009_admin_content_soft_archive"
down_revision = "008_conversation_practice"
branch_labels = None
depends_on = None


def _add_is_active(table_name: str) -> None:
    inspector = inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    if "is_active" not in columns:
        op.add_column(
            table_name,
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def upgrade() -> None:
    for table_name in (
        "conversation_topics",
        "translation_steps",
        "translation_topics",
        "translation_sentences",
    ):
        _add_is_active(table_name)


def downgrade() -> None:
    for table_name in (
        "translation_sentences",
        "translation_topics",
        "translation_steps",
        "conversation_topics",
    ):
        op.drop_column(table_name, "is_active")
