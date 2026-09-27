"""Deep Research System, Stage R1 — per-segment revenue history, one row
per company+segment+fiscal_year. Sourced from TradingView's
financials-segments page (free, no login wall) — nothing in this codebase
extracted business-segment-level revenue before this.

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_segments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("segment_name", sa.String(), nullable=False),
        sa.Column("fiscal_year", sa.String(), nullable=False),
        sa.Column("revenue", sa.Numeric(20, 2), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="INR"),
        sa.Column("source", sa.String(), nullable=False, server_default="TRADINGVIEW"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "segment_name", "fiscal_year",
            name="business_segments_company_segment_year_uq",
        ),
    )
    op.create_index("business_segments_company_idx", "business_segments", ["company_id"])


def downgrade() -> None:
    op.drop_index("business_segments_company_idx", "business_segments")
    op.drop_table("business_segments")
