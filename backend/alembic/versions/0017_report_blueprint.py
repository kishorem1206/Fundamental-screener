"""Report Blueprint column — Stage L1 of the Llama Report Interpretation
Architecture (`Sector md files/Summary.md`). Stored additively alongside
the existing `ai_analysis` column: the new modular, local-Llama-generated
blueprint (`{report: {...}, sections: [...]}`, see
`app/interpretation/llama_interpreter.py`) never replaces or modifies
`ai_analysis` in this stage — if the new pipeline produces nothing (Ollama
down, empty result), `ai_analysis`'s narrative fields remain the rendered
fallback, so nothing regresses.

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fa_analyses", sa.Column("report_blueprint", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("fa_analyses", "report_blueprint")
