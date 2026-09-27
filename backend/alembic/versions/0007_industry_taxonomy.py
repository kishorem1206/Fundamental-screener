"""fa_industry_taxonomy: NSE's official Industry Classification Structure
reference data (Macro-economic Sector / Sector / Industry / Basic Industry,
with each basic industry's definition) — the taxonomy itself, not any
company's placement within it (see fa_stock_classification for that).
Source: NSE Indices Ltd., "Industry Classification Structure", July 2023.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fa_industry_taxonomy",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("mes_code", sa.String(), nullable=False),          # e.g. IN01
        sa.Column("macro_sector", sa.String(), nullable=False),      # e.g. Commodities
        sa.Column("sect_code", sa.String(), nullable=False),         # e.g. IN0101
        sa.Column("sector", sa.String(), nullable=False),            # e.g. Chemicals
        sa.Column("ind_code", sa.String(), nullable=False),          # e.g. IN010101
        sa.Column("industry", sa.String(), nullable=False),          # e.g. Chemicals & Petrochemicals
        sa.Column("basic_ind_code", sa.String(), nullable=False),    # e.g. IN010101001
        sa.Column("basic_industry", sa.String(), nullable=False),    # e.g. Commodity Chemicals
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="NSE_INDICES"),
        sa.Column("source_document", sa.String(), nullable=False,
                  server_default="NSE Indices Ltd. - Industry Classification Structure, July 2023"),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("basic_ind_code", name="fa_industry_taxonomy_basic_ind_code_uq"),
    )
    op.create_index(
        "fa_industry_taxonomy_hierarchy_idx",
        "fa_industry_taxonomy",
        ["macro_sector", "sector", "industry", "basic_industry"],
    )


def downgrade() -> None:
    op.drop_index("fa_industry_taxonomy_hierarchy_idx", "fa_industry_taxonomy")
    op.drop_table("fa_industry_taxonomy")
