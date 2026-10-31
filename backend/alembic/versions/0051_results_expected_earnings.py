"""Expected earnings on the results calendar.

Revision ID: 0051
Revises: 0050
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None

_NUMBERS = ("eps_estimate", "eps_low", "eps_high", "eps_year_ago", "revenue_estimate_cr", "revenue_year_ago_cr")


def upgrade() -> None:
    for name in _NUMBERS:
        op.add_column("results_calendar", sa.Column(name, sa.Numeric(16, 2), nullable=True))
    op.add_column("results_calendar", sa.Column("eps_analysts", sa.Integer(), nullable=True))
    op.add_column("results_calendar", sa.Column("revenue_analysts", sa.Integer(), nullable=True))
    op.add_column("results_calendar", sa.Column("estimate_on", sa.Date(), nullable=True))


def downgrade() -> None:
    for name in (*_NUMBERS, "eps_analysts", "revenue_analysts", "estimate_on"):
        op.drop_column("results_calendar", name)
