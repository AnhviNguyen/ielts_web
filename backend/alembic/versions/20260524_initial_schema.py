"""Initial schema — all tables from SQLAlchemy models.

Revision ID: 20260524_initial
Revises:
Create Date: 2026-05-24

"""

from typing import Sequence, Union

from alembic import op

# Import models so Base.metadata is populated
from app.db import models  # noqa: F401
from app.db.database import Base

revision: str = "20260524_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
