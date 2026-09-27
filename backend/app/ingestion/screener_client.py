"""Ingests figures from Screener.in via the locally-installed `openscreener`
package (Playwright-based scraper) — both standalone and consolidated,
stored as separate rows (see metric_store.py's statement_type axis) so
neither silently overwrites or out-competes the other.

Sector-agnostic by design (openscreener works for any Screener.in stock page,
not just banks) — unlike the rest of app/ingestion/, which is banking-only.

**Screener-first ingestion order (2026-09-10)**: `orchestrator.py` now calls
this module BEFORE `banking_ingestion.py` (BSE OCR) and
`annual_report_ingestion.py` (NSE annual report) for every Banks-sector
analysis. Screener.in is fast (a Playwright scrape, no LLM call) and covers
several banking metrics directly — `gross_npa`, `net_npa`, and the full
balance sheet (`deposits`, `investments`, `total_assets`, etc.) — so those
land in the ledger immediately, without waiting on Groq or risking an
OCR misread (the kind that produced garbage 31173%/8091% NPA values earlier
in this project — see IMPLEMENTATION_PLAN.md Session 8). BSE/NSE ingestion
still runs unconditionally afterward: they're the *only* source for CASA,
PCR, slippage, CAR, ROA, CET1/Tier1, and credit_cost, none of which appear
anywhere on a standard Screener.in company page. Where both sources cover
the same field (gross_npa, net_npa), the documented trust hierarchy is
preserved, not overridden — this module intentionally stays tier=2 while
BSE/NSE stay tier=1, so a primary-filing figure still wins over Screener's
third-party aggregation when both are present for the same period; Screener
only wins when it's the *only* value on record (the common case, since BSE's
OCR pass isn't re-run once its own 24h cache gate is set).

Source tier: banking.md's own hierarchy (section 21) names Screener as a
Tier-2 cross-check source, below exchange filings/regulatory sources — so
source_tier=2, confidence="MEDIUM" (Screener.in is a third-party aggregator
parsing filings, not the filing itself).
"""
from __future__ import annotations

import calendar
import re
import time
import uuid
from datetime import date, datetime, timezone

import requests
from sqlalchemy.orm import Session

from app.config import config
from app.infrastructure.database import metric_store
from app.logger import logger

SOURCE = "SCREENER"
SOURCE_TIER = 2
CONFIDENCE = "MEDIUM"

# Delay between consecutive STANDALONE/CONSOLIDATED (and, for
# ingest_cash_flow_schedules, per-schedule-parent) requests to Screener's
# endpoints within a single ingestion call (2026-09-24, real gap found live
# on Voltas — user's own report: "Consolidated Cashflow has not been
# ingested... I've seen multiple instances like this"). Root cause: firing
# these back-to-back with zero delay was hitting Screener's own burst rate
# limit on its own traffic — confirmed live that spacing retries ~8-20s
# apart reliably succeeds where zero-delay back-to-back calls consistently
# 429'd. Applied to every function in this module (and, via import, the
# sibling `pnl_history_client.py`/`quarterly_results_client.py`) that makes
# more than one Screener request per ingestion call — see each function's
# own docstring for which specific incident/company surfaced the gap.
_SCREENER_REQUEST_DELAY_SECONDS = 1.5

# Fields that are already computed/derived by openscreener itself (not raw
# balance-sheet line items) — excluded from the generic per-row capture
# below since they're handled by their own dedicated call.
_BALANCE_SHEET_EXCLUDE = {"year"}

# Screener.in summary()'s "top ratios" strip (Stock.summary()["ratios"]) —
# the headline P/E, Book Value, Dividend Yield, Market Cap Screener shows at
# the top of every company page. Previously scraped (as part of the same
# summary() call already made for `about`/`key_points`) and discarded.
# `sr_` = "summary ratios", distinct from `bs_ratio_` (ingest_ratios(), the
# separate .ratios() endpoint's debtor-days/inventory-days/etc — a DIFFERENT
# Screener page section). `roce_percent`/`roe_percent` here are ingested for
# observability/cross-check only, deliberately NOT wired into
# screener_metrics_override.py's override table — pnl_engine.py/roce.py
# already give better-sourced equivalents with full formula control, not
# just a headline number.
_SR_FIELDS = {
    "market_cap": ("sr_market_cap", "cr"),
    "current_price": ("sr_current_price", "INR"),
    "stock_p_e": ("sr_pe_ratio", "x"),
    "book_value": ("sr_book_value", "INR"),
    "dividend_yield": ("sr_dividend_yield", "%"),
    "face_value": ("sr_face_value", "INR"),
    "roce_percent": ("sr_roce_percent", "%"),
    "roe_percent": ("sr_roe_percent", "%"),
}


