"""Results & Concall Highlights — arthneeti.com scrape (primary) with a
deterministic Python fallback (secondary) synthesized from our own
ConcallTopicSentiment/ManagementGuidance rows when arthneeti has no page
for a given company+quarter.

Revision ID: 0026
Revises: 0025
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "concall_highlights",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("transcript_id", sa.String(), sa.ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transcript_id", name="concall_highlights_transcript_uq"),
    )
    op.create_index("concall_highlights_company_idx", "concall_highlights", ["company_id"])


def downgrade() -> None:
    op.drop_index("concall_highlights_company_idx", "concall_highlights")
    op.drop_table("concall_highlights")
