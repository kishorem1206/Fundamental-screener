"""Screener.in shareholding pattern — supplementary source alongside
Stage 3's NSE-sourced `shareholding` table (migration 0011), never merged
into it. Prompted by checking whether Screener.in's own promoter-holdings
section (app/ingestion/screener_shareholding_client.py, via openscreener's
Stock.shareholding_quarterly()/shareholding_yearly()) could extend or
replace the NSE source.

Findings (2026-09-13, live-tested on ADANIENT): Screener gives
promoter/FII/DII/public % and shareholder count, with materially deeper
history than NSE's current window (11 years yearly back to Mar 2017 vs
NSE's 2022-on; 12+ quarters) and a FII/DII split NSE's summary API doesn't
provide. But Screener's shareholding section has NO pledge % field at all
— confirmed absent from every row returned, and grepping openscreener's
entire source tree for "pledg" returned zero hits. Pledge tracking, the
single most governance-critical field, stays exclusively sourced from
NSE's XBRL filings (`shareholding.pledge_pct`). This table is additive
trend-depth/FII-DII context only, kept in its own table so it can never
silently outrank or blend with the pledge-bearing NSE row for the same
period.

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shareholding_screener",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_end", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),  # quarterly | yearly
        sa.Column("promoter_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("fii_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("dii_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("public_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("shareholder_count", sa.BigInteger(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "period_end", "frequency",
            name="shareholding_screener_company_period_freq_uq",
        ),
    )
    op.create_index("shareholding_screener_company_idx", "shareholding_screener", ["company_id", "period_end"])


def downgrade() -> None:
    op.drop_index("shareholding_screener_company_idx", "shareholding_screener")
    op.drop_table("shareholding_screener")
