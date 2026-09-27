"""stocks.market_cap_rank — rank by market cap (1 = largest); tiers are rank-based:
1-100 LARGE, 101-250 MID, 251+ SMALL.

Revision ID: 0032
Revises: 0031
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stocks", sa.Column("market_cap_rank", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("stocks", "market_cap_rank")
