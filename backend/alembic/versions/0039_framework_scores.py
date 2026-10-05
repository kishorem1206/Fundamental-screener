"""Stock Quality framework scores — one row per stock per day per basis.

Revision ID: 0039
Revises: 0038
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None

_SCORES = ("quality", "business_quality", "fundamental", "quantitative", "relative_strength", "technical", "valuation")
_LABELS = ("valuation_view", "trend", "classification", "action", "sector_framework", "latest_fy")


def upgrade() -> None:
    op.create_table(
        "fw_scores",
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("basis", sa.String(), nullable=False),
        *[sa.Column(c, sa.Numeric(6, 2), nullable=True) for c in _SCORES],
        *[sa.Column(c, sa.String(), nullable=True) for c in _LABELS],
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("reconstructed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("stock_id", "as_of", "basis"),
    )
    op.create_index("fw_scores_as_of_idx", "fw_scores", ["as_of"])
    op.create_index("fw_scores_fundamental_idx", "fw_scores", ["fundamental"])
    op.create_index("fw_scores_quality_idx", "fw_scores", ["quality"])


def downgrade() -> None:
    op.drop_table("fw_scores")
