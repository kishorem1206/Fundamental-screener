"""fa_stock_classification: 4-level sector classification (macro_sector /
sector / industry / basic_industry) sourced from Screener.in per-company
pages, for stocks not covered — or only partially covered — by the shared
read-only `stocks` table (macro_sector 50% populated, basic_industry ~0%
across the active universe).

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fa_stock_classification",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("market_cap_cr", sa.Numeric(20, 2), nullable=True),
        sa.Column("macro_sector", sa.String(), nullable=True),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("basic_industry", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="SCREENER"),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", name="fa_stock_classification_symbol_uq"),
    )
    op.create_index(
        "fa_stock_classification_sector_idx",
        "fa_stock_classification",
        ["sector", "industry", "basic_industry"],
    )


def downgrade() -> None:
    op.drop_index("fa_stock_classification_sector_idx", "fa_stock_classification")
    op.drop_table("fa_stock_classification")
