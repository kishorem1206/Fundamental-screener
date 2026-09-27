"""Quick-analysis (Yahoo-only) score table — separate from fa_company_scores
(full-pipeline scores) on purpose; the two methods are never merged.

Revision ID: 0030
Revises: 0029
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None

_SCORE_COLUMNS = ("overall", "growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation")


def upgrade() -> None:
    op.create_table(
        "fa_quick_scores",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("sector_framework", sa.String(), nullable=True),
        *[sa.Column(c, sa.Numeric(6, 2), nullable=True) for c in _SCORE_COLUMNS],
        sa.Column("overall_rating", sa.String(), nullable=True),
        sa.Column("valuation_view", sa.String(), nullable=True),
        sa.Column("weights", sa.JSON(), nullable=True),
        sa.Column("red_flags", sa.JSON(), nullable=True),
        sa.Column("refinement", sa.JSON(), nullable=True),
        sa.Column("latest_fy", sa.String(), nullable=True),
        sa.Column("method_version", sa.String(), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in _SCORE_COLUMNS:
        op.create_index(f"fa_quick_scores_{c}_idx", "fa_quick_scores", [c])


def downgrade() -> None:
    op.drop_table("fa_quick_scores")
