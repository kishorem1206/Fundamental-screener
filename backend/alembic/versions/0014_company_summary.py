"""company_summary: Screener.in's summary()['about'] and ['key_points'] per
stock — free-text company description and (for many companies, e.g. TCS)
a revenue-mix breakdown, used both as MCP/API context and injected into the
HTML/PDF report's company overview section. Not a numeric metric, so it
doesn't belong in fa_metric_data_points — a simple one-row-per-company
cache, same shape as fa_bulk_metrics/analyst_consensus.

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_summary",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id", sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("key_points", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="SCREENER"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", name="company_summary_company_id_uq"),
    )


def downgrade() -> None:
    op.drop_table("company_summary")
