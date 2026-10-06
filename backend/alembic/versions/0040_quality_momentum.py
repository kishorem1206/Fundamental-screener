"""Quality Momentum columns on fw_scores.

Revision ID: 0040
Revises: 0039
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fw_scores", sa.Column("quality_change_6m", sa.Numeric(6, 2), nullable=True))
    op.add_column("fw_scores", sa.Column("quality_change_12m", sa.Numeric(6, 2), nullable=True))
    op.add_column("fw_scores", sa.Column("quality_direction", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("fw_scores", "quality_direction")
    op.drop_column("fw_scores", "quality_change_12m")
    op.drop_column("fw_scores", "quality_change_6m")
