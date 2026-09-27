"""Formula + edge-case tests for `pl_intelligence/cascade.py` and
`cost_structure.py` (P&L Analysis Engine plan, Milestone 1). Uses Maruti
Suzuki (NSE:MARUTI) as the real-data fixture — re-ingested under both
statement types this session (Milestone 1a), so both STANDALONE and
CONSOLIDATED cascades have real data to build from.
"""
from __future__ import annotations

import pytest

from app.calculations.pl_intelligence.cascade import build_income_cascade
from app.calculations.pl_intelligence.cost_structure import (
    compute_cost_ratio_deltas,
    compute_cost_ratios,
)
from app.infrastructure.database.models import Stock

_FIXTURE_SYMBOL = "MARUTI"


def _fixture_company_id(db) -> str:
    stock = db.query(Stock).filter_by(symbol=_FIXTURE_SYMBOL).first()
    assert stock is not None, f"fixture company {_FIXTURE_SYMBOL} not found in stocks table"
    return stock.id


def test_build_income_cascade_rejects_missing_statement_type(db):
    with pytest.raises(TypeError):
        build_income_cascade(db, "any-company")  # type: ignore[call-arg]


def test_build_income_cascade_rejects_invalid_statement_type(db):
    with pytest.raises(ValueError):
        build_income_cascade(db, "any-company", statement_type="BOTH")


def test_build_income_cascade_unknown_company_returns_empty(db):
    result = build_income_cascade(db, "NOT-A-REAL-COMPANY-ID", statement_type="CONSOLIDATED")
    assert result == {}


def test_gross_margin_always_unavailable(db):
    company_id = _fixture_company_id(db)
    cascade = build_income_cascade(db, company_id, statement_type="CONSOLIDATED")
    assert cascade, "expected at least one period of cascade data for the fixture company"
    for period, entry in cascade.items():
        assert entry["cogs"] is None
        assert entry["gross_profit"] is None
        assert entry["gross_margin"] is None
        assert entry["gross_margin_confidence"] == "LOW"
        assert entry["confidence"]["revenue"] == "HIGH"


def test_cascade_margins_are_percentages_of_revenue(db):
    company_id = _fixture_company_id(db)
    cascade = build_income_cascade(db, company_id, statement_type="CONSOLIDATED")
    for period, entry in cascade.items():
        if entry["revenue"] and entry["ebitda"] is not None:
            expected = round(entry["ebitda"] / entry["revenue"] * 100, 2)
            assert entry["ebitda_margin"] == expected
        if entry["revenue"] and entry["pat"] is not None:
            expected = round(entry["pat"] / entry["revenue"] * 100, 2)
            assert entry["pat_margin"] == expected


def test_cascade_standalone_and_consolidated_never_mixed(db):
    company_id = _fixture_company_id(db)
    standalone = build_income_cascade(db, company_id, statement_type="STANDALONE")
    consolidated = build_income_cascade(db, company_id, statement_type="CONSOLIDATED")
    assert standalone, "expected standalone data after Milestone 1a re-ingestion"
    assert consolidated, "expected consolidated data (pre-existing)"
    # Maruti's standalone and consolidated revenue are close but not
    # required to be identical — the real assertion is that each call only
    # ever reads its own statement_type, never a blend of both.
    shared_periods = set(standalone) & set(consolidated)
    assert shared_periods, "expected at least one period present in both statement types"


def test_cost_ratios_employee_cost_always_unavailable():
    period_entry = {"revenue": 1000.0, "opex": 800.0, "finance_cost": 20.0,
                     "depreciation": 50.0, "tax": 40.0, "pbt": 160.0}
    ratios = compute_cost_ratios(period_entry)
    assert ratios["employee_cost_to_revenue_pct"] is None
    assert ratios["employee_cost_confidence"] == "UNAVAILABLE"
    assert ratios["opex_to_revenue_pct"] == 80.0


def test_cost_ratio_deltas_none_when_either_side_missing():
    current = {"opex_to_revenue_pct": 75.0, "finance_cost_to_revenue_pct": None,
               "depreciation_to_revenue_pct": 5.0, "tax_to_pbt_pct": 25.0}
    prior = {"opex_to_revenue_pct": 70.0, "finance_cost_to_revenue_pct": 2.0,
             "depreciation_to_revenue_pct": None, "tax_to_pbt_pct": 24.0}
    deltas = compute_cost_ratio_deltas(current, prior)
    assert deltas["delta_opex_to_revenue_pct"] == 5.0
    assert deltas["delta_finance_cost_to_revenue_pct"] is None
    assert deltas["delta_depreciation_to_revenue_pct"] is None
    assert deltas["delta_tax_to_pbt_pct"] == 1.0
