"""Multi-year P&L ingestion — P&L Analysis System, Stage P0.

Screener.in's `profit_loss()` returns 12 years + TTM for every company
checked (TCS, Maruti, live-probed 2026-09-13) — sales, expenses (one
aggregate line, no material/employee/power-fuel breakdown — confirmed
absent from the scraped page for both an IT company and a manufacturer,
so that granularity is out of scope here, not silently faked), operating
profit, OPM, other income, interest, depreciation, PBT, tax %, net profit,
EPS, and dividend payout.

Stored into the existing `metric_store` provenance ledger (same pattern
`screener_client.py::ingest_balance_sheet` already uses for Screener's
multi-year balance sheet) rather than a new dedicated table — this gets
`metric_store.get_metric_history()`/`get_authoritative_value()` reuse for
free, and keeps every P&L figure participating in the same tier/confidence
conflict-resolution the rest of the app already relies on. Every metric_key
here is `pnl_`-prefixed specifically to guarantee no collision with any
existing key.

TTM is stored under the literal period string "TTM" (not a date) — safe
only because these pnl_ metric_keys are brand new and nothing else queries
them expecting ISO-only periods. The calc engine (Stage P1) fetches it
separately and never mixes it into a fixed-year CAGR window. Sector-agnostic
by design (works for any Screener.in company page, not just banks).

**Both statement types, since 2026-09-15** (originally consolidated-only
after a live mismatch on L&T: this module's standalone Mar-2026-quarter
sales read Rs.47,191 Cr against arthneeti.com's consolidated Rs.82,762 Cr
for the same quarter — confirmed correct on both sides, just different
scopes). `pnl_engine.py::_series` still reads `statement_type="CONSOLIDATED"`
explicitly (unchanged — every one of its existing callers keeps seeing
exactly what they always have, per the P&L Analysis Engine plan's Stage 0
"don't break the existing engine" boundary). This mirrors what
`MetricsCalculator` (app/calculations/engine.py) already gets from yfinance
for Indian tickers — confirmed live: yfinance's `financials` for LT.NS sums
to the same ballpark as arthneeti's consolidated quarters, not Screener's
standalone ones — so CONSOLIDATED stays the default read for the existing
engine.

The new `pl_intelligence/` P&L Analysis Engine's standalone-vs-consolidated
module (Stage 8 of the spec) needs STANDALONE rows too — `metric_store.py`'s
`statement_type` axis and `get_both_statement_types()` already supported
this, only this module's single-pass CONSOLIDATED-only fetch didn't. Fixed
by replicating `screener_client.py::ingest_balance_sheet`'s exact dual-loop
pattern below (`for statement_type, consolidated in (("STANDALONE", False),
("CONSOLIDATED", True))`) — purely additive: STANDALONE rows land alongside
the existing CONSOLIDATED ones, nothing that already reads CONSOLIDATED
changes behavior.

Deliberately NOT applied to `screener_client.py::ingest_quarterly_metrics`
(bank NPA/cost-to-income) — Indian banking regulatory figures (gross_npa,
net_npa, CAR, CASA) are standalone-only concepts by RBI convention; there is
no "consolidated NPA". That module is untouched.
"""
from __future__ import annotations

import calendar
import time
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.ingestion.screener_client import _SCREENER_REQUEST_DELAY_SECONDS
from app.logger import logger

SOURCE = "SCREENER"
SOURCE_TIER = 2
CONFIDENCE = "MEDIUM"

