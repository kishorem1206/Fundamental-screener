"""Tests for `pnl_history_client.py`'s `_parse_compounded_growth_widgets()`
— the "Compounded Sales/Profit Growth" `table.ranges-table` grid Screener
renders directly below the main P&L table (real markup shape confirmed
live on Pine Labs, 2026-09-16, consolidated view: sales 5y=32%/3y=19%/
ttm=20%, profit 5y=32%/3y=36%/ttm=262%, 10y blank for both since the
company hasn't been listed 10 years)."""
from __future__ import annotations

from app.ingestion.pnl_history_client import _parse_compounded_growth_widgets

_SAMPLE_HTML = """
<html><body>
<section id="profit-loss">
  <table class="data-table"><tbody><tr><td>Sales</td></tr></tbody></table>
  <div style="display: grid;">
    <table class="ranges-table">
      <tbody>
        <tr><th colspan="2">Compounded Sales Growth</th></tr>
        <tr><td>10 Years:</td><td>%</td></tr>
        <tr><td>5 Years:</td><td>32%</td></tr>
        <tr><td>3 Years:</td><td>19%</td></tr>
        <tr><td>TTM:</td><td>20%</td></tr>
      </tbody>
    </table>
    <table class="ranges-table">
      <tbody>
        <tr><th colspan="2">Compounded Profit Growth</th></tr>
        <tr><td>10 Years:</td><td>%</td></tr>
        <tr><td>5 Years:</td><td>32%</td></tr>
        <tr><td>3 Years:</td><td>36%</td></tr>
        <tr><td>TTM:</td><td>262%</td></tr>
      </tbody>
    </table>
    <table class="ranges-table">
      <tbody>
        <tr><th colspan="2">Stock Price CAGR</th></tr>
        <tr><td>10 Years:</td><td>%</td></tr>
      </tbody>
    </table>
    <table class="ranges-table">
      <tbody>
        <tr><th colspan="2">Return on Equity</th></tr>
        <tr><td>Last Year:</td><td>3%</td></tr>
      </tbody>
    </table>
  </div>
</section>
</body></html>
"""


def test_parses_sales_and_profit_growth_windows():
    result = _parse_compounded_growth_widgets(_SAMPLE_HTML)
    assert result["sales_growth"] == {"5y": 32.0, "3y": 19.0, "ttm": 20.0}
    assert result["profit_growth"] == {"5y": 32.0, "3y": 36.0, "ttm": 262.0}


def test_blank_window_is_omitted_not_zero():
    result = _parse_compounded_growth_widgets(_SAMPLE_HTML)
    assert "10y" not in result["sales_growth"]
    assert "10y" not in result["profit_growth"]


def test_ignores_stock_price_cagr_and_roe_widgets():
    result = _parse_compounded_growth_widgets(_SAMPLE_HTML)
    assert "stock_price_cagr" not in result
    assert "roe" not in result
    assert set(result.keys()) == {"sales_growth", "profit_growth"}


def test_empty_html_returns_empty_dict():
    assert _parse_compounded_growth_widgets("<html><body></body></html>") == {}
