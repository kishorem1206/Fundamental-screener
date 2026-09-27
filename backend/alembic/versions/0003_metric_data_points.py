"""fa_metric_data_points: provenance ledger for non-yfinance sector metrics (banking pilot)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fa_metric_data_points",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id",
            sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric_key", sa.String(), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(20, 6), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        # RBI | NSE_XBRL | BSE_XBRL | COMPANY_IR | SCREENER | MONEYCONTROL | CALCULATED | MANUAL
        sa.Column("source_tier", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("source_document", sa.String(), nullable=True),
        sa.Column("source_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reported_or_calculated", sa.String(), nullable=False),
        # REPORTED | CALCULATED | DERIVED | ESTIMATED
        sa.Column("calculation_formula", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=False),
        # HIGH | MEDIUM | LOW
        sa.Column("raw_reported_value", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "fa_metric_points_company_metric_idx",
        "fa_metric_data_points",
        ["company_id", "metric_key"],
    )
    op.create_index(
        "fa_metric_points_company_metric_period_idx",
        "fa_metric_data_points",
        ["company_id", "metric_key", "period"],
    )


def downgrade() -> None:
    op.drop_index("fa_metric_points_company_metric_period_idx", "fa_metric_data_points")
    op.drop_index("fa_metric_points_company_metric_idx", "fa_metric_data_points")
    op.drop_table("fa_metric_data_points")
