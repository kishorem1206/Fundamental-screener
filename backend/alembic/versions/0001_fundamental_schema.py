"""fundamental analysis schema

Revision ID: 0001
Revises:
Create Date: 2026-08-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fa_analyses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("stock_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="QUEUED"),
        sa.Column("current_stage", sa.String(), nullable=True),
        sa.Column("stage_progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("data_quality_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ai_rating", sa.String(), nullable=True),
        sa.Column("valuation_rating", sa.String(), nullable=True),
        sa.Column("company_info", sa.JSON(), nullable=True),
        sa.Column("financial_data", sa.JSON(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("metric_validations", sa.JSON(), nullable=True),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("sector_analysis", sa.JSON(), nullable=True),
        sa.Column("peers", sa.JSON(), nullable=True),
        sa.Column("risks", sa.JSON(), nullable=True),
        sa.Column("catalysts", sa.JSON(), nullable=True),
        sa.Column("ai_analysis", sa.JSON(), nullable=True),
        sa.Column("report_path", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("fa_analyses_stock_idx", "fa_analyses", ["stock_id"])
    op.create_index("fa_analyses_status_idx", "fa_analyses", ["status"])
    op.create_index("fa_analyses_created_idx", "fa_analyses", ["created_at"])

    op.create_table(
        "fa_analysis_stages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("analysis_id", sa.String(), sa.ForeignKey("fa_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("fa_stages_analysis_idx", "fa_analysis_stages", ["analysis_id"])


def downgrade() -> None:
    op.drop_table("fa_analysis_stages")
    op.drop_table("fa_analyses")
