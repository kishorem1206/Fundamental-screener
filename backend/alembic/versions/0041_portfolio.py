"""Portfolio holdings and settings (framework sections 12-14).

Revision ID: 0041
Revises: 0040
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pf_holdings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("symbol", sa.String(), nullable=True),
        sa.Column("isin", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("asset_class", sa.String(), nullable=False),
        sa.Column("class_basis", sa.String(), nullable=True),
        sa.Column("quantity", sa.Numeric(20, 4), nullable=True),
        sa.Column("avg_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("last_price", sa.Numeric(20, 4), nullable=True),
        sa.Column("value", sa.Numeric(20, 2), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=True),
    )
    op.create_index("pf_holdings_source_idx", "pf_holdings", ["source"])
    op.create_table(
        "pf_settings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("pf_settings")
    op.drop_table("pf_holdings")
