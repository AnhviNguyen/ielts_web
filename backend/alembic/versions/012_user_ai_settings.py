"""012 – Per-user AI provider + encrypted API key on profile."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "012_user_ai_settings"
down_revision = "011_merge_forecast_placement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    cols = {c["name"] for c in inspector.get_columns("user_profiles")}
    if "ai_provider" not in cols:
        op.add_column(
            "user_profiles",
            sa.Column("ai_provider", sa.String(20), nullable=True, server_default="system"),
        )
    if "ai_api_key_encrypted" not in cols:
        op.add_column(
            "user_profiles",
            sa.Column("ai_api_key_encrypted", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    cols = {c["name"] for c in inspector.get_columns("user_profiles")}
    if "ai_api_key_encrypted" in cols:
        op.drop_column("user_profiles", "ai_api_key_encrypted")
    if "ai_provider" in cols:
        op.drop_column("user_profiles", "ai_provider")
