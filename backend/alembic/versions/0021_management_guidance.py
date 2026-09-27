"""Concall Intelligence System, Stage C3 — extracted guidance statements.
Local-Llama-extracted, restricted to management-role utterances only.
status/change_midpoint are deterministic Python comparisons against
previous_guidance_id, never LLM-assigned.

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "management_guidance",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transcript_id", sa.String(), sa.ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("utterance_id", sa.String(), sa.ForeignKey("concall_utterances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quarter", sa.String(), nullable=True),
        sa.Column("speaker_role", sa.String(), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("period", sa.String(), nullable=True),
        sa.Column("guidance_type", sa.String(), nullable=False),
        sa.Column("target_low", sa.Numeric(20, 4), nullable=True),
        sa.Column("target_high", sa.Numeric(20, 4), nullable=True),
        sa.Column("target_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),
        sa.Column("certainty", sa.String(), nullable=True),
        sa.Column("conditional", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(), nullable=False, server_default="NEW"),
        sa.Column("previous_guidance_id", sa.String(), sa.ForeignKey("management_guidance.id", ondelete="SET NULL"), nullable=True),
        sa.Column("change_midpoint", sa.Numeric(20, 4), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("management_guidance_company_metric_idx", "management_guidance", ["company_id", "metric", "period"])


def downgrade() -> None:
    op.drop_index("management_guidance_company_metric_idx", "management_guidance")
    op.drop_table("management_guidance")
