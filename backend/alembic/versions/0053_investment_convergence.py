"""Investment convergence on the Combined Score page: latest read, daily history, settings.

Revision ID: 0053
Revises: 0052
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None


def _stock() -> sa.Column:
    return sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), primary_key=True)


def upgrade() -> None:
    n = lambda p, s: sa.Numeric(p, s)
    op.create_table(
        "convergence_scores", _stock(), sa.Column("as_of", sa.Date(), nullable=False), sa.Column("method_version", sa.String(), nullable=False),
        sa.Column("combined", n(5, 1)), sa.Column("classification", sa.String(), nullable=False), sa.Column("confidence", n(5, 1), nullable=False),
        sa.Column("confidence_label", sa.String(), nullable=False), sa.Column("risk_reward", n(10, 2)), sa.Column("upside_pct", n(10, 1)), sa.Column("downside_pct", n(10, 1)),
        sa.Column("target", n(16, 2)), sa.Column("invalidation", n(16, 2)), sa.Column("detail", sa.JSON()), sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_convergence_scores_combined", "convergence_scores", ["combined"])
    op.create_index("ix_convergence_scores_classification", "convergence_scores", ["classification"])
    op.create_table(
        "convergence_history", _stock(), sa.Column("as_of", sa.Date(), primary_key=True), sa.Column("method_version", sa.String(), nullable=False),
        sa.Column("quality", n(6, 2)), sa.Column("fundamental", n(6, 2)), sa.Column("technical", n(6, 2)), sa.Column("relative_strength", n(6, 2)), sa.Column("valuation", n(6, 2)),
        sa.Column("stage", sa.SmallInteger()), sa.Column("sub_stage", sa.String()), sa.Column("risk_reward", n(10, 2)), sa.Column("combined", n(5, 1)), sa.Column("classification", sa.String(), nullable=False))
    op.create_index("ix_convergence_history_as_of", "convergence_history", ["as_of"])
    op.create_table("convergence_settings", sa.Column("key", sa.String(), primary_key=True), sa.Column("value", n(10, 3), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    for name in ("convergence_settings", "convergence_history", "convergence_scores"):
        op.drop_table(name)