def _fmt_period(year_label: str) -> str:
    """"Mar 2026" -> "2026-03-31" — the last calendar day of the given month
    (Screener's balance sheet rows are always month-end snapshots; this
    doesn't hardcode "31" since not every month has one)."""
    try:
        dt = datetime.strptime(year_label.strip(), "%b %Y")
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        return date(dt.year, dt.month, last_day).isoformat()
    except ValueError:
        return year_label


def ingest_balance_sheet(db: Session, company_id: str, symbol: str) -> list:
    """Fetch both standalone and consolidated balance sheets for `symbol`
    from Screener.in and store every line item Screener reports, every year,
    tagged with the correct statement_type. Every key openscreener's generic
    row parser returns is stored as its own metric_key (no fixed allowlist)
    — this is what makes bank-specific rows like `deposits` and `borrowing`
    (present on a bank's balance sheet, absent on a non-financial company's)
    land automatically, without hardcoding a sector-specific field list in a
    module that's otherwise sector-agnostic by design. Never raises — logs
    and returns an empty list on failure, matching every other ingestion
    path's contract.

    2026-09-24: `_SCREENER_REQUEST_DELAY_SECONDS` between the two statement-
    type requests — see that constant's own module-level comment for the
    rate-limit incident (Voltas cash-flow schedules) this same fix pattern
    was applied everywhere else for."""
    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("screener_client: openscreener not installed", symbol=symbol)
        return []

    inserted = []
    now = datetime.now(timezone.utc)
    source_url = f"https://www.screener.in/company/{symbol}/"

    for pass_index, (statement_type, consolidated) in enumerate((("STANDALONE", False), ("CONSOLIDATED", True))):
        if pass_index > 0:
            time.sleep(_SCREENER_REQUEST_DELAY_SECONDS)
        try:
            stock = Stock(symbol, consolidated=consolidated)
            rows = stock.balance_sheet()
        except Exception as e:
            logger.warning("screener_client: balance_sheet fetch failed", symbol=symbol,
                            statement_type=statement_type, error=str(e))
            continue

        for row in rows:
            period = _fmt_period(row.get("year", ""))
            for field, value in row.items():
                if field in _BALANCE_SHEET_EXCLUDE or value is None:
                    continue
                if not isinstance(value, (int, float)):
                    continue
                row = metric_store.insert_metric_value(
                    db,
                    company_id=company_id,
                    metric_key=field,
                    period=period,
                    value=float(value),
                    unit="cr",
                    statement_type=statement_type,
                    source=SOURCE,
                    source_tier=SOURCE_TIER,
                    reported_or_calculated="REPORTED",
                    confidence=CONFIDENCE,
                    source_url=source_url,
                    source_document=f"Screener.in balance sheet ({statement_type.title()})",
                    source_date=now,
                    raw_reported_value=str(value),
                )
                if row is not None:
                    inserted.append(row)

    logger.info("screener_client: balance sheet ingested", symbol=symbol, rows_inserted=len(inserted))
    return inserted


# Balance Sheet Analysis Engine, Milestone 1 — every key openscreener's
# `cash_flow()` row returns is stored (same generic-row-capture style as
# `ingest_balance_sheet()` above), prefixed `cf_` so it reads distinctly from
# both this module's own `pnl_*` prefix and the balance-sheet engine's own
# computed `bs_*` metrics in the same ledger.
_CASH_FLOW_EXCLUDE = {"year"}


