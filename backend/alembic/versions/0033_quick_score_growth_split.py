"""fa_quick_scores.growth_annual / growth_quarterly — the two components
blended into `growth` (see scoring.py::_growth_score()), stored so the
Quick Screener can filter/sort on either one, not just the blend.

Revision ID: 0033
Revises: 0032
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fa_quick_scores", sa.Column("growth_annual", sa.Numeric(6, 2), nullable=True))
    op.add_column("fa_quick_scores", sa.Column("growth_quarterly", sa.Numeric(6, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("fa_quick_scores", "growth_quarterly")
    op.drop_column("fa_quick_scores", "growth_annual")
