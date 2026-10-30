"""Earnings estimate snapshots; market news from publisher feeds.

Revision ID: 0047
Revises: 0046
Create Date: 2026-10-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "estimate_snapshots",
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("on_date", sa.Date(), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("eps_now", sa.Numeric(14, 4), nullable=False),
        sa.Column("eps_30d_ago", sa.Numeric(14, 4), nullable=True),
        sa.Column("eps_90d_ago", sa.Numeric(14, 4), nullable=True),
        sa.Column("revision_30d_pct", sa.Numeric(8, 2), nullable=True),
        sa.Column("revision_90d_pct", sa.Numeric(8, 2), nullable=True),
        sa.Column("up_30d", sa.Integer(), nullable=True),
        sa.Column("down_30d", sa.Integer(), nullable=True),
        sa.Column("analysts", sa.Integer(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("stock_id", "on_date"),
    )
    op.create_table(
        "market_news",
        sa.Column("url", sa.String(), primary_key=True),
        sa.Column("publisher", sa.String(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("symbols", sa.JSON(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_market_news_published_at", "market_news", ["published_at"])


def downgrade() -> None:
    op.drop_table("market_news")
    op.drop_table("estimate_snapshots")
