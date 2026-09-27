"""Persists one company's P&L Intelligence computation to the 5 tables
`alembic/versions/0027_pl_intelligence.py` created. Called once per
completed analysis (see `master_object.py`'s Milestone 4 wiring) — not on
every read, unlike `pnl_engine.py`'s always-compute-fresh pattern. Every
row carries `algorithm_version`; re-scoring under a new version inserts new
rows rather than overwriting old ones (the unique constraint on
`pl_score_components` enforces this for the score table specifically).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import (
    PlDiagnostics,
    PlIncomeQuality,
    PlScoreComponents,
    PlStructuralAnalysis,
    PlTrends,
)

# Dual-write source/tier/confidence for the screener-filter ledger rows
# below — mirrors `screener_client.py::ingest_quarterly_metrics`'s existing
# CALCULATED-metric convention (e.g. cost_to_income_ratio) exactly.
_LEDGER_SOURCE = "CALCULATED"
_LEDGER_SOURCE_TIER = 1  # this app's own deterministic P&L engine output
_LEDGER_CONFIDENCE = "MEDIUM"  # derived from several ledger-sourced inputs

# `metric_store.get_latest_period_value()` — the function
# `app/screening/engine.py::_resolve_metric_value()` actually calls — reads
# `statement_type=DEFAULT_STATEMENT_TYPE` ("STANDALONE") when the caller
# doesn't override it, and the screener's rule evaluator never overrides
# it. A P&L score is one number per company (not itself a standalone-vs-
# consolidated concept), so it's written under STANDALONE regardless of
# which statement_type the underlying cascade used — the only way these
# metrics are actually discoverable through the existing screener mechanism.
_LEDGER_STATEMENT_TYPE = "STANDALONE"

# metric_key -> path into `result` (dot-separated) for the screener-filter
# dual-write. Registered in app/metrics/registry.py under the same ids.
_LEDGER_METRICS: dict[str, tuple[str, ...]] = {
    "pl_score": ("score", "master_pl_score"),
    "pl_pat_margin_percentile": ("peer_percentiles", "pat_margin", "percentile"),
    "pl_ebitda_margin_percentile": ("peer_percentiles", "ebitda_margin", "percentile"),
    "pl_revenue_doubling_years": ("doubling", "revenue", "doubling_years"),
    "pl_pat_doubling_years": ("doubling", "pat", "doubling_years"),
    "pl_eqi": ("earnings_quality", "eqi"),
    "pl_csr": ("structure", "csr"),
    "pl_margin_headroom": ("margin_headroom", "headroom_pct"),
}


def _dig(d: dict, path: tuple[str, ...]):
    for key in path:
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d


_LEDGER_UNITS: dict[str, str] = {
    "pl_score": "score",
    "pl_pat_margin_percentile": "percentile",
    "pl_ebitda_margin_percentile": "percentile",
    "pl_revenue_doubling_years": "years",
    "pl_pat_doubling_years": "years",
    "pl_eqi": "ratio",
    "pl_csr": "ratio",
    "pl_margin_headroom": "pp",
}


def sync_to_metric_ledger(db: Session, company_id: str, period: str, result: dict) -> None:
    """Dual-writes the screenable P&L Intelligence metrics into the
    existing `fa_metric_data_points` ledger (spec Stage 27) — gets full
    screener-filter support for free through the existing declarative
    `rules.yaml`/`app/screening/engine.py` mechanism, at the cost of the
    same number living in both a structured `pl_*` table (via
    `save_pl_score`, for point-in-time reproducibility) and a ledger row
    (for screening) — an accepted, precedented tradeoff (`MetricDataPoint`
    is already this app's canonical raw-value ledger). Skips any metric
    whose value is currently `None` rather than writing a misleading zero."""
    now = datetime.now(timezone.utc)
    for metric_key, path in _LEDGER_METRICS.items():
        value = _dig(result, path)
        if value is None:
            continue
        metric_store.insert_metric_value(
            db,
            company_id=company_id,
            metric_key=metric_key,
            period=period,
            value=float(value),
            unit=_LEDGER_UNITS[metric_key],
            statement_type=_LEDGER_STATEMENT_TYPE,
            source=_LEDGER_SOURCE,
            source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED",
            confidence=_LEDGER_CONFIDENCE,
            calculation_formula=f"pl_intelligence.{'.'.join(path)}, algorithm_version={result.get('score', {}).get('algorithm_version')}",
            source_date=now,
        )


def save_pl_score(db: Session, company_id: str, period: str, result: dict, statement_type: str = "CONSOLIDATED") -> None:
    """`result`: the combined dict `pl_intelligence/__init__.py`'s
    orchestrator produces (Milestone 4) — keyed the same way this function
    reads it below. Never raises on a missing optional sub-key (mirrors
    every other calc module's "never raises" contract); only genuinely
    fails if `db.add`/`flush` itself fails, which the caller should let
    propagate (a failed write should not look like a successful one).

    Idempotent per `(company_id, period, algorithm_version)`: a real bug
    found immediately after wiring this into the orchestrator (Milestone
    5) — a second pipeline run for the same company+period+version (an
    ordinary "Analyze" re-run, not an edge case) hit
    `pl_score_components`'s unique constraint and raised `IntegrityError`,
    which would have permanently failed this stage on every re-analysis
    until the algorithm version changed. Existing rows for this exact key
    are deleted before inserting fresh ones — this is "latest computation
    for this version wins," not a violation of Rule 7's reproducibility:
    reproducibility is about being able to recompute a PAST
    `algorithm_version`'s score from the data available then, not about
    freezing every individual re-run of the CURRENT version forever."""
    now = datetime.now(timezone.utc)
    score = result.get("score") or {}
    components = score.get("components") or {}
    algorithm_version = score.get("algorithm_version", "UNKNOWN")

    db.query(PlScoreComponents).filter_by(
        company_id=company_id, period=period, statement_type=statement_type, algorithm_version=algorithm_version,
    ).delete()
    db.query(PlDiagnostics).filter_by(
        company_id=company_id, period=period, algorithm_version=algorithm_version,
    ).delete()
    db.query(PlTrends).filter_by(
        company_id=company_id, period=period, statement_type=statement_type, algorithm_version=algorithm_version,
    ).delete()
    db.query(PlStructuralAnalysis).filter_by(
        company_id=company_id, period=period, algorithm_version=algorithm_version,
    ).delete()
    db.query(PlIncomeQuality).filter_by(
        company_id=company_id, period=period, algorithm_version=algorithm_version,
    ).delete()

    db.add(PlScoreComponents(
        id=str(uuid.uuid4()),
        company_id=company_id,
        period=period,
        statement_type=statement_type,
        m1_sector_margin_percentile=result.get("peer_percentiles", {}).get("pat_margin", {}).get("percentile"),
        m1_score=components.get("M1"),
        m2_margin_headroom=result.get("margin_headroom", {}).get("headroom_pct"),
        m2_score=components.get("M2"),
        m3_revenue_doubling_years=result.get("doubling", {}).get("revenue", {}).get("doubling_years"),
        m3_score=components.get("M3"),
        m4_eqi=result.get("earnings_quality", {}).get("eqi"),
        m4_score=components.get("M4"),
        m5_csr=result.get("structure", {}).get("csr"),
        m5_score=components.get("M5"),
        master_pl_score=score.get("master_pl_score"),
        classification=score.get("classification"),
        algorithm_version=algorithm_version,
        data_version=result.get("data_version"),
        peer_group_snapshot=result.get("peer_group_snapshot"),
        calculated_at=now,
    ))

    for flag in result.get("diagnostic_flags", []):
        db.add(PlDiagnostics(
            id=str(uuid.uuid4()),
            company_id=company_id,
            period=period,
            flag=flag,
            severity=result.get("flag_severity", {}).get(flag),
            details=result.get("flag_details", {}).get(flag),
            algorithm_version=algorithm_version,
            calculated_at=now,
        ))

    margins = result.get("margins", {})
    doubling = result.get("doubling", {})
    db.add(PlTrends(
        id=str(uuid.uuid4()),
        company_id=company_id,
        period=period,
        statement_type=statement_type,
        gross_margin=None,
        gross_margin_confidence="LOW",
        ebitda_margin=margins.get("ebitda_margin"),
        ebit_margin=margins.get("ebit_margin"),
        pat_margin=margins.get("pat_margin"),
        margin_direction=margins.get("margin_direction"),
        revenue_doubling_years=doubling.get("revenue", {}).get("doubling_years"),
        pat_doubling_years=doubling.get("pat", {}).get("doubling_years"),
        algorithm_version=algorithm_version,
        calculated_at=now,
    ))

    structure = result.get("structure", {})
    db.add(PlStructuralAnalysis(
        id=str(uuid.uuid4()),
        company_id=company_id,
        period=period,
        csr=structure.get("csr"),
        csr_band=structure.get("csr_band"),
        subsidiary_revenue_share=structure.get("subsidiary_revenue_share"),
        is_conglomerate=structure.get("is_conglomerate", False),
        segment_count=structure.get("segment_count"),
        segment_sector_count=structure.get("segment_sector_count"),
        sotp_required=structure.get("sotp_required", False),
        algorithm_version=algorithm_version,
        calculated_at=now,
    ))

    eq = result.get("earnings_quality", {})
    db.add(PlIncomeQuality(
        id=str(uuid.uuid4()),
        company_id=company_id,
        period=period,
        eqi=eq.get("eqi"),
        core_operating_income=eq.get("core_operating_income"),
        total_income=eq.get("total_income"),
        other_income_to_pat_pct=eq.get("other_income_to_pat_pct"),
        non_core_decomposition_available=False,
        algorithm_version=algorithm_version,
        calculated_at=now,
    ))
