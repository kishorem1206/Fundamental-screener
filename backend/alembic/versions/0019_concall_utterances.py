"""Concall Intelligence System, Stage C1 — parsed speaker turns.
Deterministic regex parsing (app/ingestion/concall_parser.py) of the PDF
already stored in Stage C0, one row per speaker turn.

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "concall_utterances",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("transcript_id", sa.String(), sa.ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("speaker_name", sa.String(), nullable=False),
        sa.Column("speaker_role", sa.String(), nullable=False),
        sa.Column("section", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("concall_utterances_transcript_idx", "concall_utterances", ["transcript_id", "sequence"])


def downgrade() -> None:
    op.drop_index("concall_utterances_transcript_idx", "concall_utterances")
    op.drop_table("concall_utterances")
