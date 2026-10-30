"""Largest penalty named in a SEBI order's operative part.

Revision ID: 0045
Revises: 0044
Create Date: 2026-10-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sebi_orders", sa.Column("penalty_rs", sa.Numeric(18, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("sebi_orders", "penalty_rs")
