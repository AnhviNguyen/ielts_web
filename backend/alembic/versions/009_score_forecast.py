"""009 – score_history + forecast_model_meta for band forecasting"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "009_score_forecast"
down_revision = "008_conversation_practice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "score_history" not in tables:
        op.create_table(
            "score_history",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("ds", sa.Date(), nullable=False),
            sa.Column("y", sa.Float(), nullable=False),
            sa.Column("skill", sa.String(32), nullable=False),
            sa.Column("session_min", sa.Float(), nullable=False, server_default="0"),
            sa.Column("correct_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "skill", "ds", name="uq_score_history_user_skill_ds"),
        )
        op.create_index("ix_score_history_user_id", "score_history", ["user_id"])
        op.create_index("idx_score_history_user_skill", "score_history", ["user_id", "skill"])
        op.create_index("idx_score_history_user_ds", "score_history", ["user_id", "ds"])

    if "forecast_model_meta" not in tables:
        op.create_table(
            "forecast_model_meta",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("skill", sa.String(32), nullable=False),
            sa.Column("trainer", sa.String(32), nullable=False, server_default="fallback"),
            sa.Column("mae", sa.Float(), nullable=True),
            sa.Column("rmse", sa.Float(), nullable=True),
            sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("model_path", sa.String(512), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("user_id", "skill", name="uq_forecast_model_user_skill"),
        )
        op.create_index("ix_forecast_model_meta_user_id", "forecast_model_meta", ["user_id"])


def downgrade() -> None:
    op.drop_table("forecast_model_meta")
    op.drop_table("score_history")
