"""SEBI orders, their company matches, and credit ratings (app/risk/).

Revision ID: 0043
Revises: 0042
Create Date: 2026-10-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sebi_orders",
        sa.Column("url", sa.String(), primary_key=True),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("pdf_url", sa.String(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("outcome_excerpt", sa.Text(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sebi_orders_order_date", "sebi_orders", ["order_date"])
    op.create_table(
        "sebi_order_matches",
        sa.Column("order_url", sa.String(), sa.ForeignKey("sebi_orders.url", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("matched_name", sa.String(), nullable=False),
        sa.Column("company_in_operative", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("order_url", "stock_id"),
    )
    op.create_index("ix_sebi_order_matches_stock_id", "sebi_order_matches", ["stock_id"])
    op.create_table(
        "credit_ratings",
        sa.Column("filing_url", sa.String(), primary_key=True),
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("announced_on", sa.Date(), nullable=False),
        sa.Column("agency", sa.String(), nullable=True),
        sa.Column("instrument", sa.String(), nullable=True),
        sa.Column("rating", sa.String(), nullable=True),
        sa.Column("short_term", sa.String(), nullable=True),
        sa.Column("outlook", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("previous_rating", sa.String(), nullable=True),
        sa.Column("previous_outlook", sa.String(), nullable=True),
        sa.Column("rationale_url", sa.String(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("parsed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_credit_ratings_stock_id", "credit_ratings", ["stock_id"])


def downgrade() -> None:
    op.drop_table("credit_ratings")
    op.drop_table("sebi_order_matches")
    op.drop_table("sebi_orders")
