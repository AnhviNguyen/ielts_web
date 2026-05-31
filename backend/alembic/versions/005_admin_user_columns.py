"""Admin: users.role/lock fields and user_profiles leaderboard moderation."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "005_admin_user_columns"
down_revision = "004_adaptive_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "role" not in user_columns:
        op.add_column(
            "users",
            sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        )
    if "is_active" not in user_columns:
        op.add_column(
            "users",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if "locked_at" not in user_columns:
        op.add_column("users", sa.Column("locked_at", sa.DateTime(timezone=True)))
    if "lock_reason" not in user_columns:
        op.add_column("users", sa.Column("lock_reason", sa.Text()))

    profile_columns = {col["name"] for col in inspector.get_columns("user_profiles")}
    if "is_leaderboard_hidden" not in profile_columns:
        op.add_column(
            "user_profiles",
            sa.Column(
                "is_leaderboard_hidden",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    if "leaderboard_flag_reason" not in profile_columns:
        op.add_column("user_profiles", sa.Column("leaderboard_flag_reason", sa.Text()))
    if "leaderboard_hidden_at" not in profile_columns:
        op.add_column(
            "user_profiles",
            sa.Column("leaderboard_hidden_at", sa.DateTime(timezone=True)),
        )


def downgrade() -> None:
    op.drop_column("user_profiles", "leaderboard_hidden_at")
    op.drop_column("user_profiles", "leaderboard_flag_reason")
    op.drop_column("user_profiles", "is_leaderboard_hidden")
    op.drop_column("users", "lock_reason")
    op.drop_column("users", "locked_at")
    op.drop_column("users", "is_active")
    op.drop_column("users", "role")
