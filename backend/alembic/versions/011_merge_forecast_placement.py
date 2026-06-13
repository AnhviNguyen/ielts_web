"""011 – merge the forecast (009_score_forecast) and placement (010_placement) heads

Both branches diverged from 008_conversation_practice:
  008 → 009_admin_content_soft_archive → 010_placement
  008 → 009_score_forecast

This is an empty merge revision so `alembic upgrade head` resolves to a single
head again. Databases that were on either branch get the missing branch applied
(the underlying migrations are idempotent — they inspect before creating).
"""
from __future__ import annotations

revision = "011_merge_forecast_placement"
down_revision = ("010_placement", "009_score_forecast")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
