"""NSE corporate actions (from NSE's MCP server).

Revision ID: 0042
Revises: 0041
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nse_corporate_actions",
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("adjustment_factor", sa.Numeric(14, 8), nullable=False, server_default="1"),
        sa.Column("dividend_per_share", sa.Numeric(14, 4), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("stock_id", "ex_date", "purpose"),
    )


def downgrade() -> None:
    op.drop_table("nse_corporate_actions")
