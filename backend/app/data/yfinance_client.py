"""
Fetches historical financial statements from yfinance for Indian stocks.
Returns normalized dicts keyed by fiscal year string (e.g. "FY2025").
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

from app.infrastructure.redis.client import cache_get_json, cache_set_json
from app.logger import logger

_CACHE_TTL = 60 * 60 * 24  # 24 hours


def _yf_symbol(exchange: str, symbol: str) -> str:
    if exchange.upper() == "BSE":
        return f"{symbol.upper()}.BO"
    return f"{symbol.upper()}.NS"


def _fy_label(dt) -> str:
    """Convert a pandas Timestamp or datetime to a fiscal-year label like FY2025."""
    if hasattr(dt, "year"):
        return f"FY{dt.year}"
    return str(dt)[:4]


def _safe(val) -> float | None:
    try:
        v = float(val)
        return round(v, 4) if not pd.isna(v) else None
    except (TypeError, ValueError):
        return None


def _df_to_dict(df: pd.DataFrame | None, row_key: str) -> dict[str, float | None]:
    """Extract a single row from a yfinance DataFrame into {FYyear: value}."""
    if df is None or df.empty:
        return {}
    try:
        row = df.loc[row_key] if row_key in df.index else None
        if row is None:
            return {}
        return {_fy_label(col): _safe(val) for col, val in row.items()}
    except Exception:
        return {}


def _try_keys(df: pd.DataFrame | None, *keys: str) -> dict[str, float | None]:
    """Try multiple row key variants until one matches — returns first non-empty hit."""
    if df is None or df.empty:
        return {}
    for key in keys:
        if key in df.index:
            result = _df_to_dict(df, key)
            if result:
                return result
    return {}


def _df_to_dict_dated(df: pd.DataFrame | None, row_key: str) -> dict[str, float | None]:
    """Same as `_df_to_dict()` but keyed by the real ISO quarter-end date
    (e.g. "2026-06-30"), not `_fy_label()`'s calendar-year bucket. Real bug
    found live on Anthem Biosciences: `quarterly_financials` genuinely has 5
    distinct quarter columns (2026-06-30, 2026-03-31, 2025-12-31,
    2025-09-30, 2025-06-30), but `_df_to_dict()`'s `_fy_label()` collapses
    any two quarters landing in the same calendar year to the same "FY2026"/
    "FY2025" key — a dict comprehension over `row.items()`, so whichever
    quarter is processed last for that year silently overwrites the other,
    leaving a "quarterly" series that's actually just 2 mislabeled annual-ish
    points. Only used for the `quarterly` block below — every OTHER caller
    of `_df_to_dict`/`_try_keys` here (the FY-level `fin`/`bs`/`cf` series)
    is unaffected, since a real annual DataFrame has at most one column per
    calendar year already."""
    if df is None or df.empty:
        return {}
    try:
        row = df.loc[row_key] if row_key in df.index else None
        if row is None:
            return {}
        return {col.date().isoformat(): _safe(val) for col, val in row.items() if hasattr(col, "date")}
    except Exception:
        return {}


def _try_keys_dated(df: pd.DataFrame | None, *keys: str) -> dict[str, float | None]:
    """`_try_keys()`, dated — see `_df_to_dict_dated()`."""
    if df is None or df.empty:
        return {}
    for key in keys:
        if key in df.index:
            result = _df_to_dict_dated(df, key)
            if result:
                return result
    return {}


def _merge_series(*series: dict[str, float | None]) -> dict[str, float | None]:
    """Merge multiple year-keyed series, preferring non-None values."""
    merged: dict[str, float | None] = {}
    for s in series:
        for yr, val in s.items():
            if yr not in merged or (merged[yr] is None and val is not None):
                merged[yr] = val
    return merged


def _compute_fcf_from_ocf(
    ocf: dict[str, float | None],
    capex: dict[str, float | None],
) -> dict[str, float | None]:
    """FCF = OCF - |CapEx|. CapEx from yfinance is negative, so we add it."""
    result: dict[str, float | None] = {}
    for yr in set(ocf) | set(capex):
        o = ocf.get(yr)
        c = capex.get(yr)
        if o is not None and c is not None:
            # yfinance stores CapEx as negative; FCF = OCF + CapEx (which is OCF - |CapEx|)
            result[yr] = round(o + c, 4)
        elif o is not None:
            result[yr] = o  # assume no capex
        else:
            result[yr] = None
    return result


def _ttm_from_quarterly(q_series: dict[str, float | None]) -> float | None:
    """Sum the 4 most-recent quarterly values to get TTM."""
    vals = [v for v in sorted(q_series.items(), key=lambda x: x[0], reverse=True)
            if v[1] is not None]
    if not vals:
        return None
    recent = [v for _, v in vals[:4]]
    if len(recent) < 2:
        return None
    return round(sum(recent), 4)


def _diagnose(income: dict, balance: dict, cash_flow: dict) -> dict:
    """
    Return data quality diagnostics: years available, missing key fields, staleness.
    """
    revenue_years = sorted(k for k, v in income.get("revenue", {}).items() if v is not None)
    ni_years = sorted(k for k, v in income.get("net_income", {}).items() if v is not None)
    bs_years = sorted(k for k, v in balance.get("total_assets", {}).items() if v is not None)
    cf_years = sorted(k for k, v in cash_flow.get("operating_cash_flow", {}).items() if v is not None)

    all_years = sorted(set(revenue_years) | set(bs_years))
    years_count = len(all_years)

    # Detect staleness: most-recent year should be FY2024 or FY2025
    current_fy = f"FY{datetime.now().year}"
    prev_fy = f"FY{datetime.now().year - 1}"
    is_stale = bool(all_years) and all_years[-1] < prev_fy

    missing: list[str] = []
    if not income.get("gross_profit"):
        missing.append("gross_profit")
    if not income.get("ebitda"):
        missing.append("ebitda")
    if not balance.get("total_debt"):
        missing.append("total_debt")
    if not cash_flow.get("free_cash_flow") and not cash_flow.get("operating_cash_flow"):
        missing.append("free_cash_flow")
    if not income.get("interest_expense"):
        missing.append("interest_expense")

    return {
        "years_available": all_years,
        "years_count": years_count,
        "revenue_years": revenue_years,
        "bs_years": bs_years,
        "cf_years": cf_years,
        "missing_fields": missing,
        "is_stale": is_stale,
        "latest_fy": all_years[-1] if all_years else None,
    }


def fetch_financial_data(exchange: str, symbol: str) -> dict:
    """
    Fetch annual income statement, balance sheet, cash flow, and market info.
    Returns a structured dict ready for the calculation engine.
    """
    cache_key = f"yf:{exchange.lower()}:{symbol.lower()}"
    cached = cache_get_json(cache_key)
    if cached:
        logger.debug("Cache hit", cache_key=cache_key)
        return cached

    yf_sym = _yf_symbol(exchange, symbol)
    logger.info("Fetching yfinance data", symbol=yf_sym)

    try:
        ticker = yf.Ticker(yf_sym)
        info = ticker.info or {}
        fin = ticker.financials
        bs = ticker.balance_sheet
        cf = ticker.cashflow
        q_fin = ticker.quarterly_financials
        q_bs = ticker.quarterly_balance_sheet
        q_cf = ticker.quarterly_cashflow
    except Exception as e:
        logger.warning("yfinance fetch failed", symbol=yf_sym, error=str(e))
        return _empty_result(exchange, symbol, error=str(e))

    # ── Income Statement ──────────────────────────────────────────────────────
    revenue_s = _try_keys(fin,
        "Total Revenue", "Revenue", "Net Revenue", "Revenues",
        "Total Revenues", "Net Revenues",
    )
    gross_profit_s = _try_keys(fin,
        "Gross Profit", "Gross Income",
    )
    ebit_s = _try_keys(fin,
        "EBIT", "Operating Income", "Operating Profit",
        "Total Operating Income As Reported", "Normalized EBIT",
    )
    # D&A — check both income stmt and CF stmt
    da_s = _merge_series(
        _try_keys(fin, "Reconciled Depreciation", "Depreciation And Amortization"),
        _try_keys(cf,  "Depreciation And Amortization",
                       "Depreciation Depletion And Amortization",
                       "Depreciation And Amortization In Cash Flow",
                       "Depreciation"),
    )
    ebitda_s = _try_keys(fin, "EBITDA", "Normalized EBITDA")
    # Compute EBITDA = EBIT + D&A when not directly available
    if not ebitda_s and ebit_s:
        ebitda_s = {}
        for yr in set(ebit_s) | set(da_s):
            e = ebit_s.get(yr)
            d = da_s.get(yr) or 0
            ebitda_s[yr] = round(e + d, 4) if e is not None else None

    net_income_s = _try_keys(fin,
        "Net Income", "Net Income Common Stockholders",
        "Net Income From Continuing Operations",
        "Net Income Including Noncontrolling Interests",
    )
    interest_s = _try_keys(fin,
        "Interest Expense", "Interest Expense Non Operating",
        "Net Interest Income",
        "Total Other Finance Cost",
    )
    tax_s = _try_keys(fin,
        "Tax Provision", "Income Tax Expense",
        "Reconciled Cost Of Revenue",
    )
    diluted_eps_s = _try_keys(fin,
        "Diluted EPS", "Diluted Eps", "Basic EPS", "Basic Eps",
        "Normalized Diluted EPS",
    )
    basic_eps_s = _try_keys(fin, "Basic EPS", "Basic Eps")

    income = {
        "revenue":           revenue_s,
        "gross_profit":      gross_profit_s,
        "ebit":              ebit_s,
        "ebitda":            ebitda_s,
        "net_income":        net_income_s,
        "interest_expense":  interest_s,
        "tax_provision":     tax_s,
        "diluted_eps":       diluted_eps_s,
        "basic_eps":         basic_eps_s,
    }

    # ── Balance Sheet ─────────────────────────────────────────────────────────
    total_equity_s = _try_keys(bs,
        "Total Equity Gross Minority Interest",
        "Stockholders Equity", "Total Stockholder Equity",
        "Common Stock Equity", "Total Equity",
    )
    cash_s = _try_keys(bs,
        "Cash And Cash Equivalents",
        "Cash Cash Equivalents And Short Term Investments",
        "Cash And Short Term Investments",
        "Cash Equivalents",
    )
    receivables_s = _try_keys(bs,
        "Receivables", "Accounts Receivable", "Net Receivables",
        "Gross Accounts Receivable", "Trade And Other Receivables Non Current",
    )
    inventory_s = _try_keys(bs,
        "Inventory", "Inventories",
    )
    total_debt_s = _merge_series(
        _try_keys(bs, "Total Debt"),
        # fallback: long-term debt + short-term borrowings
        _try_keys(bs, "Long Term Debt And Capital Lease Obligation"),
    )
    payables_s = _try_keys(bs,
        "Payables", "Accounts Payable", "Payables And Accrued Expenses",
        "Trade And Other Payables Non Current",
    )
    long_term_debt_s = _try_keys(bs,
        "Long Term Debt",
        "Long Term Debt And Capital Lease Obligation",
        "Long Term Debt Net Current",
    )
    current_assets_s = _try_keys(bs,
        "Current Assets", "Total Current Assets",
    )
    current_liab_s = _try_keys(bs,
        "Current Liabilities", "Total Current Liabilities",
    )

    balance = {
        "total_assets":             _try_keys(bs, "Total Assets"),
        "current_assets":           current_assets_s,
        "cash":                     cash_s,
        "inventory":                inventory_s,
        "receivables":              receivables_s,
        "total_equity":             total_equity_s,
        "total_debt":               total_debt_s,
        "current_liabilities":      current_liab_s,
        "non_current_liabilities":  _try_keys(bs,
            "Total Non Current Liabilities Net Minority Interest",
            "Non Current Deferred Liabilities",
        ),
        "payables":                 payables_s,
        "long_term_debt":           long_term_debt_s,
    }

    # ── Cash Flow ─────────────────────────────────────────────────────────────
    ocf_s = _try_keys(cf,
        "Operating Cash Flow",
        "Cash Flow From Continuing Operating Activities",
        "Net Cash Provided By Operating Activities",
        "Net Income From Continuing Operations",  # last-resort proxy
    )
    capex_s = _try_keys(cf,
        "Capital Expenditure", "Capital Expenditures",
        "Purchase Of Property Plant And Equipment",
        "Purchase Of Ppe",
    )
    direct_fcf_s = _try_keys(cf, "Free Cash Flow")
    # Use direct FCF if available, else compute
    fcf_s = direct_fcf_s if direct_fcf_s else _compute_fcf_from_ocf(ocf_s, capex_s)

    da_cf_s = _try_keys(cf,
        "Depreciation And Amortization",
        "Depreciation Depletion And Amortization",
        "Depreciation And Amortization In Cash Flow",
        "Depreciation",
    )

    cash_flow = {
        "operating_cash_flow":      ocf_s,
        "capital_expenditure":      capex_s,
        "free_cash_flow":           fcf_s,
        "investing_cash_flow":      _try_keys(cf,
            "Investing Cash Flow",
            "Cash Flow From Continuing Investing Activities",
        ),
        "financing_cash_flow":      _try_keys(cf,
            "Financing Cash Flow",
            "Cash Flow From Continuing Financing Activities",
        ),
        "depreciation_amortization": da_cf_s,
    }

    # ── Market / Valuation ────────────────────────────────────────────────────
    def sf(k): return _safe(info.get(k))

    market = {
        "market_cap":       sf("marketCap"),
        "enterprise_value": sf("enterpriseValue"),
        "trailing_pe":      sf("trailingPE"),
        "forward_pe":       sf("forwardPE"),
        "price_to_book":    sf("priceToBook"),
        "price_to_sales":   sf("priceToSalesTrailing12Months"),
        "ev_to_ebitda":     sf("enterpriseToEbitda"),
        "ev_to_revenue":    sf("enterpriseToRevenue"),
        "trailing_eps":     sf("trailingEps"),
        "forward_eps":      sf("forwardEps"),
        "book_value":       sf("bookValue"),
        "dividend_yield":   sf("dividendYield"),
        "dividend_rate":    sf("dividendRate"),
        "current_price":    sf("currentPrice") or sf("regularMarketPrice"),
        "beta":             sf("beta"),
        "week52_high":      sf("fiftyTwoWeekHigh"),
        "week52_low":       sf("fiftyTwoWeekLow"),
        "shares_outstanding": sf("sharesOutstanding"),
        "float_shares":     sf("floatShares"),
        "peg_ratio":        sf("pegRatio"),
        "short_ratio":      sf("shortRatio"),
        # Extra ratios (2026-09-13 yfinance audit) — margins/ROE/ROA/D-E are
        # deliberately NOT pulled from .info here even though Yahoo has them;
        # this app computes those itself from raw statements for consistency
        # with every other sector's methodology, so only genuinely new
        # fields are added.
        "payout_ratio":         sf("payoutRatio"),
        "five_yr_avg_div_yield": sf("fiveYearAvgDividendYield"),
        "held_pct_insiders":    sf("heldPercentInsiders"),
        "held_pct_institutions": sf("heldPercentInstitutions"),
        "week52_change":        sf("52WeekChange"),
    }

    # ── Company Info ──────────────────────────────────────────────────────────
    company_info = {
        "long_name":    info.get("longName") or info.get("shortName"),
        "sector":       info.get("sector"),
        "industry":     info.get("industry"),
        "description":  (info.get("longBusinessSummary") or "")[:800] or None,
        "website":      info.get("website"),
        "employees":    _safe(info.get("fullTimeEmployees")),
        "country":      info.get("country"),
        "currency":     info.get("currency", "INR"),
    }

    # ── Quarterly (recent 4–8 quarters, real ISO quarter-end date keys —
    # see `_df_to_dict_dated()`'s docstring for why these use the _dated
    # variant and not the FY-bucketing `_try_keys()` every other series
    # here uses) ──────────────────────────────────────────────────────────
    q_revenue = _try_keys_dated(q_fin, "Total Revenue", "Revenue", "Net Revenue")
    q_net_income = _try_keys_dated(q_fin, "Net Income", "Net Income Common Stockholders")
    q_ebitda = _try_keys_dated(q_fin, "EBITDA", "Normalized EBITDA")
    q_gross = _try_keys_dated(q_fin, "Gross Profit", "Gross Income")
    q_ebit = _try_keys_dated(q_fin, "EBIT", "Operating Income")
    q_eps = _try_keys_dated(q_fin, "Diluted EPS", "Basic EPS")
    q_ocf = _try_keys_dated(q_cf, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities")
    q_capex = _try_keys_dated(q_cf, "Capital Expenditure", "Capital Expenditures")

    quarterly = {
        "revenue":              q_revenue,
        "net_income":           q_net_income,
        "ebitda":               q_ebitda,
        "gross_profit":         q_gross,
        "ebit":                 q_ebit,
        "eps":                  q_eps,
        "operating_cash_flow":  q_ocf,
        "capital_expenditure":  q_capex,
        # TTM convenience fields
        "ttm_revenue":          _ttm_from_quarterly(q_revenue),
        "ttm_net_income":       _ttm_from_quarterly(q_net_income),
        "ttm_ebitda":           _ttm_from_quarterly(q_ebitda),
        "ttm_ocf":              _ttm_from_quarterly(q_ocf),
    }

    # ── Data Quality Diagnostics ──────────────────────────────────────────────
    diagnostics = _diagnose(income, balance, cash_flow)

    result = {
        "exchange":     exchange,
        "symbol":       symbol,
        "yf_symbol":    yf_sym,
        "income":       income,
        "balance":      balance,
        "cash_flow":    cash_flow,
        "market":       market,
        "company_info": company_info,
        "quarterly":    quarterly,
        "diagnostics":  diagnostics,
        "fetched_at":   datetime.now(timezone.utc).isoformat(),
        "error":        None,
    }

    cache_set_json(cache_key, result, ttl_seconds=_CACHE_TTL)
    logger.info("yfinance data fetched and cached",
                symbol=yf_sym,
                years=diagnostics["years_count"],
                latest_fy=diagnostics["latest_fy"],
                missing=diagnostics["missing_fields"])
    return result


def _empty_result(exchange: str, symbol: str, error: str = "") -> dict:
    empty_diag = {
        "years_available": [], "years_count": 0,
        "revenue_years": [], "bs_years": [], "cf_years": [],
        "missing_fields": ["revenue", "gross_profit", "ebitda", "total_debt", "free_cash_flow"],
        "is_stale": False, "latest_fy": None,
    }
    return {
        "exchange":     exchange,
        "symbol":       symbol,
        "yf_symbol":    _yf_symbol(exchange, symbol),
        "income":       {},
        "balance":      {},
        "cash_flow":    {},
        "market":       {},
        "company_info": {},
        "quarterly":    {},
        "diagnostics":  empty_diag,
        "fetched_at":   datetime.now(timezone.utc).isoformat(),
        "error":        error,
    }
