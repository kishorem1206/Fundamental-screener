"""Working capital / liquidity ratios (spec §32-34).

**Source priority (rewritten 2026-09-23, explicit user directive — "Screener's
consolidated values should be the first preference and yfinance should be
the fallback"): Screener's `.ratios()` value is authoritative for EVERY
fiscal year it covers, overriding yfinance's value for that same year, not
just the latest one. yfinance-sourced multi-year series (`app/calculations/
engine.py::MetricsCalculator`, persisted on `FundamentalAnalysis.metrics`)
only fill in years Screener genuinely has nothing for.

This module originally (same day) merged Screener in as a single-latest-
period override, on the belief Screener's `.ratios()` endpoint only ever
exposes the latest year. That belief was wrong — the user's own screenshot
of Screener's Ratios tab showed 11 years of Debtor Days/Cash Conversion
Cycle/ROCE%, and `ingest_ratios()` was already rewritten earlier this
session to fetch that full history via `openscreener`'s `ratios_history()`
(see `snapshot.screener_ratios_history()`'s own docstring) — the ledger had
the full multi-year data sitting in it all along; this module just wasn't
reading past the latest point. Now every fiscal year Screener covers is
merged in, not just one.

DSO/DPO here use CLOSING balances over TOTAL revenue (not average balances
over credit sales/purchases — neither source separates either) — the
spec's own documented fallback, disclosed via `METHODOLOGY` on every
output so no downstream consumer misrepresents it as the CFO framework's
preferred formula.

**`single_period_fallback[label] = True`** means "the LATEST period's value
came from Screener" (kept as a latest-period-only flag for the existing
UI/PDF "Screener (preferred)" badge — see `latest_cross_check` for the full
per-year picture isn't exposed today, only the latest year's yfinance-vs-
Screener comparison is). `latest_cross_check[label]` carries both raw
values for the latest year plus `divergence_pct`.

Current Ratio has no equivalent Screener source and never will: confirmed
against the vendored `openscreener` parser's `_LABEL_MAP` that Screener's
Ratios page has no "Current Ratio" row at all (it only carries Debtor/
Inventory/Payable Days, Cash Conversion Cycle, Working Capital Days, ROCE,
ROE), and Screener's raw balance-sheet section doesn't split current vs.
non-current assets/liabilities either — so there is no Screener-sourced
number to prefer. Current Ratio is genuinely yfinance-only."""
from __future__ import annotations

import re

METHODOLOGY = "CLOSING_BALANCE_OVER_TOTAL_REVENUE"

# yfinance-blend series key -> Screener .ratios() history field (see
# canonical_fields.CANONICAL_FIELD_TO_RATIOS_KEY)
_CROSS_CHECK_PAIRS = (
    ("dso", "receivable_days_series", "debtor_days"),
    ("dio", "inventory_days_series", "inventory_days"),
    ("dpo", "payable_days_series", "days_payable"),
    ("ccc", "ccc_series", "cash_conversion_cycle"),
)

_YEAR_RE = re.compile(r"(\d{4})")


def _fiscal_year(period: str) -> str | None:
    """"2026-03-31" and "FY2026" both -> "2026" — yfinance-sourced series
    key by the latter, Screener/ledger periods by the former (same
    convention `snapshot.fiscal_year()` already documents; duplicated here
    as a tiny pure regex rather than importing snapshot.py, keeping this
    module's "no cross-module coupling" discipline intact)."""
    match = _YEAR_RE.search(period)
    return match.group(1) if match else None


def _key_for_year(series: dict, year: str) -> str | None:
    for key in series:
        if _fiscal_year(key) == year:
            return key
    return None


def _value_for_year(series: dict, year: str | None) -> float | None:
    if year is None:
        return None
    for key, value in series.items():
        if _fiscal_year(key) == year:
            return value
    return None


def _merge_screener_primary(yfinance_series: dict, screener_series: dict) -> dict:
    """Merge two period-keyed series, Screener winning for every fiscal
    year it covers. A Screener value lands on the SAME key yfinance
    already uses for that fiscal year when one exists (keeps the merged
    series internally consistent, one key per year) — otherwise it's
    added under Screener's own period key, extending the series with a
    year yfinance didn't have at all."""
    merged = dict(yfinance_series)
    year_to_key: dict[str, str] = {}
    for key in yfinance_series:
        year = _fiscal_year(key)
        if year is not None:
            year_to_key.setdefault(year, key)
    for period, value in screener_series.items():
        year = _fiscal_year(period)
        if year is None:
            continue
        merged[year_to_key.get(year, period)] = value
    return merged


