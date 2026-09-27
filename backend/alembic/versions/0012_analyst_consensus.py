"""analyst_consensus: third-party analyst sentiment/target-price snapshots
(e.g. IndMoney's aggregated Street view — 39 analysts, BUY, target ₹978).

Deliberately NOT part of fa_metric_data_points: that table holds FACTS
(GNPA, CASA, CAR...) resolved across sources by tier/confidence: this is a
single external OPINION snapshot, not something to cross-validate or blend
into our own deterministic scoring — per explicit instruction, analyst
consensus must never become a concrete source of truth this platform's own
analysis relies on. Every read of this table must present it as external
context, not as an input to compute_scores()/compute_sector_score() or the
AI rating.

Also architecturally different from every other ingestion table in this
project: the backend has no direct HTTP path to IndMoney (only reachable
via the MCP connector inside a Claude session, not a public API this
service can call autonomously) — so rows here are written by an agent
session that fetched the data via that MCP tool and POSTed it in, not by a
backend batch job like every other source.

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analyst_consensus",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id", sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("num_analysts", sa.Integer(), nullable=True),
        sa.Column("sentiment", sa.String(), nullable=True),  # BUY | HOLD | SELL, as reported
        sa.Column("buy_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("hold_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("sell_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("target_price_mean", sa.Numeric(12, 2), nullable=True),
        sa.Column("target_price_low", sa.Numeric(12, 2), nullable=True),
        sa.Column("target_price_high", sa.Numeric(12, 2), nullable=True),
        sa.Column("price_at_capture", sa.Numeric(12, 2), nullable=True),
        sa.Column("implied_upside_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="INDMONEY"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "source", name="analyst_consensus_company_source_uq"),
    )
    op.create_index("analyst_consensus_company_idx", "analyst_consensus", ["company_id"])


def downgrade() -> None:
    op.drop_index("analyst_consensus_company_idx", "analyst_consensus")
    op.drop_table("analyst_consensus")
