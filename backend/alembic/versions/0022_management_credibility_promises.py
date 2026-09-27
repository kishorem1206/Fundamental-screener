"""Concall Intelligence System, Stage C4 — guidance consistency tracking
and promise tracking. management_credibility is a deterministic Python
aggregation of ManagementGuidance.status history (never LLM-scored);
management_promises is populated from already-extracted qualitative
guidance rows, no new LLM call.

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "management_credibility",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("guidance_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("upgraded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("downgraded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reiterated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_status", sa.String(), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "metric", name="management_credibility_company_metric_uq"),
    )

    op.create_table(
        "management_promises",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guidance_id", sa.String(), sa.ForeignKey("management_guidance.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("promise", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("target_date", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("management_promises_company_idx", "management_promises", ["company_id"])


def downgrade() -> None:
    op.drop_index("management_promises_company_idx", "management_promises")
    op.drop_table("management_promises")
    op.drop_table("management_credibility")
