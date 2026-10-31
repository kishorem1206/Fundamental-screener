"""Who started an analysis: the app or the scheduled job.

Revision ID: 0050
Revises: 0049
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fa_analyses", sa.Column("started_by", sa.String(), nullable=False, server_default="app"))


def downgrade() -> None:
    op.drop_column("fa_analyses", "started_by")
