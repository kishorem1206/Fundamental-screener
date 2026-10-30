"""AMFI scheme NAVs by ISIN (app/portfolio/amfi.py).

Revision ID: 0044
Revises: 0043
Create Date: 2026-10-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "amfi_navs",
        sa.Column("isin", sa.String(), primary_key=True),
        sa.Column("scheme_code", sa.String(), nullable=False),
        sa.Column("scheme_name", sa.String(), nullable=False),
        sa.Column("fund_house", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("asset_class", sa.String(), nullable=False),
        sa.Column("class_basis", sa.String(), nullable=False),
        sa.Column("nav", sa.Numeric(20, 4), nullable=True),
        sa.Column("nav_date", sa.Date(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("amfi_navs")