# The "Compounded Sales Growth"/"Compounded Profit Growth" mini-widget
# Screener renders directly below the main P&L table (`table.ranges-table`,
# 4 tables in a grid — Stock Price CAGR and Return on Equity are the other
# two, not scraped here as nothing in `analysis.metrics` needs them yet).
# These are SCREENER'S OWN pre-computed CAGR figures, not something we
# derive — needed because our own CAGR formula (`engine.py::calculate_cagr`,
# reused by `pnl_engine.py::_cagr_window`) returns None whenever either
# window endpoint is <= 0 (avoids a complex-number result), which blanks
# out `pat_cagr_3y` for any company with a loss-to-profit turnaround in its
# window (confirmed live on Pine Labs: CONSOLIDATED PAT was negative every
# year FY2023-FY2025, swinging positive only in FY2026). Screener's widget
# still shows a number for that case via its own undocumented methodology —
# trusting it outright, per "Screener is the primary source of truth,"
# beats reverse-engineering a formula nobody's confirmed.
_GROWTH_WIDGET_TITLES = {
    "Compounded Sales Growth": "sales_growth",
    "Compounded Profit Growth": "profit_growth",
}
_GROWTH_WIDGET_ROWS = {"10 years": "10y", "5 years": "5y", "3 years": "3y", "ttm": "ttm"}
_GROWTH_WIDGET_METRIC_KEYS = {
    ("sales_growth", "10y"): "screener_revenue_cagr_10y",
    ("sales_growth", "5y"): "screener_revenue_cagr_5y",
    ("sales_growth", "3y"): "screener_revenue_cagr_3y",
    ("sales_growth", "ttm"): "screener_revenue_cagr_ttm",
    ("profit_growth", "10y"): "screener_pat_cagr_10y",
    ("profit_growth", "5y"): "screener_pat_cagr_5y",
    ("profit_growth", "3y"): "screener_pat_cagr_3y",
    ("profit_growth", "ttm"): "screener_pat_cagr_ttm",
}


