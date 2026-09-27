"""Company score snapshot table — one row per stock holding its six category
scores + overall, upserted after every completed analysis, so the analysed
universe can be filtered/sorted by any score without re-running or
re-reading each analysis's JSON.

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

_SCORE_COLUMNS = ("overall", "growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation")


def upgrade() -> None:
    op.create_table(
        "fa_company_scores",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("analysis_id", sa.String(), nullable=True),
        *[sa.Column(c, sa.Numeric(6, 2), nullable=True) for c in _SCORE_COLUMNS],
        sa.Column("overall_rating", sa.String(), nullable=True),
        sa.Column("valuation_view", sa.String(), nullable=True),
        sa.Column("weights", sa.JSON(), nullable=True),
        sa.Column("red_flags", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_quarter_end", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in _SCORE_COLUMNS:
        op.create_index(f"fa_company_scores_{c}_idx", "fa_company_scores", [c])


def downgrade() -> None:
    op.drop_table("fa_company_scores")
