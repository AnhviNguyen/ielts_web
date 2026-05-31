"""Adaptive study SRS, notifications, study plan priority columns."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "004_adaptive_notifications"
down_revision = "003_history_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Use raw SQL with IF NOT EXISTS to avoid inspect() issues with async drivers
    bind.execute(sa.text(
        "ALTER TABLE study_plan_tasks "
        "ADD COLUMN IF NOT EXISTS suggested_difficulty VARCHAR(20);"
    ))
    bind.execute(sa.text(
        "ALTER TABLE study_plan_tasks "
        "ADD COLUMN IF NOT EXISTS priority_score FLOAT NOT NULL DEFAULT 0;"
    ))

    if not inspector.has_table("skill_adaptive_states"):
        op.create_table(
            "skill_adaptive_states",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("skill", sa.String(30), nullable=False),
            sa.Column("srs_ease", sa.Float(), server_default="2.5", nullable=False),
            sa.Column("srs_interval_days", sa.Integer(), server_default="1", nullable=False),
            sa.Column("srs_repetitions", sa.Integer(), server_default="0", nullable=False),
            sa.Column("srs_next_review_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("srs_last_review_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("suggested_difficulty", sa.String(20), server_default="medium", nullable=False),
            sa.Column("avg_performance", sa.Float(), server_default="0", nullable=False),
            sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "skill", name="uq_user_skill_adaptive"),
        )
        inspector = inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes("skill_adaptive_states")}
    if "idx_skill_adaptive_user" not in indexes:
        op.create_index("idx_skill_adaptive_user", "skill_adaptive_states", ["user_id"])

    if not inspector.has_table("notification_settings"):
        op.create_table(
            "notification_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("reminder_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("reminder_time", sa.Time(), nullable=True),
            sa.Column("channel", sa.String(20), server_default="in_app", nullable=False),
            sa.Column("email_daily_digest", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("push_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("timezone", sa.String(64), server_default="Asia/Ho_Chi_Minh", nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not inspector.has_table("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", sa.String(40), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("link_path", sa.String(200), nullable=True),
            sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        inspector = inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes("notifications")}
    if "idx_notifications_user_read" not in indexes:
        op.create_index("idx_notifications_user_read", "notifications", ["user_id", "is_read", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_notifications_user_read", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("notification_settings")
    op.drop_index("idx_skill_adaptive_user", table_name="skill_adaptive_states")
    op.drop_table("skill_adaptive_states")
    op.drop_column("study_plan_tasks", "priority_score")
    op.drop_column("study_plan_tasks", "suggested_difficulty")
