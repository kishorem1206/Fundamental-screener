"""Weinstein stage screener: latest read, weekly history, threshold overrides, watchlist.

Revision ID: 0052
Revises: 0051
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None


def _stock() -> sa.Column:
    return sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), primary_key=True)


def upgrade() -> None:
    n = lambda p, s: sa.Numeric(p, s)
    op.create_table(
        "stage_scores", _stock(),
        sa.Column("as_of", sa.Date(), nullable=False), sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("provisional", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stage", sa.SmallInteger()), sa.Column("sub_stage", sa.String()), sa.Column("confidence", n(5, 1)), sa.Column("reason", sa.String()),
        sa.Column("prev_stage", sa.SmallInteger()), sa.Column("stage_since", sa.Date()), sa.Column("weeks_in_stage", sa.Integer()), sa.Column("next_stage", sa.SmallInteger()),
        sa.Column("close", n(16, 2)), sa.Column("sma30", n(16, 2)), sa.Column("sma10", n(16, 2)), sa.Column("sma_slope_pct", n(8, 2)), sa.Column("sma_distance_pct", n(8, 2)),
        sa.Column("rs", n(8, 2)), sa.Column("rs_change", n(8, 2)), sa.Column("rs_improving", sa.Boolean()), sa.Column("rsi", n(6, 2)), sa.Column("volume_ratio", n(8, 2)),
        sa.Column("high_52w", n(16, 2)), sa.Column("low_52w", n(16, 2)), sa.Column("high_distance_pct", n(8, 2)), sa.Column("weeks_above_sma", sa.Integer()),
        sa.Column("resistance", n(16, 2)), sa.Column("support", n(16, 2)),
        sa.Column("opportunity", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("near_breakout", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("detail", sa.JSON()), sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_stage_scores_stage", "stage_scores", ["stage"])
    op.create_index("ix_stage_scores_opportunity", "stage_scores", ["opportunity"])
    op.create_table(
        "stage_history", _stock(), sa.Column("week_end", sa.Date(), primary_key=True),
        sa.Column("open", n(16, 2), nullable=False), sa.Column("high", n(16, 2), nullable=False), sa.Column("low", n(16, 2), nullable=False), sa.Column("close", n(16, 2), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False), sa.Column("sma30", n(16, 2)), sa.Column("sma10", n(16, 2)), sa.Column("rs", n(8, 2)),
        sa.Column("stage", sa.SmallInteger()), sa.Column("sub_stage", sa.String()), sa.Column("confidence", n(5, 1)), sa.Column("event", sa.String()),
        sa.Column("provisional", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_stage_history_week_end", "stage_history", ["week_end"])
    op.create_table("stage_thresholds", sa.Column("key", sa.String(), primary_key=True), sa.Column("value", n(10, 3), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("stage_watchlist", _stock(), sa.Column("added_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    for name in ("stage_watchlist", "stage_thresholds", "stage_history", "stage_scores"):
        op.drop_table(name)
