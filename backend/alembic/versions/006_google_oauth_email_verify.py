"""Google OAuth columns and email_verifications table.

Revision ID: 006_google_oauth_email_verify
Revises: 005_admin_user_columns
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "006_google_oauth_email_verify"
down_revision = "005_admin_user_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    user_columns = {col["name"] for col in inspector.get_columns("users")}

    if "google_id" not in user_columns:
        op.add_column("users", sa.Column("google_id", sa.String(255), nullable=True))
        op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    if "is_verified" not in user_columns:
        # Existing users are trusted — mark them verified by default.
        op.add_column(
            "users",
            sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        )

    if "auth_provider" not in user_columns:
        op.add_column(
            "users",
            sa.Column("auth_provider", sa.String(20), nullable=False, server_default="email"),
        )

    tables = inspector.get_table_names()
    if "email_verifications" not in tables:
        op.create_table(
            "email_verifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("code_hash", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_email_verifications_user_id", "email_verifications", ["user_id"]
        )


def downgrade() -> None:
    op.drop_table("email_verifications")
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "is_verified")
    op.drop_column("users", "google_id")
