"""Tests for `app/calculations/screener_metrics_override.py` (Screener.in as
Primary Source of Truth, Milestone 2 — P&L overrides). Mocks
`pnl_engine.compute_pnl_analysis()`'s return shape (already confirmed exact
against the live code: `growth.sales_cagr/profit_cagr/eps_cagr` keyed
"10y"/"7y"/"5y"/"3y", `margins.npm.current`, `roe.latest`,
`interest_coverage.latest`) rather than hitting the real DB/network — this
module's own logic (which keys get overwritten, with what, and which stay
untouched) is what's under test, not `pnl_engine.py` itself (already
covered by its own test files).
"""
from __future__ import annotations

from app.calculations import screener_metrics_override as smo

_FAKE_PNL_RESULT = {
    "period": "2026-03-31",
    "growth": {
        "sales_cagr": {"10y": 12.5, "7y": 11.0, "5y": 15.0, "3y": 18.0},
        "profit_cagr": {"10y": 14.0, "7y": 13.0, "5y": 16.0, "3y": 20.0},
        "eps_cagr": {"10y": 13.5, "7y": 12.0, "5y": 17.0, "3y": 19.0},
    },
    "margins": {"npm": {"current": 9.8}},
    "roe": {"latest": 22.4},
    "interest_coverage": {"latest": 8.1},
}


def _base_metrics() -> dict:
    return {
        "revenue_cagr_3y": 10.0, "revenue_cagr_5y": 10.0, "revenue_cagr_10y": 10.0,
        "pat_cagr_3y": 10.0, "pat_cagr_5y": 10.0, "pat_cagr_10y": 10.0,
        "eps_cagr_3y": 10.0, "eps_cagr_5y": 10.0, "eps_cagr_10y": 10.0,
        "pat_margin": 5.0, "roe": 15.0, "interest_coverage": 3.0,
        "ebitda_margin": 25.0,  # untouched by Milestone 2 — must stay byte-identical
        "roa": 4.0,             # SCREENER_NOT_AVAILABLE — must stay byte-identical
    }


def test_pnl_overrides_apply_correct_windows_and_values(monkeypatch):
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: _FAKE_PNL_RESULT)
    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")

    assert result["revenue_cagr_3y"] == 18.0
    assert result["revenue_cagr_5y"] == 15.0
    assert result["revenue_cagr_10y"] == 12.5
    assert result["pat_cagr_3y"] == 20.0
    assert result["eps_cagr_3y"] == 19.0
    assert result["pat_margin"] == 9.8
    assert result["roe"] == 22.4
    assert result["interest_coverage"] == 8.1


def test_pnl_overrides_never_touch_the_7y_window(monkeypatch):
    """pnl_engine.py computes a 7y CAGR window but engine.py has no
    `revenue_cagr_7y` key anywhere — confirm this override never invents
    one."""
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: _FAKE_PNL_RESULT)
    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert "revenue_cagr_7y" not in result


def test_pnl_overrides_leave_untouched_keys_byte_identical(monkeypatch):
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: _FAKE_PNL_RESULT)
    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["ebitda_margin"] == 25.0
    assert result["roa"] == 4.0


def test_metric_sources_records_only_touched_keys(monkeypatch):
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: _FAKE_PNL_RESULT)
    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    sources = result["_metric_sources"]
    assert sources["roe"] == "SCREENER"
    assert sources["pat_margin"] == "SCREENER"
    assert "ebitda_margin" not in sources
    assert "roa" not in sources


class _FakeRow:
    def __init__(self, value):
        self.value = value


