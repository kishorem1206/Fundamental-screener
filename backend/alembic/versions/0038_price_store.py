"""Price store — daily bars for every stock and every NSE index.

Revision ID: 0038
Revises: 0037
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_bars_daily",
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bar_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(16, 4), nullable=True),
        sa.Column("high", sa.Numeric(16, 4), nullable=True),
        sa.Column("low", sa.Numeric(16, 4), nullable=True),
        sa.Column("close", sa.Numeric(16, 4), nullable=False),
        sa.Column("adj_close", sa.Numeric(16, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("stock_id", "bar_date"),
    )
    op.create_index("price_bars_daily_date_idx", "price_bars_daily", ["bar_date"])

    op.create_table(
        "index_bars_daily",
        sa.Column("index_name", sa.String(), nullable=False),
        sa.Column("bar_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(16, 4), nullable=True),
        sa.Column("high", sa.Numeric(16, 4), nullable=True),
        sa.Column("low", sa.Numeric(16, 4), nullable=True),
        sa.Column("close", sa.Numeric(16, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("turnover_cr", sa.Numeric(18, 2), nullable=True),
        sa.Column("pe", sa.Numeric(10, 2), nullable=True),
        sa.Column("pb", sa.Numeric(10, 2), nullable=True),
        sa.Column("div_yield", sa.Numeric(8, 2), nullable=True),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("index_name", "bar_date"),
    )
    op.create_index("index_bars_daily_date_idx", "index_bars_daily", ["bar_date"])


def downgrade() -> None:
    op.drop_table("index_bars_daily")
    op.drop_table("price_bars_daily")
