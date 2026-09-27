"""P&L Analysis Engine — P&L Intelligence, Milestone 3. Persists the M1-M5
Master Score, rule-based diagnostics, margin trends, standalone-vs-
consolidated structural analysis, and earnings-quality results computed by
`app/calculations/pl_intelligence/`. Point-in-time persisted (not
compute-on-read like `pnl_engine.py`) because the Master Score needs to
stay reproducible under a given `algorithm_version` even as the underlying
ledger grows (spec Rule 7) — the unique constraint on
`(company_id, period, statement_type, algorithm_version)` on
`pl_score_components` is what enforces that: a new algorithm version
inserts new rows alongside old ones, never overwrites them.

Also adds the ORM class for the pre-existing but previously-unmapped
`fa_stock_classification` table (migration 0006) — no schema change there,
just closes a real gap flagged while building the peer/sector-gating work
in this milestone.

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pl_score_components",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("statement_type", sa.String(), nullable=False, server_default="CONSOLIDATED"),
        sa.Column("m1_sector_margin_percentile", sa.Numeric(6, 2), nullable=True),
        sa.Column("m1_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("m2_margin_headroom", sa.Numeric(6, 2), nullable=True),
        sa.Column("m2_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("m3_revenue_doubling_years", sa.Numeric(6, 2), nullable=True),
        sa.Column("m3_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("m4_eqi", sa.Numeric(6, 4), nullable=True),
        sa.Column("m4_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("m5_csr", sa.Numeric(6, 4), nullable=True),
        sa.Column("m5_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("master_pl_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("classification", sa.String(), nullable=True),
        sa.Column("algorithm_version", sa.String(), nullable=False),
        sa.Column("data_version", sa.String(), nullable=True),
        sa.Column("peer_group_snapshot", sa.JSON(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "period", "statement_type", "algorithm_version",
            name="pl_score_components_company_period_version_uq",
        ),
    )
    op.create_index("pl_score_components_company_idx", "pl_score_components", ["company_id"])

    op.create_table(
        "pl_diagnostics",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("flag", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("algorithm_version", sa.String(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("pl_diagnostics_company_idx", "pl_diagnostics", ["company_id"])

    op.create_table(
        "pl_trends",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("statement_type", sa.String(), nullable=False, server_default="CONSOLIDATED"),
        sa.Column("gross_margin", sa.Numeric(6, 2), nullable=True),
        sa.Column("gross_margin_confidence", sa.String(), nullable=False, server_default="LOW"),
        sa.Column("ebitda_margin", sa.Numeric(6, 2), nullable=True),
        sa.Column("ebit_margin", sa.Numeric(6, 2), nullable=True),
        sa.Column("pat_margin", sa.Numeric(6, 2), nullable=True),
        sa.Column("margin_direction", sa.String(), nullable=True),
        sa.Column("revenue_doubling_years", sa.Numeric(6, 2), nullable=True),
        sa.Column("pat_doubling_years", sa.Numeric(6, 2), nullable=True),
        sa.Column("algorithm_version", sa.String(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("pl_trends_company_idx", "pl_trends", ["company_id"])

    op.create_table(
        "pl_structural_analysis",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("csr", sa.Numeric(6, 4), nullable=True),
        sa.Column("csr_band", sa.String(), nullable=True),
        sa.Column("subsidiary_revenue_share", sa.Numeric(6, 4), nullable=True),
        sa.Column("is_conglomerate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("segment_count", sa.Integer(), nullable=True),
        sa.Column("segment_sector_count", sa.Integer(), nullable=True),
        sa.Column("sotp_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("algorithm_version", sa.String(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("pl_structural_analysis_company_idx", "pl_structural_analysis", ["company_id"])

    op.create_table(
        "pl_income_quality",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("eqi", sa.Numeric(6, 4), nullable=True),
        sa.Column("core_operating_income", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_income", sa.Numeric(20, 2), nullable=True),
        sa.Column("other_income_to_pat_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("non_core_decomposition_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("algorithm_version", sa.String(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("pl_income_quality_company_idx", "pl_income_quality", ["company_id"])


def downgrade() -> None:
    op.drop_index("pl_income_quality_company_idx", "pl_income_quality")
    op.drop_table("pl_income_quality")
    op.drop_index("pl_structural_analysis_company_idx", "pl_structural_analysis")
    op.drop_table("pl_structural_analysis")
    op.drop_index("pl_trends_company_idx", "pl_trends")
    op.drop_table("pl_trends")
    op.drop_index("pl_diagnostics_company_idx", "pl_diagnostics")
    op.drop_table("pl_diagnostics")
    op.drop_index("pl_score_components_company_idx", "pl_score_components")
    op.drop_table("pl_score_components")
