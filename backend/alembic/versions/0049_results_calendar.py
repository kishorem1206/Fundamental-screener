"""NSE results calendar, driving re-reads the day after results (app/results/).

Revision ID: 0049
Revises: 0048
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "results_calendar",
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("board_date", sa.Date(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quarter", sa.String(), nullable=True),
        sa.Column("last_tried_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("done_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("stock_id", "board_date"),
    )
    op.create_index("ix_results_calendar_board_date", "results_calendar", ["board_date"])
    op.create_index("ix_results_calendar_status", "results_calendar", ["status"])


def downgrade() -> None:
    op.drop_table("results_calendar")
