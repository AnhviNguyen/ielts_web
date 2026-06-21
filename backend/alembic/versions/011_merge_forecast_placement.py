"""011 – merge the forecast (009_score_forecast) and placement (010_placement) heads

Both branches diverged from 008_conversation_practice:
  008 → 009_admin_content_soft_archive → 010_placement
  008 → 009_score_forecast

009_admin_content_soft_archive is not listed in down_revision because it is an
ancestor of 010_placement (not a separate head). This merge only needs the two
leaf revisions before upgrade continues to 012_user_ai_settings.
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
