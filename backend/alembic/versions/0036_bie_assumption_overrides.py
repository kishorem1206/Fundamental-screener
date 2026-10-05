"""Business Intelligence Engine, phase 4.5 — analyst overrides of model
assumptions, kept as an append-only history.

Revision ID: 0036
Revises: 0035
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bie_assumption_overrides",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("value", sa.Numeric(20, 6), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_url", sa.String(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=False, server_default="MEDIUM"),
        sa.Column("created_by", sa.String(), nullable=False, server_default="analyst"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("bie_overrides_company_idx", "bie_assumption_overrides", ["company_id", "superseded_at"])


def downgrade() -> None:
    op.drop_index("bie_overrides_company_idx", table_name="bie_assumption_overrides")
    op.drop_table("bie_assumption_overrides")
