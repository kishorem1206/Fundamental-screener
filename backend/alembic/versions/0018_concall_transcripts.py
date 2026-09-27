"""Concall Intelligence System, Stage C0 — transcript filing metadata.
Raw PDF bytes live in the existing documents/MinIO storage (Architecture v2
Stage 7); this table is the transcript-specific layer on top (quarter, call
date, management participants), one row per genuine transcript filing.

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "concall_transcripts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("quarter", sa.String(), nullable=True),
        sa.Column("call_date", sa.String(), nullable=True),
        sa.Column("filing_date", sa.String(), nullable=True),
        sa.Column("management_participants", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="NSE"),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("extraction_status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("concall_transcripts_company_idx", "concall_transcripts", ["company_id", "call_date"])


def downgrade() -> None:
    op.drop_index("concall_transcripts_company_idx", "concall_transcripts")
    op.drop_table("concall_transcripts")
