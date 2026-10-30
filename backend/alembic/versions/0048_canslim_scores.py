"""CANSLIM scores, one row a stock (app/canslim/).

Revision ID: 0048
Revises: 0047
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    cols = [sa.Column(x, sa.Numeric(5, 1), nullable=True) for x in ("c", "a", "n", "s", "l", "i", "m")]
    op.create_table(
        "canslim_scores",
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("as_of", sa.Date(), nullable=False),
        *cols,
        sa.Column("letters", sa.Integer(), nullable=False),
        sa.Column("canslim", sa.Numeric(5, 1), nullable=True),
        sa.Column("peer_quality", sa.Numeric(5, 1), nullable=True),
        sa.Column("combined", sa.Numeric(5, 1), nullable=True),
        sa.Column("basis", sa.String(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_canslim_scores_canslim", "canslim_scores", ["canslim"])


def downgrade() -> None:
    op.drop_table("canslim_scores")
