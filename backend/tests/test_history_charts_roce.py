"""Tests for `history_charts._screener_ratio_series()` — exposes the
multi-year `bs_ratio_roce_percent` series `ingest_ratios()` now stores
(2026-09-22 fix, see screener_client.py's docstring) to the "Revenue &
ROCE" history charts.
"""
from __future__ import annotations

from app.infrastructure.database.models import Stock
from app.routes.history_charts import _screener_ratio_series

_MANUFACTURING_SYMBOL = "MARUTI"


def _fixture_company_id(db, symbol: str) -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


def test_roce_series_covers_multiple_fiscal_years(db):
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    series = _screener_ratio_series(db, company_id, "bs_ratio_roce_percent")
    assert len(series) > 1, "expected multiple fiscal years of Screener-sourced ROCE, not just the latest"
    assert all(isinstance(v, float) for v in series.values())


def test_roce_series_unknown_metric_returns_empty(db):
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    assert _screener_ratio_series(db, company_id, "bs_ratio_not_a_real_field") == {}
