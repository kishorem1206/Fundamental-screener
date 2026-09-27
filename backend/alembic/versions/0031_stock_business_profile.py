"""Yahoo business profile per stock (peer selection by business similarity).

Revision ID: 0031
Revises: 0030
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fa_stock_business_profile",
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("yahoo_industry", sa.String(), nullable=True),
        sa.Column("yahoo_sector", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("fa_stock_business_profile")
