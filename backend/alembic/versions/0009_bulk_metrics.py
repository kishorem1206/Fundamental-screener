"""fa_bulk_metrics: Architecture v2 Stage 2 — a lightweight, whole-universe
cache of compute_metrics() output (deterministic, yfinance-derived, no LLM)
per stock, refreshed by a bounded/resumable batch job
(app/screening/bulk_metrics.py). Distinct from fa_analyses (the heavyweight
13-stage pipeline result, currently only ~15 stocks) and fa_metric_data_points
(the multi-source provenance ledger for operational/banking-specific
metrics) — this table exists purely so the declarative screening engine
(app/screening/engine.py) has real breadth to run rules against.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fa_bulk_metrics",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "stock_id",
            sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", name="fa_bulk_metrics_stock_id_uq"),
    )
    op.create_index("fa_bulk_metrics_stock_idx", "fa_bulk_metrics", ["stock_id"])


def downgrade() -> None:
    op.drop_index("fa_bulk_metrics_stock_idx", "fa_bulk_metrics")
    op.drop_table("fa_bulk_metrics")
