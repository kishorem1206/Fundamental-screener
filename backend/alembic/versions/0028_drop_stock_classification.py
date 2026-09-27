"""Drop fa_stock_classification — retired 2026-09-17. It was a separate,
manually-synced ~1610-row shadow copy of the sector/industry/basic_industry/
macro_sector data `stocks` now carries directly (stocks was expanded to the
same ~1610-company universe from this table's own data, then this table's
two live callers — app/routes/screening.py and app/sectors/
classification_map.py's data source — were repointed at `stocks`). Single
source of truth from here on, no more manual sync scripts.

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("fa_stock_classification_sector_idx", "fa_stock_classification")
    op.drop_table("fa_stock_classification")


def downgrade() -> None:
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
