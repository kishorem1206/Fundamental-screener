"""agent_runs table, sequence-based IDs, composite index, model_version column

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Sequential analysis counter (avoids COUNT race condition) ──────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS fa_analysis_seq START 1 INCREMENT 1")

    # ── Extra columns on fa_analyses ───────────────────────────────────────────
    op.add_column("fa_analyses", sa.Column("model_version", sa.String(), nullable=True))
    op.add_column("fa_analyses", sa.Column("prompt_version", sa.String(), nullable=True))
    op.add_column("fa_analyses", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))

    # Composite index for "latest analysis per stock" query
    op.create_index(
        "fa_analyses_stock_created_idx",
        "fa_analyses",
        ["stock_id", sa.text("created_at DESC")],
    )

    # ── fa_agent_runs ──────────────────────────────────────────────────────────
    op.create_table(
        "fa_agent_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "analysis_id",
            sa.String(),
            sa.ForeignKey("fa_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage_name", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="RUNNING"),
        # RUNNING | COMPLETED | FAILED | SKIPPED
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("fa_agent_runs_analysis_idx", "fa_agent_runs", ["analysis_id"])
    op.create_index("fa_agent_runs_stage_idx", "fa_agent_runs", ["analysis_id", "stage_name"])


def downgrade() -> None:
    op.drop_table("fa_agent_runs")
    op.drop_index("fa_analyses_stock_created_idx", "fa_analyses")
    op.drop_column("fa_analyses", "cancelled_at")
    op.drop_column("fa_analyses", "prompt_version")
    op.drop_column("fa_analyses", "model_version")
    op.execute("DROP SEQUENCE IF EXISTS fa_analysis_seq")
