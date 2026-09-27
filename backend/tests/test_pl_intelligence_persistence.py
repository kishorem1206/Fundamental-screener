"""Persistence idempotency tests (P&L Analysis Engine plan, Milestone 5).
`test_save_pl_score_is_idempotent_on_rerun` is a regression test for a
real bug found immediately after wiring `save_pl_score` into the
orchestrator pipeline: calling it twice for the same
(company_id, period, algorithm_version) — an ordinary re-analysis, not an
edge case — raised `IntegrityError` on `pl_score_components`'s unique
constraint instead of refreshing the row.
"""
from __future__ import annotations

from app.calculations.pl_intelligence.persistence import save_pl_score
from app.infrastructure.database.models import (
    PlDiagnostics,
    PlIncomeQuality,
    PlScoreComponents,
    PlStructuralAnalysis,
    PlTrends,
)

_RESULT = {
    "score": {
        "master_pl_score": 75.0, "classification": "STABLE_COMPOUNDER_MARGIN_EXPANSION_CANDIDATE",
        "components": {"M1": 70.0, "M2": 80.0, "M3": 80.0, "M4": 60.0, "M5": 75.0},
        "algorithm_version": "PL_ENGINE_V1.0",
    },
    "peer_percentiles": {"pat_margin": {"percentile": 65}},
    "margin_headroom": {"headroom_pct": 12.0},
    "doubling": {"revenue": {"doubling_years": 7}, "pat": {"doubling_years": 6}},
    "earnings_quality": {"eqi": 0.85},
    "structure": {"csr": 0.72, "csr_band": "MATERIAL_SUBSIDIARY_CONTRIBUTION",
                  "subsidiary_revenue_share": 0.28, "is_conglomerate": False, "sotp_required": False,
                  "segment_count": 1, "segment_sector_count": 1},
    "margins": {"ebitda_margin": 18.0, "ebit_margin": 14.0, "pat_margin": 10.0, "margin_direction": "STABLE"},
    "diagnostic_flags": ["margin_expansion_candidate"],
    "flag_severity": {}, "flag_details": {},
}

# `pl_*` tables FK company_id -> stocks.id, so a synthetic company_id
# isn't usable here — reuse a real stock (Maruti, already used elsewhere
# in this test suite) with a clearly-synthetic period date that would
# never occur in real data, so this test can't collide with genuinely
# computed rows for the same company.
_COMPANY_ID = "NSE:MARUTI"
_PERIOD = "1901-03-31"


def test_save_pl_score_is_idempotent_on_rerun(db):
    save_pl_score(db, _COMPANY_ID, _PERIOD, _RESULT)
    db.flush()
    save_pl_score(db, _COMPANY_ID, _PERIOD, _RESULT)  # must not raise IntegrityError
    db.flush()

    score_rows = db.query(PlScoreComponents).filter_by(company_id=_COMPANY_ID, period=_PERIOD).all()
    assert len(score_rows) == 1
    assert score_rows[0].master_pl_score == 75.0

    diagnostics_rows = db.query(PlDiagnostics).filter_by(company_id=_COMPANY_ID, period=_PERIOD).all()
    assert len(diagnostics_rows) == 1

    trends_rows = db.query(PlTrends).filter_by(company_id=_COMPANY_ID, period=_PERIOD).all()
    assert len(trends_rows) == 1

    structural_rows = db.query(PlStructuralAnalysis).filter_by(company_id=_COMPANY_ID, period=_PERIOD).all()
    assert len(structural_rows) == 1

    income_quality_rows = db.query(PlIncomeQuality).filter_by(company_id=_COMPANY_ID, period=_PERIOD).all()
    assert len(income_quality_rows) == 1


def test_save_pl_score_refreshes_values_on_rerun(db):
    save_pl_score(db, _COMPANY_ID, _PERIOD, _RESULT)
    db.flush()

    updated_result = {**_RESULT, "score": {**_RESULT["score"], "master_pl_score": 88.0}}
    save_pl_score(db, _COMPANY_ID, _PERIOD, updated_result)
    db.flush()

    row = db.query(PlScoreComponents).filter_by(company_id=_COMPANY_ID, period=_PERIOD).one()
    assert row.master_pl_score == 88.0


def test_save_pl_score_preserves_rows_under_a_different_algorithm_version(db):
    save_pl_score(db, _COMPANY_ID, _PERIOD, _RESULT)
    db.flush()

    v2_result = {**_RESULT, "score": {**_RESULT["score"], "algorithm_version": "PL_ENGINE_V1.1", "master_pl_score": 90.0}}
    save_pl_score(db, _COMPANY_ID, _PERIOD, v2_result)
    db.flush()

    rows = db.query(PlScoreComponents).filter_by(company_id=_COMPANY_ID, period=_PERIOD).all()
    assert len(rows) == 2
    versions = {r.algorithm_version: r.master_pl_score for r in rows}
    assert versions == {"PL_ENGINE_V1.0": 75.0, "PL_ENGINE_V1.1": 90.0}