def _parse_compounded_growth_widgets(html: str) -> dict[str, dict[str, float]]:
    """Parse the `table.ranges-table` grid's Sales/Profit Growth widgets out
    of a Screener company-page HTML string. Returns e.g.
    `{"sales_growth": {"5y": 32.0, "3y": 19.0, "ttm": 20.0}, "profit_growth": {...}}`
    — a blank cell (just "%", no number, meaning Screener itself has no data
    for that window, e.g. "10 Years" for a recently-listed company) is
    simply omitted, not stored as 0."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, dict[str, float]] = {}
    for table in soup.select("table.ranges-table"):
        header = table.find("th")
        if header is None:
            continue
        widget_key = _GROWTH_WIDGET_TITLES.get(header.get_text(strip=True))
        if widget_key is None:
            continue
        rows: dict[str, float] = {}
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all("td")
            if len(cells) != 2:
                continue
            row_key = _GROWTH_WIDGET_ROWS.get(cells[0].get_text(strip=True).rstrip(":").lower())
            if row_key is None:
                continue
            value_text = cells[1].get_text(strip=True).replace("%", "")
            try:
                rows[row_key] = float(value_text)
            except ValueError:
                continue
        if rows:
            out[widget_key] = rows
    return out

# Screener field name -> (metric_key, unit). Banks/NBFCs get a DIFFERENT
# field vocabulary from Screener ("revenue"/"financing_profit"/
# "financing_margin" instead of "sales"/"operating_profit"/
# "operating_margin_percent") — real gap found live-testing on HDFCBANK
# (2026-09-13): the industrial-only map above left every bank's P&L history
# empty. Mapped to the same pnl_ keys as the industrial equivalents (same
# real-world concept — total income, core operating profit before
# non-operating items) rather than separate bank-only keys, so the
# universal 10-year table renders for every sector; banks still get their
# own dedicated NIM/CASA/credit-cost path from the banking.md framework
# elsewhere, this is only the generic P&L table/CAGR/margin view.
_FIELD_MAP = {
    "sales": ("pnl_sales", "cr"),
    "revenue": ("pnl_sales", "cr"),
    "expenses": ("pnl_expenses", "cr"),
    "operating_profit": ("pnl_operating_profit", "cr"),
    "financing_profit": ("pnl_operating_profit", "cr"),
    "operating_margin_percent": ("pnl_opm", "%"),
    "financing_margin": ("pnl_opm", "%"),
    "other_income": ("pnl_other_income", "cr"),
    "interest": ("pnl_interest", "cr"),
    "depreciation": ("pnl_depreciation", "cr"),
    "profit_before_tax": ("pnl_pbt", "cr"),
    "tax_percent": ("pnl_tax_pct", "%"),
    "net_profit": ("pnl_net_profit", "cr"),
    "eps": ("pnl_eps", "INR"),
    "dividend_payout": ("pnl_dividend_payout", "%"),
}


def _fmt_period(year_label: str) -> str | None:
    """"Mar 2026" -> "2026-03-31". Returns None for "TTM" or anything
    unparseable — caller skips those rows."""
    try:
        dt = datetime.strptime(year_label.strip(), "%b %Y")
    except ValueError:
        return None
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return date(dt.year, dt.month, last_day).isoformat()


def ingest_pnl_history(db: Session, company_id: str, symbol: str) -> list:
    """Fetch and store Screener.in's multi-year P&L for `symbol`, both
    standalone and consolidated. Never raises — logs and returns whatever it
    managed to insert (possibly empty) on failure, matching every other
    ingestion path's contract; a fetch failure on one statement type doesn't
    prevent the other from being ingested.

    2026-09-24: `_SCREENER_REQUEST_DELAY_SECONDS` between the two statement-
    type requests — real gap found live on Voltas's cash-flow schedules
    (user's own report: "Consolidated Cashflow has not been ingested...
    I've seen multiple instances like this"), root-caused to firing
    back-to-back Screener requests with zero delay and hitting Screener's
    own burst rate limit; applied here too since this function has the
    exact same two-rapid-requests shape (see
    `screener_client.py`'s module-level comment on the shared constant for
    the full incident writeup)."""
    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("pnl_history_client: openscreener not installed", symbol=symbol)
        return []

    now = datetime.now(timezone.utc)
    source_url = f"https://www.screener.in/company/{symbol}/"
    inserted = []
    years_seen = 0

    for pass_index, (statement_type, consolidated) in enumerate((("STANDALONE", False), ("CONSOLIDATED", True))):
        if pass_index > 0:
            time.sleep(_SCREENER_REQUEST_DELAY_SECONDS)
        try:
            stock = Stock(symbol, consolidated=consolidated)
            rows = stock.profit_loss()
        except Exception as e:
            logger.warning("pnl_history_client: profit_loss fetch failed", symbol=symbol,
                            statement_type=statement_type, error=str(e))
            continue

        years_seen = max(years_seen, len(rows))

        widgets = _parse_compounded_growth_widgets(stock.page_html or "")
        today = date.today().isoformat()  # snapshot-dated, same convention as screener_client.py's sr_* fields
        for (widget_key, row_key), metric_key in _GROWTH_WIDGET_METRIC_KEYS.items():
            value = widgets.get(widget_key, {}).get(row_key)
            if value is None:
                continue
            result = metric_store.insert_metric_value(
                db,
                company_id=company_id,
                metric_key=metric_key,
                period=today,
                value=value,
                unit="%",
                statement_type=statement_type,
                source=SOURCE,
                source_tier=SOURCE_TIER,
                reported_or_calculated="REPORTED",
                confidence=CONFIDENCE,
                source_url=source_url,
                source_document=f"Screener.in compounded growth widget ({statement_type.title()})",
                source_date=now,
                raw_reported_value=str(value),
            )
            if result is not None:
                inserted.append(result)

        for row in rows:
            year_label = str(row.get("year", ""))
            if year_label.upper() == "TTM":
                # Stored under the literal period "TTM", not a date — safe only
                # because these pnl_ metric_keys are new and nothing else in the
                # codebase queries them expecting ISO-only periods (unlike
                # get_latest_period_value's max()-over-dates elsewhere). The P&L
                # calc engine (app/calculations/pnl_engine.py) fetches this
                # separately and never mixes it into a CAGR window.
                period = "TTM"
            else:
                period = _fmt_period(year_label)
                if period is None:
                    continue

            for field, (metric_key, unit) in _FIELD_MAP.items():
                value = row.get(field)
                if value is None or not isinstance(value, (int, float)):
                    continue
                result = metric_store.insert_metric_value(
                    db,
                    company_id=company_id,
                    metric_key=metric_key,
                    period=period,
                    value=float(value),
                    unit=unit,
                    statement_type=statement_type,
                    source=SOURCE,
                    source_tier=SOURCE_TIER,
                    reported_or_calculated="REPORTED",
                    confidence=CONFIDENCE,
                    source_url=source_url,
                    source_document=f"Screener.in profit & loss ({statement_type.title()})",
                    source_date=now,
                    raw_reported_value=str(value),
                )
                if result is not None:
                    inserted.append(result)

    logger.info("pnl_history_client: ingested", symbol=symbol, years=years_seen, rows_inserted=len(inserted))
    return inserted
