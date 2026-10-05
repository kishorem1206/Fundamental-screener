"""Recent IPO tracking — `fa_ipo_issues` (raw NSE past/upcoming-issue data,
every security type) + `stocks.ipo_listing_date` (set only for the mainboard
EQ/BE issues actually promoted into the stocks universe — see
app/ingestion/nse_ipo_client.py).

Revision ID: 0034
Revises: 0033
Create Date: 2026-09-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stocks", sa.Column("ipo_listing_date", sa.Date(), nullable=True))

    op.create_table(
        "fa_ipo_issues",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("security_type", sa.String(), nullable=False),
        sa.Column("issue_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("price_range_low", sa.Numeric(12, 2), nullable=True),
        sa.Column("price_range_high", sa.Numeric(12, 2), nullable=True),
        sa.Column("issue_start_date", sa.Date(), nullable=True),
        sa.Column("issue_end_date", sa.Date(), nullable=True),
        sa.Column("listing_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "issue_start_date", name="uq_ipo_issue_symbol_start"),
    )
    op.create_index("ix_fa_ipo_issues_symbol", "fa_ipo_issues", ["symbol"])
    op.create_index("ix_fa_ipo_issues_listing_date", "fa_ipo_issues", ["listing_date"])


def downgrade() -> None:
    op.drop_index("ix_fa_ipo_issues_listing_date", table_name="fa_ipo_issues")
    op.drop_index("ix_fa_ipo_issues_symbol", table_name="fa_ipo_issues")
    op.drop_table("fa_ipo_issues")
    op.drop_column("stocks", "ipo_listing_date")
