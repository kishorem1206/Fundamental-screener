"""Tests for `app/ingestion/quarterly_results_client.py` — the Quarterly
Report Extraction Engine's Tier-1 Screener ingestion. Uses the real
NSE:MARUTI fixture company (already present in the dev DB per
`tests/conftest.py`'s "join an external transaction" pattern, same
convention `test_balance_sheet_ingestion.py` uses) for FK safety, and
monkeypatches `openscreener.Stock` (imported locally inside
`ingest_quarterly_results()`, so patching the `openscreener` module
attribute before the call is enough) rather than hitting the network.
"""
from __future__ import annotations

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock
from app.ingestion import quarterly_results_client as qrc
from app.ingestion.pnl_history_client import _fmt_period


def _fixture_company_id(db, symbol: str = "MARUTI") -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


def test_field_map_uses_qtr_prefix_not_pnl_prefix():
    """Guards against a future accidental `pnl_` typo reintroducing the
    Q4/fiscal-year-end date collision this module was built to avoid."""
    for metric_key, _unit in qrc._FIELD_MAP.values():
        assert metric_key.startswith("qtr_"), f"{metric_key} must be qtr_-prefixed, not pnl_-prefixed"


def test_fmt_period_parses_mon_yyyy():
    assert _fmt_period("Mar 2026") == "2026-03-31"
    assert _fmt_period("Jun 2025") == "2025-06-30"


def test_fmt_period_returns_none_for_ttm_and_garbage():
    assert _fmt_period("TTM") is None
    assert _fmt_period("not a date") is None


class _FakeStock:
    def __init__(self, symbol: str, consolidated: bool):
        self.symbol = symbol
        self.consolidated = consolidated

    def quarterly_results(self):
        return [
            {"date": "Dec 2025", "sales": 100.0, "operating_profit": 20.0,
             "operating_margin_percent": 20.0, "net_profit": 10.0},
            {"date": "Mar 2026", "sales": 110.0, "operating_profit": 22.0,
             "operating_margin_percent": 20.0, "net_profit": 11.0},
            {"date": "TTM", "sales": 999.0, "operating_profit": 200.0,
             "operating_margin_percent": 20.0, "net_profit": 90.0},
        ]


def test_ingest_quarterly_results_dual_statement_type(monkeypatch, db):
    monkeypatch.setattr("openscreener.Stock", _FakeStock)
    monkeypatch.setattr(qrc, "_SCREENER_REQUEST_DELAY_SECONDS", 0)
    company_id = _fixture_company_id(db)

    result = qrc.ingest_quarterly_results(db, company_id=company_id, symbol="MARUTI")
    assert result, "expected rows to be inserted"

    for statement_type in ("STANDALONE", "CONSOLIDATED"):
        row = next(
            (r for r in result if r.metric_key == "qtr_sales" and r.statement_type == statement_type
             and r.period == "2026-03-31"),
            None,
        )
        assert row is not None, f"expected qtr_sales row for {statement_type}"
        assert row.value == 110.0
        assert row.source == "SCREENER"
        assert row.source_tier == 2


def test_ingest_quarterly_results_skips_ttm_row(monkeypatch, db):
    monkeypatch.setattr("openscreener.Stock", _FakeStock)
    monkeypatch.setattr(qrc, "_SCREENER_REQUEST_DELAY_SECONDS", 0)
    company_id = _fixture_company_id(db)

    result = qrc.ingest_quarterly_results(db, company_id=company_id, symbol="MARUTI")
    assert not any(r.period == "TTM" for r in result)


def test_no_collision_with_pnl_history_same_period(monkeypatch, db):
    """The direct regression test for the exact bug scenario flagged during
    design: a Q4 quarter-end date is textually identical to that year's
    fiscal-year-end date. Confirms `pnl_sales` and `qtr_sales` for the same
    company/period/statement_type land as two independent rows, neither
    overwriting the other."""
    company_id = _fixture_company_id(db)
    period = "2026-03-31"

    metric_store.insert_metric_value(
        db, company_id=company_id, metric_key="pnl_sales", period=period, value=555.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )

    monkeypatch.setattr("openscreener.Stock", _FakeStock)
    monkeypatch.setattr(qrc, "_SCREENER_REQUEST_DELAY_SECONDS", 0)
    qrc.ingest_quarterly_results(db, company_id=company_id, symbol="MARUTI")

    pnl_history = metric_store.get_metric_history(db, company_id, "pnl_sales", statement_type="STANDALONE")
    qtr_history = metric_store.get_metric_history(db, company_id, "qtr_sales", statement_type="STANDALONE")

    pnl_row = next(r for r in pnl_history if r.period == period)
    qtr_row = next(r for r in qtr_history if r.period == period)

    assert pnl_row.value == 555.0, "pnl_sales row must be untouched by the quarterly ingest"
    assert qtr_row.value == 110.0, "qtr_sales row must hold its own value, independent of pnl_sales"