def test_growth_widget_value_wins_over_pnl_engine_calculated_cagr(monkeypatch):
    """Real gap found live on Pine Labs (2026-09-16): pnl_engine.py's
    calculated pat_cagr_3y comes back None on a loss-to-profit turnaround
    (a window endpoint <= 0), but Screener's own displayed widget still
    shows a number for that case — the widget value must win when present."""
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: _FAKE_PNL_RESULT)

    def _fake_latest(db, company_id, metric_key, statement_type):
        widget_values = {"screener_pat_cagr_3y": 36.0, "screener_revenue_cagr_3y": 19.0}
        value = widget_values.get(metric_key)
        return _FakeRow(value) if value is not None else None
    monkeypatch.setattr("app.infrastructure.database.metric_store.get_latest_period_value", _fake_latest)

    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=object(), company_id="NSE:PINELABS")

    assert result["pat_cagr_3y"] == 36.0  # widget value, not pnl_engine's 20.0
    assert result["revenue_cagr_3y"] == 19.0  # widget value, not pnl_engine's 18.0
    assert result["pat_cagr_5y"] == 16.0  # no widget row for 5y -> pnl_engine's calculated value
    assert result["_metric_sources"]["pat_cagr_3y"] == "SCREENER_WIDGET"
    assert result["_metric_sources"]["pat_cagr_5y"] == "SCREENER"


def test_growth_widget_lookup_failure_falls_back_to_pnl_engine(monkeypatch):
    """A DB error reading the widget snapshot must not block the
    pnl_engine.py calculated CAGR from still being applied — matches this
    module's degrade-gracefully contract."""
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: _FAKE_PNL_RESULT)

    def _boom(db, company_id, metric_key, statement_type):
        raise RuntimeError("db unavailable")
    monkeypatch.setattr("app.infrastructure.database.metric_store.get_latest_period_value", _boom)

    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=object(), company_id="NSE:PINELABS")
    assert result["pat_cagr_3y"] == 20.0  # pnl_engine's calculated value, untouched by the failed widget lookup


def test_never_overwrites_with_none(monkeypatch):
    """A Screener-sourced None (e.g. pnl_engine has no data at all yet for
    this company) must never blank out a working yfinance value."""
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: {})
    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["revenue_cagr_3y"] == 10.0
    assert result["roe"] == 15.0
    assert "_metric_sources" not in result


def test_never_raises_on_pnl_engine_exception(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("db down")
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", _boom)
    metrics = _base_metrics()
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["roe"] == 15.0  # unchanged, no exception propagated


def test_none_metrics_passthrough():
    assert smo.apply_screener_primary_overrides(None, db=None, company_id="NSE:FAKE") is None


# ── Milestone 3: balance-sheet overrides ────────────────────────────────────

_FAKE_BSI_RESULT = {
    "period": "2026-03-31",
    "statement_type": "CONSOLIDATED",
    "derived_metrics": {"roce": 21.5, "debt_to_equity": 0.42, "net_debt_to_ebitda": 0.8},
    "working_capital": {
        "latest_cross_check": {
            "dio": {"yfinance": None, "screener_latest": 12.0, "divergence_pct": None},
            "dso": {"yfinance": 61.2, "screener_latest": 79.0, "divergence_pct": 29.08},
        },
    },
}
_FAKE_CASCADE = {"2026-03-31": {"ebitda": 900.0, "ebit": 800.0, "revenue": 5000.0}}


def _patch_bsi_and_cascade(monkeypatch, bsi_result=_FAKE_BSI_RESULT, cascade=_FAKE_CASCADE):
    monkeypatch.setattr(
        "app.calculations.balance_sheet_intelligence.compute_balance_sheet_intelligence",
        lambda *a, **k: bsi_result,
    )
    monkeypatch.setattr(
        "app.calculations.pl_intelligence.cascade.build_income_cascade",
        lambda *a, **k: cascade,
    )
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: {})


def test_balance_sheet_overrides_apply_correct_values(monkeypatch):
    _patch_bsi_and_cascade(monkeypatch)
    metrics = _base_metrics()
    metrics.update({"debt_to_equity": 1.0, "net_debt_to_ebitda": 2.0, "inventory_days": 40.0, "receivable_days": 50.0})
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")

    assert result["roce"] == 21.5
    assert result["debt_to_equity"] == 0.42
    assert result["net_debt_to_ebitda"] == 0.8
    assert result["inventory_days"] == 12.0
    assert result["receivable_days"] == 79.0
    assert result["ebitda_margin"] == 18.0   # 900/5000*100
    assert result["ebit_margin"] == 16.0     # 800/5000*100
    for key in ("roce", "debt_to_equity", "net_debt_to_ebitda", "inventory_days",
                "receivable_days", "ebitda_margin", "ebit_margin"):
        assert result["_metric_sources"][key] == "SCREENER"


