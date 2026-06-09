"""Placement onboarding."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "010_placement"
down_revision = "009_admin_content_soft_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    profile_columns = {col["name"] for col in inspector.get_columns("user_profiles")}
    additions = {
        "placement_status": "VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "initial_band_source": "VARCHAR(20)",
        "initial_reading_band": "FLOAT",
        "initial_listening_band": "FLOAT",
        "initial_writing_band": "FLOAT",
        "initial_speaking_band": "FLOAT",
        "initial_overall_band": "FLOAT",
        "placement_completed_at": "TIMESTAMP WITH TIME ZONE",
    }
    for name, ddl in additions.items():
        if name not in profile_columns:
            bind.execute(sa.text(f"ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS {name} {ddl};"))

    if not inspector.has_table("placement_sessions"):
        op.create_table(
            "placement_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(20), server_default="started", nullable=False),
            sa.Column("current_stage", sa.String(20), server_default="reading", nullable=False),
            sa.Column("reading_quiz_id", sa.String(100), nullable=True),
            sa.Column("listening_quiz_id", sa.String(100), nullable=True),
            sa.Column("writing_topic_id", sa.String(100), nullable=True),
            sa.Column("speaking_quiz_id", sa.String(100), nullable=True),
            sa.Column("results", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        inspector = inspect(bind)
    placement_indexes = {idx["name"] for idx in inspector.get_indexes("placement_sessions")}
    if "idx_placement_sessions_user_status" not in placement_indexes:
        op.create_index(
            "idx_placement_sessions_user_status",
            "placement_sessions",
            ["user_id", "status", "started_at"],
        )


def downgrade() -> None:
    op.drop_index("idx_placement_sessions_user_status", table_name="placement_sessions")
    op.drop_table("placement_sessions")
    for column in (
        "placement_completed_at",
        "initial_overall_band",
        "initial_speaking_band",
        "initial_writing_band",
        "initial_listening_band",
        "initial_reading_band",
        "initial_band_source",
        "placement_status",
    ):
        op.drop_column("user_profiles", column)