def compute_working_capital_blend(metrics: dict, screener_ratios_history: dict) -> dict:
    """`metrics` is the persisted `MetricsCalculator.compute_all()` output
    (`FundamentalAnalysis.metrics`) — passed in by the orchestrator, never
    fetched here (this package has no yfinance access of its own, matching
    every other module's "no DB/network access outside snapshot.py"
    discipline, extended here to "no yfinance access outside the pipeline's
    existing `compute_metrics()` call"). `screener_ratios_history` is
    `snapshot.screener_ratios_history()`'s output: {canonical_field:
    {period: value}} for every year Screener has, merged in year-by-year
    as the primary source per the module docstring's "Source priority"
    note."""
    dso_yf = dict(metrics.get("receivable_days_series") or {})
    dio_yf = dict(metrics.get("inventory_days_series") or {})
    dpo_yf = dict(metrics.get("payable_days_series") or {})
    ccc_yf = dict(metrics.get("ccc_series") or {})
    current_ratio_series = metrics.get("curr_ratio_series") or {}
    quick_ratio_series = metrics.get("quick_ratio_series") or {}
    cash_ratio_series = metrics.get("cash_ratio_series") or {}

    yfinance_by_label = {"dso": dso_yf, "dio": dio_yf, "dpo": dpo_yf, "ccc": ccc_yf}
    all_series = {
        label: _merge_screener_primary(yfinance_by_label[label], screener_ratios_history.get(ratios_key, {}))
        for label, _series_key, ratios_key in _CROSS_CHECK_PAIRS
    }

    # Reconcile the OVERALL latest fiscal year onto ONE shared key across
    # all 4 series. Each series above was merged independently, so two
    # metrics can land on different key formats for the SAME year (e.g.
    # DSO reuses yfinance's "FY2026" because yfinance had DSO data, while
    # CCC gets Screener's ISO "2026-03-31" because yfinance had no CCC
    # series at all) — a raw `max()`/`.get(latest_period)` lookup across
    # series would then silently miss real data in whichever series uses
    # the "other" format for that year (confirmed by a real test failure
    # while building this: the CCC-recompute block below couldn't find a
    # DIO value that was genuinely there, just under a different key).
    all_years = {_fiscal_year(k) for s in all_series.values() for k in s if _fiscal_year(k) is not None}
    latest_year = max(all_years) if all_years else None
    latest_period = None
    if latest_year is not None:
        for series in all_series.values():
            latest_period = _key_for_year(series, latest_year)
            if latest_period is not None:
                break
        for series in all_series.values():
            existing_key = _key_for_year(series, latest_year)
            if existing_key is not None and existing_key != latest_period:
                series[latest_period] = series.pop(existing_key)

    latest_cross_check: dict[str, dict] = {}
    single_period_fallback: dict[str, bool] = {}
    if latest_period is not None:
        for label, _series_key, ratios_key in _CROSS_CHECK_PAIRS:
            yfinance_value = _value_for_year(yfinance_by_label[label], latest_year)
            screener_value = _value_for_year(screener_ratios_history.get(ratios_key, {}), latest_year)
            divergence_pct = None
            if yfinance_value is not None and screener_value is not None and yfinance_value:
                divergence_pct = round(abs(yfinance_value - screener_value) / abs(yfinance_value) * 100, 2)
            latest_cross_check[label] = {
                "yfinance": yfinance_value,
                "screener_latest": screener_value,
                "divergence_pct": divergence_pct,
            }
            if screener_value is not None:
                single_period_fallback[label] = True

    dso_series, dio_series, dpo_series, ccc_series = (
        all_series["dso"], all_series["dio"], all_series["dpo"], all_series["ccc"],
    )
    # CCC itself may need recomputing for the latest period when DIO/DSO/DPO
    # are all available (from either source) but Screener doesn't carry
    # cash_conversion_cycle directly for this year: CCC = DIO + DSO - DPO.
    if latest_period is not None and "ccc" not in single_period_fallback and latest_period not in ccc_series:
        dio_v, dso_v, dpo_v = dio_series.get(latest_period), dso_series.get(latest_period), dpo_series.get(latest_period)
        if dio_v is not None and dso_v is not None and dpo_v is not None:
            ccc_series = {**ccc_series, latest_period: round(dio_v + dso_v - dpo_v, 2)}
            single_period_fallback["ccc"] = True

    # Flat "latest value" convenience fields — same series, just the most
    # recent point pulled out to a fixed key, needed by the metric-ledger
    # sync (which can only dual-write a fixed dot-path, not a
    # dynamically-keyed-by-period series) and generally convenient for any
    # other consumer that just wants "the current number."
    ratio_latest_period = max(current_ratio_series.keys(), default=None)

    return {
        "methodology": METHODOLOGY,
        "latest_period": latest_period,
        "dso_series": dso_series,
        "dio_series": dio_series,
        "dpo_series": dpo_series,
        "ccc_series": ccc_series,
        "current_ratio_series": current_ratio_series,
        "quick_ratio_series": quick_ratio_series,
        "cash_ratio_series": cash_ratio_series,
        "latest_cross_check": latest_cross_check,
        "single_period_fallback": single_period_fallback,
        "ccc_latest": ccc_series.get(latest_period) if latest_period else None,
        "current_ratio_latest": current_ratio_series.get(ratio_latest_period) if ratio_latest_period else None,
        "quick_ratio_latest": quick_ratio_series.get(ratio_latest_period) if ratio_latest_period else None,
        "cash_ratio_latest": cash_ratio_series.get(ratio_latest_period) if ratio_latest_period else None,
    }


def compute_working_capital_amounts(current_assets: float | None, current_liabilities: float | None,
                                     revenue: float | None) -> dict:
    """Gross/Net Working Capital in absolute terms (spec §32) — separate
    from the days-based ratios above since it needs raw current-assets/
    current-liabilities figures, not the derived ratio series."""
    gross_wc = current_assets
    net_wc = None
    if current_assets is not None and current_liabilities is not None:
        net_wc = round(current_assets - current_liabilities, 2)
    wc_pct_revenue = None
    if net_wc is not None and revenue:
        wc_pct_revenue = round(net_wc / revenue * 100, 2)
    return {
        "gross_working_capital": gross_wc,
        "net_working_capital": net_wc,
        "working_capital_pct_revenue": wc_pct_revenue,
    }
