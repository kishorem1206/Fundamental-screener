"""Regression tripwire for the EXISTING `pnl_engine.py`, written before any
new `pl_intelligence/` code touches shared helpers it depends on
(`app/calculations/engine.py::calculate_cagr`/`safe_div`/`trend_direction`,
`metric_store.py`). Per the P&L Analysis Engine plan's Stage 0 boundary:
nothing in this file should ever need to change as new P&L Intelligence
code is added — if it does, something leaked across the boundary.

Uses Jyothy Labs (NSE:JYOTHYLAB), a non-financial (FMCG) company with
`pnl_*` ledger rows already ingested under `statement_type="CONSOLIDATED"`
(the statement type `pnl_engine.py::_series()` explicitly reads) — TCS and
several other early-ingested companies only have pre-2026-09-15 STANDALONE
rows under the `pnl_*` keys and would make this fixture look empty through
no fault of the engine itself.
"""
from __future__ import annotations

from app.calculations.pnl_engine import calc_margin_series, compute_pnl_analysis
from app.infrastructure.database.models import Stock

_FIXTURE_SYMBOL = "JYOTHYLAB"


def _fixture_company_id(db) -> str:
    stock = db.query(Stock).filter_by(symbol=_FIXTURE_SYMBOL).first()
    assert stock is not None, f"fixture company {_FIXTURE_SYMBOL} not found in stocks table"
    return stock.id


def test_calc_margin_series_basic():
    numerator = {"2024-03-31": 50.0, "2025-03-31": 60.0}
    denominator = {"2024-03-31": 200.0, "2025-03-31": 300.0}
    result = calc_margin_series(numerator, denominator)
    assert result["2024-03-31"] == 25.0
    assert result["2025-03-31"] == 20.0


def test_calc_margin_series_skips_zero_denominator():
    result = calc_margin_series({"2024-03-31": 10.0}, {"2024-03-31": 0.0})
    assert "2024-03-31" not in result


def test_compute_pnl_analysis_never_raises_for_unknown_company(db):
    result = compute_pnl_analysis(db, "NOT-A-REAL-COMPANY-ID")
    assert isinstance(result, dict)
    assert result.get("years_of_data") == 0


def test_compute_pnl_analysis_output_shape(db):
    company_id = _fixture_company_id(db)
    result = compute_pnl_analysis(db, company_id, sector_name="Fast Moving Consumer Goods")

    expected_top_level_keys = {
        "years_of_data", "is_financial_sector", "fiscal_years", "table",
        "growth", "margins", "consistency", "interest_coverage",
        "other_income_dependency", "depreciation", "roe", "dividend",
        "stock_price_cagr", "inflection_points", "red_flags",
        "positive_signals", "quality_score", "expense_structure",
        "buffetts_dollar_test",
    }
    assert expected_top_level_keys.issubset(result.keys())

    assert result["years_of_data"] > 0
    assert result["is_financial_sector"] is False
    assert result["expense_structure"] == {
        "not_available": True,
        "reason": (
            "Screener.in's standard P&L view has no material/employee/"
            "power-fuel breakdown for any sector checked"
        ),
    }
    assert result["buffetts_dollar_test"]["not_available"] is True

    quality_score = result["quality_score"]
    assert set(quality_score.keys()) == {"sub_scores", "overall"}
    assert isinstance(quality_score["overall"], float)


def test_compute_pnl_analysis_is_deterministic(db):
    company_id = _fixture_company_id(db)
    first = compute_pnl_analysis(db, company_id, sector_name="Fast Moving Consumer Goods")
    second = compute_pnl_analysis(db, company_id, sector_name="Fast Moving Consumer Goods")
    assert first["quality_score"] == second["quality_score"]
    assert first["table"] == second["table"]
    assert first["red_flags"] == second["red_flags"]