def ingest_cash_flow(db: Session, company_id: str, symbol: str) -> list:
    """Fetch both standalone and consolidated cash-flow statements for
    `symbol` from Screener.in — operating/investing/financing/net/free cash
    flow, ~12 years. Not previously ingested anywhere in this app (confirmed
    by grep before writing this): the balance sheet and P&L history both
    already had dedicated ingestors, cash flow didn't. Needed for the
    Balance Sheet Analysis Engine's CFO-based red flags (CFO vs. PAT
    divergence, capex without cash generation) — never raises, logs and
    returns an empty list on failure, matching every other ingestion path
    in this module.

    2026-09-24: `_SCREENER_REQUEST_DELAY_SECONDS` between the two statement-
    type requests — see that constant's own module-level comment."""
    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("screener_client: openscreener not installed", symbol=symbol)
        return []

    inserted = []
    now = datetime.now(timezone.utc)
    source_url = f"https://www.screener.in/company/{symbol}/"

    for pass_index, (statement_type, consolidated) in enumerate((("STANDALONE", False), ("CONSOLIDATED", True))):
        if pass_index > 0:
            time.sleep(_SCREENER_REQUEST_DELAY_SECONDS)
        try:
            stock = Stock(symbol, consolidated=consolidated)
            rows = stock.cash_flow()
        except Exception as e:
            logger.warning("screener_client: cash_flow fetch failed", symbol=symbol,
                            statement_type=statement_type, error=str(e))
            continue

        for row in rows:
            period = _fmt_period(row.get("year", ""))
            for field, value in row.items():
                if field in _CASH_FLOW_EXCLUDE or value is None:
                    continue
                if not isinstance(value, (int, float)):
                    continue
                inserted_row = metric_store.insert_metric_value(
                    db,
                    company_id=company_id,
                    metric_key=f"cf_{field}",
                    period=period,
                    value=float(value),
                    unit="cr",
                    statement_type=statement_type,
                    source=SOURCE,
                    source_tier=SOURCE_TIER,
                    reported_or_calculated="REPORTED",
                    confidence=CONFIDENCE,
                    source_url=source_url,
                    source_document=f"Screener.in cash flow ({statement_type.title()})",
                    source_date=now,
                    raw_reported_value=str(value),
                )
                if inserted_row is not None:
                    inserted.append(inserted_row)

    logger.info("screener_client: cash flow ingested", symbol=symbol, rows_inserted=len(inserted))
    return inserted


# Cash Flow Analysis Engine, Milestone 1 — Screener.in's own "Schedule"
# breakdown for each cash-flow parent row (Operating/Investing/Financing
# Activity). Not part of `openscreener`'s public API — found by reading
# Screener's own frontend JS bundles (`company.customisation.js`'s
# `showSchedule()`, `utils.js`'s `getUrls()`), which call
# `GET /api/company/{companyId}/schedules/?parent=<row>&section=cash-flow
# [&consolidated=]`. This is an UNDOCUMENTED internal endpoint, not a
# published API contract — it could change shape or start blocking
# non-browser requests without notice. Every call here is wrapped the same
# try/except-log-and-return-empty way every other ingestion path in this
# module already is, so a break in this endpoint degrades this feature
# gracefully (falls back to whatever was last successfully ingested) rather
# than failing the pipeline. Confirmed live for Maruti and Lenskart
# (2026-09-16): returns the full line-item breakdown — receivables/
# inventory/payables cash impact, gross debt raised/repaid separately
# (yfinance only ever gives a net issuance figure), capex, dividends — in
# Crores, ~12 years, matching this app's other Screener-sourced units
# exactly (no repeat of the Rupees-vs-Crores mismatch found earlier this
# session when blending Screener with yfinance).
_SCHEDULE_PARENTS = (
    "Cash from Operating Activity",
    "Cash from Investing Activity",
    "Cash from Financing Activity",
)
_SCHEDULE_KEY_PREFIX = {
    "Cash from Operating Activity": "cf_sched_op_",
    "Cash from Investing Activity": "cf_sched_inv_",
    "Cash from Financing Activity": "cf_sched_fin_",
}
# Not a real data row — a display hint Screener attaches to the "total"
# row of each schedule (e.g. "Working capital changes", "Profit from
# operations") for bold-styling on their own page. Never a metric.
_SCHEDULE_META_KEYS = {"setAttributes"}
_SCHEDULE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}


def _extract_screener_company_id(html: str) -> str | None:
    """Screener's internal numeric company ID (e.g. Maruti=2023,
    Lenskart=1285752) — needed for the schedules endpoint, not exposed by
    any `openscreener.Stock` property, only present in the rendered page's
    `data-company-id` attribute."""
    match = re.search(r'data-company-id="(\d+)"', html)
    return match.group(1) if match else None


