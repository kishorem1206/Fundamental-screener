"""Tests for `balance_sheet_intelligence.persistence` and the
`/api/balance-sheet-intelligence/*` route (Balance Sheet Analysis Engine,
Milestone 7) — mirrors `test_pl_intelligence_persistence.py`/
`test_pl_intelligence_api.py`.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.calculations.balance_sheet_intelligence.persistence import sync_to_metric_ledger
from app.infrastructure.database.models import MetricDataPoint, Stock
from app.main import app

client = TestClient(app)
_UNKNOWN_COMPANY = "NOT-A-REAL-COMPANY-ID"

_RESULT = {
    "derived_metrics": {"debt_to_equity": 0.15, "liabilities_to_equity": 0.4, "net_debt_to_ebitda": 0.5, "roce": 18.5},
    "working_capital": {"ccc_latest": -20.0, "current_ratio_latest": 1.2, "quick_ratio_latest": 0.6, "cash_ratio_latest": 0.05},
    "coverage": {"coverage_pct": 55.0},
    "archetype": {"classification": "STRONG", "ruleset_version": "BS_ENGINE_V1.0"},
    "risk_flags": [
        {"flag_id": "HIGH_LEVERAGE", "status": "NOT_TRIGGERED"},
        {"flag_id": "WORKING_CAPITAL_DRAG", "status": "TRIGGERED"},
        {"flag_id": "RELATED_PARTY_EXPOSURE", "status": "SOURCE_REQUIRED"},
    ],
}


# ── persistence.py ───────────────────────────────────────────────────────────

def test_sync_writes_expected_metric_keys(db):
    stock = db.query(Stock).filter_by(symbol="MARUTI").first()
    company_id = stock.id
    period = "2099-03-31"  # synthetic, never collides with real ingested data
    sync_to_metric_ledger(db, company_id, period, _RESULT)

    for metric_key, expected_value in [
        ("bs_debt_to_equity", 0.15), ("bs_roce", 18.5), ("bs_ccc", -20.0),
        ("bs_current_ratio", 1.2), ("bs_coverage_pct", 55.0),
        ("bs_archetype_score", 3.0),  # STRONG
        ("bs_red_flag_count", 1.0),  # only WORKING_CAPITAL_DRAG is TRIGGERED
    ]:
        row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key=metric_key, period=period).first()
        assert row is not None, f"expected {metric_key} to be written"
        assert float(row.value) == expected_value
        assert row.source == "CALCULATED"
        assert row.statement_type == "STANDALONE"


def test_sync_skips_none_values(db):
    stock = db.query(Stock).filter_by(symbol="MARUTI").first()
    company_id = stock.id
    period = "2098-03-31"
    result = {"derived_metrics": {"debt_to_equity": None}, "working_capital": {}, "coverage": {}, "archetype": {}, "risk_flags": []}
    sync_to_metric_ledger(db, company_id, period, result)
    row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key="bs_debt_to_equity", period=period).first()
    assert row is None


def test_sync_zero_red_flags_still_written(db):
    """0 is a real, meaningful value (no flags triggered) — must still be
    written, unlike a genuinely-missing metric."""
    stock = db.query(Stock).filter_by(symbol="MARUTI").first()
    company_id = stock.id
    period = "2097-03-31"
    result = {**_RESULT, "risk_flags": [{"flag_id": "HIGH_LEVERAGE", "status": "NOT_TRIGGERED"}]}
    sync_to_metric_ledger(db, company_id, period, result)
    row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key="bs_red_flag_count", period=period).first()
    assert row is not None
    assert float(row.value) == 0.0


# ── API route ────────────────────────────────────────────────────────────────

def test_base_route_returns_200_for_unknown_company():
    response = client.get(f"/api/balance-sheet-intelligence/{_UNKNOWN_COMPANY}")
    assert response.status_code == 200
    body = response.json()
    assert body["period"] is None
    assert body["balance_sheet_integrity"]["status"] == "MISSING_DATA"


def test_coverage_subroute_does_not_get_swallowed_by_base_route():
    """Regression coverage for the same routing-order bug already found
    live on pl_intelligence.py's first deploy — applying that lesson here
    from the start, verified rather than assumed."""
    response = client.get(f"/api/balance-sheet-intelligence/{_UNKNOWN_COMPANY}/coverage")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"company_id", "period", "coverage"}


def test_red_flags_subroute_shape():
    response = client.get(f"/api/balance-sheet-intelligence/{_UNKNOWN_COMPANY}/red-flags")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"company_id", "period", "risk_flags"}
    assert body["risk_flags"] == []


def test_archetype_subroute_shape():
    response = client.get(f"/api/balance-sheet-intelligence/{_UNKNOWN_COMPANY}/archetype")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"company_id", "period", "archetype", "financial_institution_summary"}


def test_real_company_returns_full_result():
    response = client.get("/api/balance-sheet-intelligence/NSE:MARUTI")
    assert response.status_code == 200
    body = response.json()
    assert body["period"] is not None
    assert body["balance_sheet_integrity"]["status"] == "VALID"
    assert len(body["risk_flags"]) == 12