def test_balance_sheet_overrides_skip_when_no_period(monkeypatch):
    _patch_bsi_and_cascade(monkeypatch, bsi_result={"period": None})
    metrics = _base_metrics()
    metrics["roce"] = 99.0
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["roce"] == 99.0
    assert "roce" not in result.get("_metric_sources", {})


def test_balance_sheet_overrides_never_raise(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("db down")
    monkeypatch.setattr("app.calculations.balance_sheet_intelligence.compute_balance_sheet_intelligence", _boom)
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: {})
    metrics = _base_metrics()
    metrics["roce"] = 7.0
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["roce"] == 7.0


# ── Milestone 4: valuation overrides ────────────────────────────────────────

def _fake_row(value):
    class _Row:
        pass
    row = _Row()
    row.value = value
    return row


def _patch_sr_values(monkeypatch, values: dict[str, float | None]):
    """`values` keyed by metric_key (e.g. "sr_pe_ratio") — mirrors
    `get_latest_period_value()`'s per-key lookup."""
    def _fake_get_latest_period_value(db, company_id, metric_key, statement_type="STANDALONE"):
        v = values.get(metric_key)
        return _fake_row(v) if v is not None else None
    monkeypatch.setattr("app.infrastructure.database.metric_store.get_latest_period_value", _fake_get_latest_period_value)
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: {})
    monkeypatch.setattr("app.calculations.balance_sheet_intelligence.compute_balance_sheet_intelligence", lambda *a, **k: {"period": None})


def test_valuation_overrides_apply_correct_values(monkeypatch):
    _patch_sr_values(monkeypatch, {
        "sr_pe_ratio": 27.5, "sr_market_cap": 386860.0, "sr_dividend_yield": 1.13,
        "sr_current_price": 12305.0, "sr_book_value": 3343.0,
    })
    metrics = _base_metrics()
    metrics.update({"pe_ratio": 30.0, "market_cap": 0.0, "dividend_yield": 0.0, "pb_ratio": 5.0})
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")

    assert result["pe_ratio"] == 27.5
    # market_cap: metrics["market_cap"] is a raw-Rupee figure everywhere
    # else in this codebase (yfinance's native unit) — sr_market_cap is
    # ingested in Crores, so the override must convert (x1e7) rather than
    # writing Crores in unconverted (see the real bug this caught, module
    # docstring in screener_metrics_override.py).
    assert result["market_cap"] == 386860.0 * 1e7
    assert result["dividend_yield"] == 1.13
    assert result["pb_ratio"] == round(12305.0 / 3343.0, 4)
    for key in ("pe_ratio", "market_cap", "dividend_yield", "pb_ratio"):
        assert result["_metric_sources"][key] == "SCREENER"


def test_valuation_overrides_pb_ratio_guards_zero_book_value(monkeypatch):
    _patch_sr_values(monkeypatch, {"sr_current_price": 100.0, "sr_book_value": 0.0})
    metrics = _base_metrics()
    metrics["pb_ratio"] = 2.5
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["pb_ratio"] == 2.5  # untouched — never divides by zero
    assert "pb_ratio" not in result.get("_metric_sources", {})


def test_valuation_overrides_pb_ratio_guards_missing_price(monkeypatch):
    _patch_sr_values(monkeypatch, {"sr_book_value": 3343.0})  # no current_price
    metrics = _base_metrics()
    metrics["pb_ratio"] = 2.5
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["pb_ratio"] == 2.5


def test_valuation_overrides_never_raise(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("db down")
    monkeypatch.setattr("app.infrastructure.database.metric_store.get_latest_period_value", _boom)
    monkeypatch.setattr("app.calculations.pnl_engine.compute_pnl_analysis", lambda *a, **k: {})
    monkeypatch.setattr("app.calculations.balance_sheet_intelligence.compute_balance_sheet_intelligence", lambda *a, **k: {"period": None})
    metrics = _base_metrics()
    metrics["pe_ratio"] = 30.0
    result = smo.apply_screener_primary_overrides(metrics, db=None, company_id="NSE:FAKE")
    assert result["pe_ratio"] == 30.0
