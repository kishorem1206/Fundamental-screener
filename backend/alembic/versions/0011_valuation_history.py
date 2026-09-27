"""valuation_history: Architecture v2 Stage 4 — historical P/E and P/B per
fiscal year, computed from real historical prices (not the "current price /
historical EPS" proxy app/calculations/engine.py's implied_pe_series()
already had). Each year's EPS/book-value-per-share is taken from whichever
source actually has it for that year (Screener.in's profit_loss()/
balance_sheet(), ~11 years deep; yfinance's annual financials as a filler
for whatever Screener didn't have or wasn't available, ~4-5 years deep) —
per-field fallback, not a single hard source pick.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "valuation_history",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id", sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("period_end", sa.String(), nullable=False),
        sa.Column("eps", sa.Numeric(14, 4), nullable=True),
        sa.Column("eps_source", sa.String(), nullable=True),  # SCREENER | YFINANCE
        sa.Column("price", sa.Numeric(14, 4), nullable=True),
        sa.Column("price_date", sa.String(), nullable=True),  # actual matched trading date, may differ from period_end
        sa.Column("pe", sa.Numeric(10, 2), nullable=True),
        sa.Column("book_value_per_share", sa.Numeric(14, 4), nullable=True),
        sa.Column("bvps_source", sa.String(), nullable=True),
        sa.Column("pb", sa.Numeric(10, 2), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period_end", name="valuation_history_company_period_uq"),
    )
    op.create_index("valuation_history_company_idx", "valuation_history", ["company_id", "period_end"])


def downgrade() -> None:
    op.drop_index("valuation_history_company_idx", "valuation_history")
    op.drop_table("valuation_history")
