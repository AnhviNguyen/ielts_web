"""Revision 003: history_archive table for cold storage."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "003_history_archive"
down_revision = "002_password_reset"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("history_archive"):
        op.create_table(
            "history_archive",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("quiz_id", sa.String(100), nullable=True),
            sa.Column("practice_session_id", sa.Integer(), nullable=True),
            sa.Column("subject", sa.String(100), nullable=True),
            sa.Column("score", sa.Integer(), nullable=True),
            sa.Column("total_questions", sa.Integer(), nullable=True),
            sa.Column("percentage", sa.Float(), nullable=True),
            sa.Column("band_score", sa.Float(), nullable=True),
            sa.Column("mode", sa.String(20), nullable=True),
            sa.Column("duration_seconds", sa.Integer(), nullable=True),
            sa.Column("answers", sa.JSON(), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("archived_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        inspector = inspect(bind)

    indexes = {idx["name"] for idx in inspector.get_indexes("history_archive")}
    if "idx_history_archive_user_date" not in indexes:
        op.create_index("idx_history_archive_user_date", "history_archive", ["user_id", "completed_at"])


def downgrade() -> None:
    op.drop_index("idx_history_archive_user_date", table_name="history_archive")
    op.drop_table("history_archive")
