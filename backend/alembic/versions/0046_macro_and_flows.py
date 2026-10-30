"""Macro and market series; FPI flows by sector (app/macro/).

Revision ID: 0046
Revises: 0045
Create Date: 2026-10-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "macro_points",
        sa.Column("series", sa.String(), nullable=False),
        sa.Column("on_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(20, 4), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("series", "on_date"),
    )
    op.create_table(
        "fpi_sector_flows",
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("sector", sa.String(), nullable=False),
        sa.Column("net_cr", sa.Numeric(16, 2), nullable=True),
        sa.Column("auc_cr", sa.Numeric(16, 2), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("period_end", "sector"),
    )


def downgrade() -> None:
    op.drop_table("fpi_sector_flows")
    op.drop_table("macro_points")