def _parse_schedule_value(raw) -> float | None:
    """Schedule values arrive as comma-formatted strings ("1,236", "-40",
    "-0") or occasionally nested dicts (`setAttributes`) — only the
    former is a real number."""
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str):
        return None
    cleaned = raw.replace(",", "").strip()
    if not cleaned or cleaned in ("-", "—"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _fetch_schedule(company_id: str, parent: str, consolidated: bool) -> dict:
    """One GET to the schedules endpoint. Never raises — returns {} on any
    failure (network, non-200, unparseable JSON), matching this module's
    established never-raise ingestion contract."""
    params = {"parent": parent, "section": "cash-flow"}
    if consolidated:
        params["consolidated"] = ""
    try:
        resp = requests.get(
            f"https://www.screener.in/api/company/{company_id}/schedules/",
            params=params, headers=_SCHEDULE_HEADERS, timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("screener_client: schedule fetch failed", company_id=company_id,
                        parent=parent, consolidated=consolidated, error=str(e))
        return {}


def ingest_cash_flow_schedules(db: Session, company_id: str, symbol: str) -> list:
    """Fetch the CFO/CFI/CFF line-item "Schedule" breakdown for `symbol`
    from Screener.in's internal schedules API (see module comment above)
    — receivables/inventory/payables cash impact, capex, gross debt
    raised/repaid, dividends, etc., ~12 years, both statement types. Field
    names vary per company (confirmed live: Lenskart has an "Exceptional CF
    items" row Maruti doesn't) — every key returned is captured generically,
    no fixed allowlist, same discipline as `ingest_balance_sheet()`. Never
    raises — logs and returns an empty list on failure.

    **Self-inflicted rate-limit fix (2026-09-24)**: real gap found live on
    Voltas (user's own report — "Consolidated Cashflow has not been
    ingested... I've seen multiple instances like this") and, once checked,
    16 other already-analyzed companies (ACE, Apollo Hospitals, Bajaj
    Finance, GNFC, GPT Healthcare, Groww, Kross, Max Healthcare, Metro
    Brands, Netweb, Pidilite, Shree Cement, Tanla, Welspun Corp, Zydus
    Lifesciences — 14 of these were genuine transient gaps and got
    backfilled the same day; Bandhan Bank/Kross/Netweb are confirmed live
    to have no consolidated data on Screener at all, a real business fact
    not a bug). Root cause: this function fires 6 requests back-to-back
    with zero delay (2 `stock.cash_flow()` page loads + 6
    `_fetch_schedule()` calls to the SAME rate-limited endpoint family) —
    it was hitting Screener's own burst rate limit on its OWN traffic, not
    from other companies' pipeline runs colliding. The existing
    `_CONSOLIDATED_GAP_RETRY_TTL` mechanism in orchestrator.py (4h) only
    retries the NEXT time this company is analyzed — it doesn't prevent
    the gap on THIS run. A small delay between each schedule call fixes it
    at the source: manually verified live that spacing individual retries
    ~8-20s apart reliably succeeds where zero-delay back-to-back calls
    consistently 429'd."""
    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("screener_client: openscreener not installed", symbol=symbol)
        return []

    inserted = []
    now = datetime.now(timezone.utc)
    source_url = f"https://www.screener.in/company/{symbol}/"

    for pass_index, (statement_type, consolidated) in enumerate((("STANDALONE", False), ("CONSOLIDATED", True))):
        if pass_index > 0:
            time.sleep(_SCREENER_REQUEST_DELAY_SECONDS)
        try:
            stock = Stock(symbol, consolidated=consolidated)
            stock.cash_flow()  # triggers the page fetch that populates page_html below
            screener_company_id = _extract_screener_company_id(stock.page_html)
        except Exception as e:
            logger.warning("screener_client: schedule page fetch failed", symbol=symbol,
                            statement_type=statement_type, error=str(e))
            continue
        if not screener_company_id:
            logger.warning("screener_client: could not resolve Screener company_id for schedules",
                            symbol=symbol, statement_type=statement_type)
            continue

        for parent_index, parent in enumerate(_SCHEDULE_PARENTS):
            if parent_index > 0:
                time.sleep(_SCREENER_REQUEST_DELAY_SECONDS)
            schedule = _fetch_schedule(screener_company_id, parent, consolidated)
            prefix = _SCHEDULE_KEY_PREFIX[parent]
            for field, periods in schedule.items():
                if field in _SCHEDULE_META_KEYS or not isinstance(periods, dict):
                    continue
                metric_key = prefix + re.sub(r"[^a-z0-9]+", "_", field.lower()).strip("_")
                for period_label, raw_value in periods.items():
                    value = _parse_schedule_value(raw_value)
                    if value is None:
                        continue
                    period = _fmt_period(period_label)
                    inserted_row = metric_store.insert_metric_value(
                        db,
                        company_id=company_id,
                        metric_key=metric_key,
                        period=period,
                        value=value,
                        unit="cr",
                        statement_type=statement_type,
                        source=SOURCE,
                        source_tier=SOURCE_TIER,
                        reported_or_calculated="REPORTED",
                        confidence=CONFIDENCE,
                        source_url=source_url,
                        source_document=f"Screener.in cash flow schedule — {parent} ({statement_type.title()})",
                        source_date=now,
                        raw_reported_value=str(raw_value),
                    )
                    if inserted_row is not None:
                        inserted.append(inserted_row)

    logger.info("screener_client: cash flow schedules ingested", symbol=symbol, rows_inserted=len(inserted))
    return inserted


# Balance Sheet Analysis Engine, Milestone 1 — Screener's own precomputed
# DSO/inventory-days/DPO/CCC/ROCE. Unlike `balance_sheet()`/`cash_flow()`,
# `.ratios()` returns a single dict (LATEST YEAR ONLY, not a list of yearly
# rows) — confirmed live: a normal company returns
# `{year, debtor_days, inventory_days, days_payable, cash_conversion_cycle,
# working_capital_days, roce_percent}`, a bank returns only
# `{year, roe_percent}` (Screener's own ratios page doesn't compute the
# manufacturing-style working-capital ratios for financial institutions).
# Stored under a `bs_ratio_` prefix — this is a same-methodology CROSS-CHECK
# against the balance-sheet engine's own blended (mostly yfinance-sourced)
# working-capital series, not the series' source of truth; the engine must
# never silently prefer one over the other, only surface both.
_RATIOS_EXCLUDE = {"year"}
_RATIOS_UNIT = {
    "debtor_days": "days", "inventory_days": "days", "days_payable": "days",
    "cash_conversion_cycle": "days", "working_capital_days": "days",
    "roce_percent": "%", "roe_percent": "%",
}


def ingest_ratios(db: Session, company_id: str, symbol: str) -> list:
    """Fetch Screener.in's own ratio computations (debtor days, inventory
    days, days payable, cash conversion cycle, working capital days,
    ROCE) for every year on record, both standalone and consolidated.
    Never raises — logs and returns an empty list on failure.

    Real gap found live on GROWW (2026-09-22, user's own report — "But we
    can take ROCE directly from screener right?"): this used to call
    `stock.ratios()`, which only ever returns the LATEST year — not
    because Screener's Ratios section only has one year (confirmed live:
    it's a real multi-year table, same "Mar 2022 .. Mar 2026" column
    layout as Balance Sheet/P&L), but because openscreener's own
    `parse_ratios()` discarded every year but the last one before this fix
    (`openscreener/parsers/ratios_parser.py`, same vendored package this
    project already patches elsewhere). `stock.ratios_history()` is the
    new method exposing the full table; this now stores every year it
    returns, the same "one ledger row per (metric, period, statement_type)"
    shape `ingest_balance_sheet()`/`ingest_cash_flow()` already use — so a
    multi-year Screener-sourced ROCE% trend becomes available wherever
    `bs_ratio_roce_percent` is read, not just a single latest-period
    cross-check point.

    2026-09-24: `_SCREENER_REQUEST_DELAY_SECONDS` between the two statement-
    type requests — see that constant's own module-level comment."""
    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("screener_client: openscreener not installed", symbol=symbol)
        return []

    inserted = []
    now = datetime.now(timezone.utc)
    source_url = f"https://www.screener.in/company/{symbol}/"

    for pass_index, (statement_type, consolidated) in enumerate((("STANDALONE", False), ("CONSOLIDATED", True))):
        if pass_index > 0:
            time.sleep(_SCREENER_REQUEST_DELAY_SECONDS)
        try:
            stock = Stock(symbol, consolidated=consolidated)
            rows = stock.ratios_history()
        except Exception as e:
            logger.warning("screener_client: ratios fetch failed", symbol=symbol,
                            statement_type=statement_type, error=str(e))
            continue

        for row in rows:
            period = _fmt_period(str(row.get("year", "")))
            for field, value in row.items():
                if field in _RATIOS_EXCLUDE or value is None:
                    continue
                if not isinstance(value, (int, float)):
                    continue
                inserted_row = metric_store.insert_metric_value(
                    db,
                    company_id=company_id,
                    metric_key=f"bs_ratio_{field}",
                    period=period,
                    value=float(value),
                    unit=_RATIOS_UNIT.get(field, ""),
                    statement_type=statement_type,
                    source=SOURCE,
                    source_tier=SOURCE_TIER,
                    reported_or_calculated="REPORTED",
                    confidence=CONFIDENCE,
                    source_url=source_url,
                    source_document=f"Screener.in ratios ({statement_type.title()})",
                    source_date=now,
                    raw_reported_value=str(value),
                )
                if inserted_row is not None:
                    inserted.append(inserted_row)

    logger.info("screener_client: ratios ingested", symbol=symbol, rows_inserted=len(inserted))
    return inserted


def ingest_quarterly_metrics(db: Session, company_id: str, symbol: str) -> list:
    """Fetch the latest standalone quarter from Screener.in's "Quarterly
    Results" section and store what it directly reports for banks:
    `gross_npa` and `net_npa` (Screener shows both as ready-made percentages
    — no OCR, no LLM extraction, no digit-misread risk). Also derives
    `cost_to_income_ratio` from the same quarter's P&L components (opex /
    (net interest income + other income) * 100) — confidence MEDIUM, one
    notch above the equivalent OCR-derived calculation in
    banking_ingestion.py, since these inputs come from Screener's parsed
    numeric table rather than an OCR pass over a scanned PDF.

    Nothing else banking.md needs (CASA, PCR, slippage, CAR, ROA, CET1,
    Tier1, credit_cost) appears in Screener's quarterly results for a bank —
    those stay BSE/NSE-only. Never raises — logs and returns an empty list
    on failure."""
    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("screener_client: openscreener not installed", symbol=symbol)
        return []

    try:
        stock = Stock(symbol, consolidated=False)
        quarters = stock.quarterly_results()
    except Exception as e:
        logger.warning("screener_client: quarterly_results fetch failed", symbol=symbol, error=str(e))
        return []

    # Screener's last row is sometimes "TTM" (trailing twelve months) rather
    # than a real quarter — skip it and take the latest dated quarter.
    dated = [q for q in quarters if q.get("date") and str(q["date"]).upper() != "TTM"]
    if not dated:
        return []
    latest = dated[-1]

    inserted = []
    now = datetime.now(timezone.utc)
    source_url = f"https://www.screener.in/company/{symbol}/"
    period = _fmt_period(str(latest.get("date", "")))
    source_document = "Screener.in quarterly results (Standalone)"

    for metric_key in ("gross_npa", "net_npa"):
        value = latest.get(metric_key)
        if value is None:
            continue
        row = metric_store.insert_metric_value(
            db,
            company_id=company_id,
            metric_key=metric_key,
            period=period,
            value=float(value),
            unit="%",
            source=SOURCE,
            source_tier=SOURCE_TIER,
            reported_or_calculated="REPORTED",
            confidence=CONFIDENCE,
            source_url=source_url,
            source_document=source_document,
            source_date=now,
            raw_reported_value=str(value),
        )
        if row is not None:
            inserted.append(row)

    revenue = latest.get("revenue")   # interest earned
    interest = latest.get("interest")  # interest expended
    opex = latest.get("expenses")
    other_income = latest.get("other_income")
    if None not in (revenue, interest, opex, other_income):
        nii = revenue - interest
        denom = nii + other_income
        if denom:
            row = metric_store.insert_metric_value(
                db,
                company_id=company_id,
                metric_key="cost_to_income_ratio",
                period=period,
                value=round(opex / denom * 100, 2),
                unit="%",
                source="CALCULATED",
                source_tier=SOURCE_TIER,
                reported_or_calculated="CALCULATED",
                confidence=CONFIDENCE,
                calculation_formula="expenses / ((revenue - interest) + other_income) * 100, "
                                     "from Screener.in's latest-quarter P&L",
                source_url=source_url,
                source_document=source_document,
                source_date=now,
            )
            if row is not None:
                inserted.append(row)

    logger.info("screener_client: quarterly metrics ingested", symbol=symbol, rows_inserted=len(inserted))
    return inserted


_SCREENER_BASE = "https://www.screener.in"


def _fetch_full_key_points(symbol: str) -> str | None:
    """Logs into Screener.in (SCREENER_EMAIL/SCREENER_PASSWORD) and fetches
    the full "Key Points" commentary — the anonymous page only renders the
    first section (e.g. "Solutions Offered") with a "Read More" button whose
    `data-url` points at a login-gated `/wiki/company/{id}/commentary/v2/`
    page holding the rest (Brand Value, Revenue Mix, Clientele, etc.).

    That URL can't just be `goto()`'d directly, even authenticated — it's an
    AJAX-only Django view that 302s back to the company page for a normal
    top-level navigation (confirmed live, 2026-09-14: `goto()` returns
    status 200 but lands back on /company/.../consolidated/). The button's
    `onclick="Modal.openInModal(event)"` is what actually fires the right
    request and injects the result into an on-page modal, so this clicks the
    button for real and reads the modal's rendered text instead — confirmed
    to return the exact full multi-section content (Brand Value, Revenue
    Mix, Infrastructure, Clientele, Order Book, Workforce, Partnerships,
    Acquisition, Focus, etc.) byte-for-byte.

    Returns None (never raises) if credentials aren't configured, login
    fails, or no Read More link exists (some companies' Key Points fit in
    the free preview with nothing more to read)."""
    if not config.screener_email or not config.screener_password:
        return None

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("screener_client: playwright not installed, skipping full key points")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(f"{_SCREENER_BASE}/login/", wait_until="domcontentloaded", timeout=30000)
                page.fill("#id_username", config.screener_email)
                page.fill("#id_password", config.screener_password)
                page.click("button[type=submit]")
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                if "/login/" in page.url:
                    logger.warning("screener_client: Screener.in login failed", symbol=symbol)
                    return None

                page.goto(
                    f"{_SCREENER_BASE}/company/{symbol.upper()}/consolidated/",
                    wait_until="domcontentloaded", timeout=30000,
                )
                page.wait_for_selector("#top", timeout=30000)
                read_more = page.query_selector("button[data-url*='/wiki/company/']")
                if read_more is None:
                    return None  # no further sections beyond the free preview

                read_more.click()
                page.wait_for_selector(".modal, [role=dialog], #modal-content, .modal-content", timeout=15000)
                page.wait_for_timeout(500)  # let the modal's content finish rendering
                modal = page.query_selector(".modal, [role=dialog], #modal-content, .modal-content")
                text = modal.inner_text() if modal else None
            finally:
                browser.close()
    except Exception as e:
        logger.warning("screener_client: full key points fetch failed", symbol=symbol, error=str(e))
        return None

    if not text:
        return None
    # The modal repeats the ABOUT section (already captured separately) and
    # ends with edit/copyright chrome — keep only the KEY POINTS body.
    start = text.find("KEY POINTS")
    if start != -1:
        text = text[start + len("KEY POINTS"):]
        text = text.split("[ edit ]", 1)[-1] if "[ edit ]" in text[:20] else text
    end = text.find("Last edited")
    if end != -1:
        text = text[:end]
    text = text.strip()
    return text or None


def _is_key_points_paywall(text: str | None) -> bool:
    """Screener.in's own unauthenticated preview sometimes renders its
    upsell copy ("Please upgrade to premium to read more key insights...")
    inside the same `commentary` div real key-points content would occupy —
    confirmed live on Netweb Technologies. Nothing upstream (the vendored
    `openscreener` parser, this ingestion function) distinguished that from
    genuine content, so it was captured verbatim and shown to users under
    a "Key Points" heading. Detect it here so it's treated as no-content,
    matching how `_fetch_full_key_points` failing is already treated."""
    if not text:
        return False
    return "upgrade to premium" in text.lower()


def ingest_company_summary(db, company_id: str, symbol: str):
    """Fetch Screener.in's free-text company description (`about`) and
    `key_points` — which for many companies (confirmed on TCS) includes a
    real revenue-mix breakdown in prose, e.g. "BFSI: 31.9%, Consumer
    Business: 15.4%...". Not a numeric metric, stored in the separate
    company_summary table (one row per company, upserted). Used both as
    MCP/API context and injected into the HTML/PDF report's overview
    section. Sector-agnostic — every Screener.in company page has this.

    Also persists the same `summary()` call's `ratios` sub-dict (P/E, Book
    Value, Dividend Yield, Market Cap — see `_SR_FIELDS`) into the metric
    ledger under `sr_*` keys, reusing this single fetch rather than
    re-scraping the page a second time. These are snapshot-dated (today's
    date), not fiscal-year-dated — P/E and market cap move daily, unlike
    `pnl_*`/balance-sheet fields.

    Real bug found live 2026-09-21 (Apollo Hospitals): this used to call
    `Stock(symbol, consolidated=False)` — the STANDALONE page
    (screener.in/company/{symbol}/) — while writing every `sr_*` row with
    `statement_type="CONSOLIDATED"` regardless, on the old (wrong) claim
    that Screener's top-ratio strip "isn't standalone/consolidated-
    specific". It very much is: confirmed live, `consolidated=False` gave
    stock_p_e=83.0/book_value=693 for Apollo Hospitals, while
    `consolidated=True` gave 62.3/659 — exactly matching Screener's own
    live consolidated-view page. Standalone Apollo excludes the ~60%-of-
    consolidated-revenue Digital Health & Pharmacy Distribution segment
    from its earnings base, so its P/E, book value and (via
    `screener_metrics_override.py`'s P/B derivation) every downstream
    consumer of these `sr_*` fields was silently valuing the wrong entity.
    Now fetches the CONSOLIDATED page, matching the label these rows have
    always carried and the CONSOLIDATED-preferring convention every other
    intelligence engine in this codebase already uses.

    Never raises — logs and returns None on failure."""
    from app.infrastructure.database.models import CompanySummary

    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("screener_client: openscreener not installed", symbol=symbol)
        return None

    try:
        stock = Stock(symbol, consolidated=True)
        summary = stock.summary()
    except Exception as e:
        logger.warning("screener_client: summary fetch failed", symbol=symbol, error=str(e))
        return None

    about = summary.get("about") if isinstance(summary, dict) else None
    key_points = summary.get("key_points") if isinstance(summary, dict) else None
    if _is_key_points_paywall(key_points):
        key_points = None

    ratios = summary.get("ratios") if isinstance(summary, dict) else None
    if isinstance(ratios, dict):
        now_sr = datetime.now(timezone.utc)
        source_url = f"https://www.screener.in/company/{symbol}/"
        period = now_sr.date().isoformat()
        for src_field, (metric_key, unit) in _SR_FIELDS.items():
            value = ratios.get(src_field)
            if not isinstance(value, (int, float)):
                continue
            metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=metric_key, period=period,
                value=float(value), unit=unit, statement_type="CONSOLIDATED",
                source=SOURCE, source_tier=SOURCE_TIER, reported_or_calculated="REPORTED",
                confidence=CONFIDENCE, source_url=source_url,
                source_document="Screener.in summary (top ratios)", source_date=now_sr,
            )
        db.flush()

    if not about and not key_points:
        return None

    # Swap the free preview for the full multi-section commentary when a
    # Screener.in login is configured — silently keeps the preview otherwise.
    full_key_points = _fetch_full_key_points(symbol)
    if full_key_points and not _is_key_points_paywall(full_key_points):
        key_points = full_key_points

    now = datetime.now(timezone.utc)
    existing = db.query(CompanySummary).filter_by(company_id=company_id).first()
    if existing:
        existing.about = about
        existing.key_points = key_points
        existing.retrieved_at = now
        row = existing
    else:
        row = CompanySummary(
            id=str(uuid.uuid4()), company_id=company_id, about=about,
            key_points=key_points, source=SOURCE, retrieved_at=now,
        )
        db.add(row)
    db.flush()
    logger.info("screener_client: company summary ingested", symbol=symbol,
                has_about=bool(about), has_key_points=bool(key_points))
    return row
