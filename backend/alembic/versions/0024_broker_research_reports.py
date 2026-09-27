"""Dated individual broker research-report history (Trendlyne, free
metadata table only — the underlying PDF text is login-gated and not
scraped). Distinct from analyst_consensus (a current-snapshot aggregate):
this is the actual history of who called what, when, and whether the
target was later hit.

Revision ID: 0024
Revises: 0023
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_research_reports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_date", sa.String(), nullable=False),
        sa.Column("broker_name", sa.String(), nullable=False),
        sa.Column("rating", sa.String(), nullable=True),
        sa.Column("target_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("ltp_at_capture", sa.Numeric(12, 2), nullable=True),
        sa.Column("price_at_reco", sa.Numeric(12, 2), nullable=True),
        sa.Column("change_since_reco_pct", sa.Numeric(8, 2), nullable=True),
        sa.Column("upside_pct", sa.Numeric(8, 2), nullable=True),
        sa.Column("reco_changed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("target_changed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("report_url", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="TRENDLYNE"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "report_date", "broker_name",
            name="broker_research_reports_company_date_broker_uq",
        ),
    )
    op.create_index("broker_research_reports_company_idx", "broker_research_reports", ["company_id"])


def downgrade() -> None:
    op.drop_index("broker_research_reports_company_idx", "broker_research_reports")
    op.drop_table("broker_research_reports")
