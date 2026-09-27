"""fa_metric_data_points: add statement_type (STANDALONE/CONSOLIDATED) so
both can be stored and resolved separately instead of one silently
overwriting/competing with the other

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fa_metric_data_points",
        sa.Column("statement_type", sa.String(), nullable=False, server_default="STANDALONE"),
    )
    # Every row ingested so far (BSE quarterly filings, NSE annual reports) is
    # standalone — both extraction prompts explicitly say "standalone
    # results, not consolidated" — so the server_default backfills existing
    # rows correctly, not just new ones.
    op.drop_index("fa_metric_points_company_metric_idx", table_name="fa_metric_data_points")
    op.drop_index("fa_metric_points_company_metric_period_idx", table_name="fa_metric_data_points")
    op.create_index(
        "fa_metric_points_company_metric_idx",
        "fa_metric_data_points",
        ["company_id", "metric_key", "statement_type"],
    )
    op.create_index(
        "fa_metric_points_company_metric_period_idx",
        "fa_metric_data_points",
        ["company_id", "metric_key", "period", "statement_type"],
    )


def downgrade() -> None:
    op.drop_index("fa_metric_points_company_metric_period_idx", table_name="fa_metric_data_points")
    op.drop_index("fa_metric_points_company_metric_idx", table_name="fa_metric_data_points")
    op.create_index(
        "fa_metric_points_company_metric_idx",
        "fa_metric_data_points",
        ["company_id", "metric_key"],
    )
    op.create_index(
        "fa_metric_points_company_metric_period_idx",
        "fa_metric_data_points",
        ["company_id", "metric_key", "period"],
    )
    op.drop_column("fa_metric_data_points", "statement_type")
