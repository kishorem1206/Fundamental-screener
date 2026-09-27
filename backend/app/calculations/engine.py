"""
Deterministic financial calculation engine.
LLMs never touch these calculations — all arithmetic is done here in Python.
"""
from __future__ import annotations
import math
from typing import Any

NA = "NOT_APPLICABLE"
INSUFFICIENT = "INSUFFICIENT_DATA"


def _v(series: dict, *years: str) -> list[float]:
    """Extract valid numeric values for given fiscal years from a series dict."""
    result = []
    for y in years:
        val = series.get(y)
        if val is not None and isinstance(val, (int, float)) and not math.isnan(val):
            result.append(float(val))
    return result


def _latest(series: dict) -> float | None:
    """Get the most recent valid value from a series dict."""
    if not series:
        return None
    for key in sorted(series.keys(), reverse=True):
        val = series.get(key)
        if val is not None and isinstance(val, (int, float)) and not math.isnan(val):
            return float(val)
    return None


def _sorted_values(series: dict) -> list[float]:
    """Return values sorted oldest→newest (ascending year order), no nulls."""
    result = []
    for key in sorted(series.keys()):
        val = series.get(key)
        if val is not None and isinstance(val, (int, float)) and not math.isnan(val):
            result.append(float(val))
    return result


def _series_avg(series: dict, n: int) -> float | None:
    """Average of the n most-recent valid values in a series dict."""
    vals = _sorted_values(series)
    if not vals:
        return None
    recent = vals[-n:] if len(vals) >= n else vals
    if not recent:
        return None
    return round(sum(recent) / len(recent), 2)


def _sorted_years(series: dict) -> list[str]:
    return [k for k in sorted(series.keys()) if series.get(k) is not None]


def safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    try:
        return round(numerator / denominator, 4)
    except (ZeroDivisionError, TypeError):
        return None


def calculate_cagr(values_oldest_to_newest: list[float], years: int) -> float | None:
    """CAGR from oldest to newest value over given number of years."""
    if len(values_oldest_to_newest) < 2 or years <= 0:
        return None
    start = values_oldest_to_newest[0]
    end = values_oldest_to_newest[-1]
    if start is None or end is None:
        return None
    if start <= 0 or end <= 0:
        # Can't calculate CAGR from a negative/zero base OR endpoint — a
        # sign flip (e.g. cash-flow figures, which legitimately cross
        # zero) makes `(end / start) ** (1/years)` raise a fractional
        # power of a negative number, which Python silently returns as a
        # COMPLEX number rather than raising (confirmed live: crashed
        # `round()` downstream with "type complex doesn't define
        # __round__" on a real Tata Technologies cash-flow series).
        # Undefined/misleading either way, so this returns None same as
        # the negative-start case already did.
        return None
    try:
        cagr = (end / start) ** (1.0 / years) - 1.0
        return round(cagr * 100, 2)  # as percentage
    except (ZeroDivisionError, ValueError):
        return None


def _cagr_from_series(series: dict, n_years: int) -> float | None:
    """Calculate CAGR for most recent n_years from a series dict."""
    vals = _sorted_values(series)
    if len(vals) < 2:
        return None
    # Use last n_years+1 values (need start + end)
    if len(vals) > n_years + 1:
        vals = vals[-(n_years + 1):]
    actual_years = len(vals) - 1
    return calculate_cagr(vals, actual_years)


def calculate_margin(numerator_series: dict, denominator_series: dict) -> dict[str, float | None]:
    """Calculate margin for each year where both numerator and denominator exist."""
    result = {}
    all_years = set(numerator_series.keys()) | set(denominator_series.keys())
    for year in sorted(all_years):
        num = numerator_series.get(year)
        den = denominator_series.get(year)
        result[year] = safe_div(num, den)
    return {k: (round(v * 100, 2) if v is not None else None) for k, v in result.items()}


def trend_direction(values_oldest_to_newest: list[float]) -> str:
    """
    Classify trend as IMPROVING, STABLE, DETERIORATING, VOLATILE, or INSUFFICIENT_DATA.

    Direction reflects the MOST RECENT period-over-period move (latest vs.
    second-latest, relative to the series' average level), not a whole-
    history linear regression. Real bug found 2026-09-15 comparing against
    Screener.in: Jyothy Labs' ROCE (FY23 18.86% -> FY24 25.18% -> FY25
    32.75% -> FY26 26.9%) was labelled STRONGLY_IMPROVING under the old
    whole-series-regression approach — the FY23-25 runup dominated the
    slope even though the latest year fell ~18% off its FY25 peak, the
    opposite of what that label told the reader. A trend badge sitting next
    to a "latest value" metric card has to answer "is this getting better
    or worse right now", which is a recent-momentum question, not a
    multi-year-average one.

    Volatility (VOLATILE) is still judged over the whole series — that's a
    genuinely different question (how noisy is this metric historically),
    not a directional one, and still deserves to override a direction call
    that a single recent swing shouldn't be read too much into.
    """
    vals = [v for v in values_oldest_to_newest if v is not None]
    if len(vals) < 2:
        return INSUFFICIENT

    mean_val = abs(sum(vals) / len(vals)) + 1e-9

    if len(vals) >= 3:
        std_val = (sum((v - sum(vals) / len(vals)) ** 2 for v in vals) / len(vals)) ** 0.5
        cv = std_val / mean_val
        if cv > 0.4:
            return "VOLATILE"

    delta_pct = (vals[-1] - vals[-2]) / mean_val
    if delta_pct > 0.03:
        return "STRONGLY_IMPROVING" if delta_pct > 0.08 else "IMPROVING"
    if delta_pct < -0.03:
        return "STRONGLY_DETERIORATING" if delta_pct < -0.08 else "DETERIORATING"
    return "STABLE"


def flip_trend(t: str) -> str:
    """`trend_direction()` only knows the raw VALUE direction (up/down) —
    for a "lower is better" metric (debt/equity, inventory/receivable
    days, CCC, net-debt/EBITDA, ...) a falling value is actually
    IMPROVING, not DETERIORATING. Apply to any such metric's raw trend
    before exposing it, matching the fix already used for working-capital
    days (`working_capital_trends()`) — extracted to module level so
    `compute_all()`'s own `debt_trend` (real bug found live: Debt/Equity
    falling was shown as "↓↓ Deteriorating" in red, the opposite of what a
    shrinking-leverage company earned) can share it rather than
    reimplementing the same mapping."""
    return {"IMPROVING": "DETERIORATING", "STRONGLY_IMPROVING": "STRONGLY_DETERIORATING",
            "DETERIORATING": "IMPROVING", "STRONGLY_DETERIORATING": "STRONGLY_IMPROVING"}.get(t, t)


class MetricsCalculator:
    """
    Given raw financial data from yfinance_client, computes all fundamental metrics.
    All values are deterministic Python arithmetic — no LLM involvement.
    """

    def __init__(self, data: dict):
        self._fd = data                          # keep full dict for diagnostics/fetched_at
        self.inc = data.get("income", {})
        self.bal = data.get("balance", {})
        self.cf = data.get("cash_flow", {})
        self.mkt = data.get("market", {})
        self.info = data.get("company_info", {})
        self.qtr = data.get("quarterly", {})

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _income_series(self, key: str) -> dict:
        return self.inc.get(key, {})

    def _bal_series(self, key: str) -> dict:
        return self.bal.get(key, {})

    def _cf_series(self, key: str) -> dict:
        return self.cf.get(key, {})

    def _mkt(self, key: str) -> float | None:
        v = self.mkt.get(key)
        return float(v) if v is not None else None

    # ── Available fiscal years ────────────────────────────────────────────────

    def available_years(self) -> list[str]:
        rev = self.inc.get("revenue", {})
        return sorted(rev.keys())

    # ── Growth Metrics ────────────────────────────────────────────────────────

    def revenue_cagr(self, n: int) -> float | None:
        return _cagr_from_series(self._income_series("revenue"), n)

    def ebitda_cagr(self, n: int) -> float | None:
        return _cagr_from_series(self._income_series("ebitda"), n)

    def pat_cagr(self, n: int) -> float | None:
        return _cagr_from_series(self._income_series("net_income"), n)

    def eps_cagr(self, n: int) -> float | None:
        return _cagr_from_series(self._income_series("diluted_eps"), n)

    def fcf_cagr(self, n: int) -> float | None:
        fcf = self._compute_fcf_series()
        return _cagr_from_series(fcf, n)

    # ── Margin Metrics ────────────────────────────────────────────────────────

    def gross_margin_series(self) -> dict[str, float | None]:
        return calculate_margin(self._income_series("gross_profit"), self._income_series("revenue"))

    def ebitda_margin_series(self) -> dict[str, float | None]:
        return calculate_margin(self._income_series("ebitda"), self._income_series("revenue"))

    def ebit_margin_series(self) -> dict[str, float | None]:
        return calculate_margin(self._income_series("ebit"), self._income_series("revenue"))

    def pat_margin_series(self) -> dict[str, float | None]:
        return calculate_margin(self._income_series("net_income"), self._income_series("revenue"))

    def gross_margin_latest(self) -> float | None:
        return _latest(self.gross_margin_series())

    def ebitda_margin_latest(self) -> float | None:
        return _latest(self.ebitda_margin_series())

    def ebit_margin_latest(self) -> float | None:
        return _latest(self.ebit_margin_series())

    def pat_margin_latest(self) -> float | None:
        return _latest(self.pat_margin_series())

    # ── ROE ──────────────────────────────────────────────────────────────────

    def roe_series(self) -> dict[str, float | None]:
        result = {}
        years = set(self._income_series("net_income").keys()) & set(self._bal_series("total_equity").keys())
        for y in sorted(years):
            ni = self._income_series("net_income").get(y)
            eq = self._bal_series("total_equity").get(y)
            if ni is not None and eq is not None and eq != 0:
                result[y] = round((ni / abs(eq)) * 100, 2)
            else:
                result[y] = None
        return result

    def roe_latest(self) -> float | None:
        return _latest(self.roe_series())

    # ── ROA ──────────────────────────────────────────────────────────────────

    def roa_series(self) -> dict[str, float | None]:
        """ROA = Net Income / Total Assets × 100 — key metric for banks and NBFCs."""
        result = {}
        ni = self._income_series("net_income")
        ta = self._bal_series("total_assets")
        years = set(ni.keys()) & set(ta.keys())
        for y in sorted(years):
            n = ni.get(y)
            a = ta.get(y)
            if n is not None and a is not None and a != 0:
                result[y] = round((n / abs(a)) * 100, 3)
            else:
                result[y] = None
        return result

    def roa_latest(self) -> float | None:
        return _latest(self.roa_series())

    # ── ROCE ─────────────────────────────────────────────────────────────────

    def roce_series(self) -> dict[str, float | None]:
        """ROCE = EBIT / (Total Assets - Current Liabilities)"""
        result = {}
        ebit = self._income_series("ebit")
        ta = self._bal_series("total_assets")
        cl = self._bal_series("current_liabilities")
        years = set(ebit.keys()) & set(ta.keys()) & set(cl.keys())
        for y in sorted(years):
            e = ebit.get(y)
            a = ta.get(y)
            c = cl.get(y)
            if e is not None and a is not None and c is not None:
                cap_employed = a - c
                result[y] = round((e / cap_employed) * 100, 2) if cap_employed != 0 else None
            else:
                result[y] = None
        return result

    def roce_latest(self) -> float | None:
        return _latest(self.roce_series())

    # ── ROIC ─────────────────────────────────────────────────────────────────

    def roic_series(self) -> dict[str, float | None]:
        """ROIC = NOPAT / Invested Capital; NOPAT = EBIT*(1-tax_rate); IC = Equity + Debt - Cash"""
        result = {}
        ebit = self._income_series("ebit")
        tax = self._income_series("tax_provision")
        ni = self._income_series("net_income")
        pbt = {y: (ebit.get(y, 0) or 0) - (tax.get(y, 0) or 0) for y in ebit}
        eq = self._bal_series("total_equity")
        debt = self._bal_series("total_debt")
        cash = self._bal_series("cash")
        years = set(ebit.keys()) & set(eq.keys())
        for y in sorted(years):
            e = ebit.get(y)
            t = tax.get(y, 0) or 0
            prebt = pbt.get(y, 0) or 0
            if e is None:
                result[y] = None
                continue
            # Tax rate estimate
            if prebt and prebt != 0:
                tax_rate = max(0.0, min(0.5, t / prebt)) if prebt > 0 else 0.25
            else:
                tax_rate = 0.25
            nopat = e * (1 - tax_rate)
            equity_val = eq.get(y, 0) or 0
            debt_val = debt.get(y, 0) or 0
            cash_val = cash.get(y, 0) or 0
            ic = equity_val + debt_val - cash_val
            result[y] = round((nopat / ic) * 100, 2) if ic and ic != 0 else None
        return result

    def roic_latest(self) -> float | None:
        return _latest(self.roic_series())

    # ── Cash Flow Metrics ─────────────────────────────────────────────────────

    def _compute_fcf_series(self) -> dict[str, float | None]:
        """FCF = Operating CF - |CapEx| (CapEx is stored as negative in yfinance)"""
        result = {}
        ocf_s = self._cf_series("operating_cash_flow")
        capex_s = self._cf_series("capital_expenditure")
        # Use pre-computed FCF if available
        precomp = self._cf_series("free_cash_flow")

        years = set(ocf_s.keys())
        for y in sorted(years):
            if y in precomp and precomp[y] is not None:
                result[y] = precomp[y]
                continue
            ocf = ocf_s.get(y)
            capex = capex_s.get(y)
            if ocf is not None:
                # capex is negative in yfinance, so FCF = OCF + capex
                cap = capex or 0
                result[y] = round(ocf + cap, 2)
            else:
                result[y] = None
        return result

    def fcf_series(self) -> dict[str, float | None]:
        return self._compute_fcf_series()

    def fcf_latest(self) -> float | None:
        return _latest(self._compute_fcf_series())

    def cfo_to_pat_series(self) -> dict[str, float | None]:
        result = {}
        ocf = self._cf_series("operating_cash_flow")
        pat = self._income_series("net_income")
        years = set(ocf.keys()) & set(pat.keys())
        for y in sorted(years):
            o = ocf.get(y)
            p = pat.get(y)
            if o is not None and p and p != 0:
                result[y] = round(o / p * 100, 2)
            else:
                result[y] = None
        return result

    def fcf_to_pat_series(self) -> dict[str, float | None]:
        result = {}
        fcf = self._compute_fcf_series()
        pat = self._income_series("net_income")
        years = set(fcf.keys()) & set(pat.keys())
        for y in sorted(years):
            f = fcf.get(y)
            p = pat.get(y)
            if f is not None and p and p != 0:
                result[y] = round(f / p * 100, 2)
            else:
                result[y] = None
        return result

    def fcf_margin_series(self) -> dict[str, float | None]:
        return calculate_margin(self._compute_fcf_series(), self._income_series("revenue"))

    # ── Balance Sheet Metrics ─────────────────────────────────────────────────

    def debt_to_equity_series(self) -> dict[str, float | None]:
        result = {}
        debt = self._bal_series("total_debt")
        eq = self._bal_series("total_equity")
        years = set(debt.keys()) & set(eq.keys())
        for y in sorted(years):
            d = debt.get(y)
            e = eq.get(y)
            if d is not None and e and e != 0:
                result[y] = round(d / abs(e), 4)
            else:
                result[y] = None
        return result

    def net_debt_series(self) -> dict[str, float | None]:
        result = {}
        debt = self._bal_series("total_debt")
        cash = self._bal_series("cash")
        years = set(debt.keys()) | set(cash.keys())
        for y in sorted(years):
            d = debt.get(y) or 0
            c = cash.get(y) or 0
            result[y] = round(d - c, 2)
        return result

    def net_debt_to_ebitda_series(self) -> dict[str, float | None]:
        result = {}
        nd = self.net_debt_series()
        ebitda = self._income_series("ebitda")
        years = set(nd.keys()) & set(ebitda.keys())
        for y in sorted(years):
            n = nd.get(y)
            e = ebitda.get(y)
            if n is not None and e and e != 0 and e > 0:
                result[y] = round(n / e, 2)
            else:
                result[y] = None
        return result

    def interest_coverage_series(self) -> dict[str, float | None]:
        """EBIT / Interest Expense"""
        result = {}
        ebit = self._income_series("ebit")
        ie = self._income_series("interest_expense")
        years = set(ebit.keys()) & set(ie.keys())
        for y in sorted(years):
            e = ebit.get(y)
            i = ie.get(y)
            if e is not None and i and i != 0:
                result[y] = round(abs(e / i), 2)
            else:
                result[y] = None
        return result

    def current_ratio_series(self) -> dict[str, float | None]:
        result = {}
        ca = self._bal_series("current_assets")
        cl = self._bal_series("current_liabilities")
        years = set(ca.keys()) & set(cl.keys())
        for y in sorted(years):
            a = ca.get(y)
            c = cl.get(y)
            if a is not None and c and c != 0:
                result[y] = round(a / c, 2)
            else:
                result[y] = None
        return result

    # ── Working Capital / Efficiency ──────────────────────────────────────────

    def inventory_days_series(self) -> dict[str, float | None]:
        """Inventory / (Revenue / 365)"""
        result = {}
        inv = self._bal_series("inventory")
        rev = self._income_series("revenue")
        years = set(inv.keys()) & set(rev.keys())
        for y in sorted(years):
            i = inv.get(y)
            r = rev.get(y)
            if i is not None and r and r != 0:
                result[y] = round(i / r * 365, 1)
            else:
                result[y] = None
        return result

    def receivable_days_series(self) -> dict[str, float | None]:
        """Receivables / (Revenue / 365)"""
        result = {}
        rec = self._bal_series("receivables")
        rev = self._income_series("revenue")
        years = set(rec.keys()) & set(rev.keys())
        for y in sorted(years):
            r_val = rec.get(y)
            rev_val = rev.get(y)
            if r_val is not None and rev_val and rev_val != 0:
                result[y] = round(r_val / rev_val * 365, 1)
            else:
                result[y] = None
        return result

    def payable_days_series(self) -> dict[str, float | None]:
        result = {}
        pay = self._bal_series("payables")
        rev = self._income_series("revenue")
        years = set(pay.keys()) & set(rev.keys())
        for y in sorted(years):
            p = pay.get(y)
            r = rev.get(y)
            if p is not None and r and r != 0:
                result[y] = round(p / r * 365, 1)
            else:
                result[y] = None
        return result

    def asset_turnover_series(self) -> dict[str, float | None]:
        """Revenue / Total Assets"""
        result = {}
        rev = self._income_series("revenue")
        ta = self._bal_series("total_assets")
        years = set(rev.keys()) & set(ta.keys())
        for y in sorted(years):
            r = rev.get(y)
            a = ta.get(y)
            if r is not None and a and a != 0:
                result[y] = round(r / a, 4)
            else:
                result[y] = None
        return result

    def capex_to_revenue_series(self) -> dict[str, float | None]:
        result = {}
        capex = self._cf_series("capital_expenditure")
        rev = self._income_series("revenue")
        years = set(capex.keys()) & set(rev.keys())
        for y in sorted(years):
            c = capex.get(y)
            r = rev.get(y)
            if c is not None and r and r != 0:
                result[y] = round(abs(c) / r * 100, 2)
            else:
                result[y] = None
        return result

    # ── Piotroski F-Score ────────────────────────────────────────────────────
    # Computed deterministically here rather than scraped from a third party
    # (Trendlyne shows this too, but as a bare number with no visible
    # methodology). Piotroski (2000)'s original public 9-point checklist,
    # using only series this class already computes/has — no new data
    # source. Each check compares the latest fiscal year (t) against the
    # prior one (t-1); a check whose inputs aren't available in either year
    # is marked unavailable, not failed, so a data gap never reads as a
    # weakness. `score` is passed-count out of `checks_available`, not a
    # fixed /9, so a company missing e.g. dividend-unrelated balance-sheet
    # detail still gets an honest score on what could be evaluated.

    def piotroski_f_score(self) -> dict:
        ni = self._income_series("net_income")
        ta = self._bal_series("total_assets")
        years = sorted(set(ni.keys()) & set(ta.keys()))
        if len(years) < 2:
            return {"score": None, "checks_available": 0, "components": []}
        t, t0 = years[-1], years[-2]

        cfo = self._cf_series("operating_cash_flow")
        roa = self.roa_series()
        debt = self._bal_series("total_debt")
        curr_ratio = self.current_ratio_series()
        gross_m = self.gross_margin_series()
        at = self.asset_turnover_series()
        # No direct historical share-count series from yfinance (`market`
        # is a current-only snapshot) — approximated from Net Income /
        # Diluted EPS per year, the standard fallback when a share-count
        # history isn't directly available. Flagged as approximate in the
        # component's own label so a downstream reader isn't misled into
        # treating it as an exact share-register figure.
        eps = self._income_series("diluted_eps")
        approx_shares = {
            y: (ni[y] / eps[y]) if ni.get(y) and eps.get(y) else None
            for y in (t, t0)
        }

        components = []

        def add(key: str, label: str, passed: bool | None, detail: str = ""):
            components.append({"key": key, "label": label, "passed": passed, "detail": detail})

        # Profitability
        add("positive_net_income", "Positive net income",
            None if ni.get(t) is None else ni[t] > 0,
            f"Net income {t}: {ni.get(t)}")
        add("positive_cfo", "Positive operating cash flow",
            None if cfo.get(t) is None else cfo[t] > 0,
            f"CFO {t}: {cfo.get(t)}")
        add("increasing_roa", "ROA improved YoY",
            None if roa.get(t) is None or roa.get(t0) is None else roa[t] > roa[t0],
            f"ROA {t0}->{t}: {roa.get(t0)} -> {roa.get(t)}")
        add("earnings_quality", "CFO exceeds net income (accrual quality)",
            None if cfo.get(t) is None or ni.get(t) is None else cfo[t] > ni[t],
            f"CFO {t}: {cfo.get(t)} vs Net income {t}: {ni.get(t)}")

        # Leverage, liquidity, source of funds
        lev_t = (debt.get(t) / ta[t]) if debt.get(t) is not None and ta.get(t) else None
        lev_t0 = (debt.get(t0) / ta[t0]) if debt.get(t0) is not None and ta.get(t0) else None
        add("decreasing_leverage", "Debt/Assets improved YoY (lower is better)",
            None if lev_t is None or lev_t0 is None else lev_t < lev_t0,
            f"Debt/Assets {t0}->{t}: {lev_t0} -> {lev_t}")
        add("increasing_current_ratio", "Current ratio improved YoY",
            None if curr_ratio.get(t) is None or curr_ratio.get(t0) is None else curr_ratio[t] > curr_ratio[t0],
            f"Current ratio {t0}->{t}: {curr_ratio.get(t0)} -> {curr_ratio.get(t)}")
        add("no_dilution", "No new shares issued (approx., from Net Income / Diluted EPS)",
            None if approx_shares.get(t) is None or approx_shares.get(t0) is None
            else approx_shares[t] <= approx_shares[t0] * 1.01,
            f"Approx. shares {t0}->{t}: {approx_shares.get(t0)} -> {approx_shares.get(t)}")

        # Operating efficiency
        add("increasing_gross_margin", "Gross margin improved YoY",
            None if gross_m.get(t) is None or gross_m.get(t0) is None else gross_m[t] > gross_m[t0],
            f"Gross margin {t0}->{t}: {gross_m.get(t0)} -> {gross_m.get(t)}")
        add("increasing_asset_turnover", "Asset turnover improved YoY",
            None if at.get(t) is None or at.get(t0) is None else at[t] > at[t0],
            f"Asset turnover {t0}->{t}: {at.get(t0)} -> {at.get(t)}")

        evaluable = [c for c in components if c["passed"] is not None]
        score = sum(1 for c in evaluable if c["passed"])
        return {
            "score": score, "checks_available": len(evaluable),
            "fiscal_year": t, "prior_fiscal_year": t0,
            "components": components,
        }

    # ── Cyclicality Analysis ──────────────────────────────────────────────────

    def _cv(self, series: dict) -> float | None:
        """Coefficient of variation of a series — measures cyclicality."""
        vals = _sorted_values(series)
        if len(vals) < 3:
            return None
        mean = sum(vals) / len(vals)
        if abs(mean) < 1e-6:
            return None
        std = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
        return round(std / abs(mean), 3)

    def cyclicality_analysis(self) -> dict:
        """
        Analyse peak/trough margins and ROCE across full history.
        CV > 0.25 on EBITDA margin → cyclical.
        Cycle position: where current margin sits between trough and peak.
        """
        ebitda_m = self.ebitda_margin_series()
        roce = self.roce_series()

        ebitda_vals = _sorted_values(ebitda_m)
        roce_vals = _sorted_values(roce)

        em_cv = self._cv(ebitda_m)
        is_cyclical = (em_cv is not None and em_cv > 0.25)

        em_peak   = round(max(ebitda_vals), 2)  if ebitda_vals else None
        em_trough = round(min(ebitda_vals), 2)  if ebitda_vals else None
        em_curr   = _latest(ebitda_m)

        # Cycle position 0–100: 0=trough, 100=peak
        cycle_position: float | None = None
        if em_peak is not None and em_trough is not None and em_curr is not None:
            span = em_peak - em_trough
            if span > 0.5:  # only meaningful if >0.5pp spread
                cycle_position = round((em_curr - em_trough) / span * 100, 1)

        roce_peak   = round(max(roce_vals), 2) if roce_vals else None
        roce_trough = round(min(roce_vals), 2) if roce_vals else None
        roce_curr   = _latest(roce)

        roce_cycle_position: float | None = None
        if roce_peak is not None and roce_trough is not None and roce_curr is not None:
            span = roce_peak - roce_trough
            if span > 1.0:
                roce_cycle_position = round((roce_curr - roce_trough) / span * 100, 1)

        return {
            "is_cyclical":          is_cyclical,
            "ebitda_margin_cv":     em_cv,
            "ebitda_margin_peak":   em_peak,
            "ebitda_margin_trough": em_trough,
            "ebitda_margin_current":em_curr,
            "cycle_position":       cycle_position,        # 0=trough, 100=peak
            "roce_peak":            roce_peak,
            "roce_trough":          roce_trough,
            "roce_current":         roce_curr,
            "roce_cycle_position":  roce_cycle_position,
        }

    # ── Working Capital Cycle Trends ──────────────────────────────────────────

    def working_capital_series(self) -> dict[str, float | None]:
        """Working Capital = Current Assets − Current Liabilities."""
        result = {}
        ca = self._bal_series("current_assets")
        cl = self._bal_series("current_liabilities")
        for y in sorted(set(ca) & set(cl)):
            a, l = ca.get(y), cl.get(y)
            result[y] = round(a - l, 2) if a is not None and l is not None else None
        return result

    def working_capital_to_revenue_series(self) -> dict[str, float | None]:
        """Working Capital / Revenue × 100 — NWC intensity."""
        wc = self.working_capital_series()
        rev = self._income_series("revenue")
        result = {}
        for y in sorted(set(wc) & set(rev)):
            w, r = wc.get(y), rev.get(y)
            result[y] = round(w / r * 100, 2) if w is not None and r and r != 0 else None
        return result

    def working_capital_trends(self) -> dict:
        """Trend directions for each working-capital component."""
        inv_d  = self.inventory_days_series()
        rec_d  = self.receivable_days_series()
        pay_d  = self.payable_days_series()
        ccc    = self.cash_conversion_cycle_series()
        wc_rev = self.working_capital_to_revenue_series()

        # For inventory/receivable days: lower is better, so flip trend label
        # (flip_trend — module-level, shared with debt_trend below)
        raw_inv = trend_direction(_sorted_values(inv_d))
        raw_rec = trend_direction(_sorted_values(rec_d))
        raw_pay = trend_direction(_sorted_values(pay_d))  # higher payables = better (more supplier credit)

        return {
            "inventory_days_trend":   flip_trend(raw_inv),   # flip: falling days = improving
            "receivable_days_trend":  flip_trend(raw_rec),   # flip: falling days = improving
            "payable_days_trend":     raw_pay,         # rising days = better
            "ccc_trend":              flip_trend(trend_direction(_sorted_values(ccc))),
            "wc_to_revenue_trend":    flip_trend(trend_direction(_sorted_values(wc_rev))),
            "working_capital_latest": _latest(self.working_capital_series()),
            "wc_to_revenue_latest":   _latest(wc_rev),
        }

    # ── ROIC Decomposition (DuPont-style) ────────────────────────────────────

    def roic_decomposition(self) -> dict:
        """
        ROIC = NOPAT Margin × Capital Turnover
        NOPAT Margin = NOPAT / Revenue
        Capital Turnover = Revenue / Invested Capital (Equity + Debt − Cash)
        """
        ebit   = self._income_series("ebit")
        tax    = self._income_series("tax_provision")
        rev    = self._income_series("revenue")
        eq     = self._bal_series("total_equity")
        debt   = self._bal_series("total_debt")
        cash   = self._bal_series("cash")

        nopat_margin_s: dict[str, float | None] = {}
        cap_turnover_s: dict[str, float | None] = {}
        roic_check_s:   dict[str, float | None] = {}

        years = sorted(set(ebit) & set(rev) & set(eq))
        for y in years:
            e  = ebit.get(y)
            t  = tax.get(y, 0) or 0
            r  = rev.get(y)
            eq_v  = eq.get(y) or 0
            d_v   = debt.get(y) or 0
            c_v   = cash.get(y) or 0

            if e is None or r is None or r == 0:
                nopat_margin_s[y] = None
                cap_turnover_s[y] = None
                roic_check_s[y]   = None
                continue

            # estimate tax rate
            pbt = e - t
            tax_rate = max(0.0, min(0.5, t / pbt)) if pbt > 0 else 0.25
            nopat = e * (1 - tax_rate)

            ic = eq_v + d_v - c_v
            if ic == 0:
                cap_turnover_s[y] = None
                roic_check_s[y]   = None
            else:
                cap_turnover_s[y] = round(r / ic, 3)
                roic_check_s[y]   = round(nopat / ic * 100, 2)

            nopat_margin_s[y] = round(nopat / r * 100, 2)

        return {
            "nopat_margin_series":    nopat_margin_s,
            "capital_turnover_series": cap_turnover_s,
            "roic_decomposed_series": roic_check_s,
            "nopat_margin_latest":    _latest(nopat_margin_s),
            "capital_turnover_latest":_latest(cap_turnover_s),
            "nopat_margin_3y_avg":    _series_avg(nopat_margin_s, 3),
            "capital_turnover_3y_avg":_series_avg(cap_turnover_s, 3),
        }

    # ── Quick Ratio ───────────────────────────────────────────────────────────

    def quick_ratio_series(self) -> dict[str, float | None]:
        """(Cash + Receivables) / Current Liabilities — excludes inventory."""
        result = {}
        cash = self._bal_series("cash")
        rec = self._bal_series("receivables")
        cl = self._bal_series("current_liabilities")
        years = set(cl.keys()) & (set(cash.keys()) | set(rec.keys()))
        for y in sorted(years):
            c = cash.get(y) or 0
            r = rec.get(y) or 0
            l = cl.get(y)
            if l and l != 0:
                result[y] = round((c + r) / l, 2)
            else:
                result[y] = None
        return result

    def quick_ratio_latest(self) -> float | None:
        return _latest(self.quick_ratio_series())

    def cash_ratio_series(self) -> dict[str, float | None]:
        """Cash / Current Liabilities — the strictest liquidity ratio
        (excludes both inventory and receivables). Added for the Balance
        Sheet Analysis Engine, a direct sibling of `current_ratio_series()`/
        `quick_ratio_series()` above."""
        result = {}
        cash = self._bal_series("cash")
        cl = self._bal_series("current_liabilities")
        years = set(cash.keys()) & set(cl.keys())
        for y in sorted(years):
            c = cash.get(y)
            l = cl.get(y)
            if c is not None and l and l != 0:
                result[y] = round(c / l, 2)
            else:
                result[y] = None
        return result

    def cash_ratio_latest(self) -> float | None:
        return _latest(self.cash_ratio_series())

    def cash_series(self) -> dict[str, float | None]:
        """Raw cash & equivalents balance — used internally by several ratio
        methods above (`net_debt_series`, `quick_ratio_series`,
        `cash_ratio_series`) but never itself exposed until the Balance
        Sheet Analysis Engine needed the raw figure (not just a ratio) for
        its Sources-vs-Applications "House" visual."""
        return dict(self._bal_series("cash"))

    def current_liabilities_series(self) -> dict[str, float | None]:
        """Raw current liabilities — same rationale as `cash_series()`
        above: used internally by `current_ratio_series()`/
        `quick_ratio_series()`/`cash_ratio_series()` but never itself
        exposed until the Balance Sheet Analysis Engine needed the raw
        figure for its Capital-Employed calc (Total Assets - Current
        Liabilities)."""
        return dict(self._bal_series("current_liabilities"))

    # ── Cash Conversion Cycle ─────────────────────────────────────────────────

    def cash_conversion_cycle_series(self) -> dict[str, float | None]:
        """CCC = Inventory Days + Receivable Days - Payable Days."""
        result = {}
        inv_d = self.inventory_days_series()
        rec_d = self.receivable_days_series()
        pay_d = self.payable_days_series()
        years = set(inv_d.keys()) & set(rec_d.keys()) & set(pay_d.keys())
        for y in sorted(years):
            i = inv_d.get(y)
            r = rec_d.get(y)
            p = pay_d.get(y)
            if i is not None and r is not None and p is not None:
                result[y] = round(i + r - p, 1)
            else:
                result[y] = None
        return result

    def cash_conversion_cycle_latest(self) -> float | None:
        return _latest(self.cash_conversion_cycle_series())

    # ── Normalized EPS (3Y average — mid-cycle approximation) ────────────────

    def normalized_eps(self) -> float | None:
        """3-year average diluted EPS — smooths out single-year distortions."""
        return _series_avg(self._income_series("diluted_eps"), 3)

    # ── Valuation ─────────────────────────────────────────────────────────────

    def pe_ratio(self) -> float | None:
        return self._mkt("trailing_pe")

    def forward_pe(self) -> float | None:
        return self._mkt("forward_pe")

    def pb_ratio(self) -> float | None:
        return self._mkt("price_to_book")

    def ev_to_ebitda(self) -> float | None:
        return self._mkt("ev_to_ebitda")

    def ev_to_sales(self) -> float | None:
        return self._mkt("ev_to_revenue")

    def dividend_yield(self) -> float | None:
        # Real bug found 2026-09-15: yfinance's `dividendYield` field is
        # already a percentage (confirmed live across 5 tickers — ITC 6.16,
        # Jyothy 1.79, HDFC Bank 1.84, TCS 2.95, Reliance 0.48 — all
        # plausible real yields, not fractions like 0.0616), so multiplying
        # by 100 here produced "616.0%" instead of "6.16%" for ITC.
        dy = self._mkt("dividend_yield")
        return round(dy, 2) if dy else None

    def fcf_yield(self) -> float | None:
        mc = self._mkt("market_cap")
        fcf = self.fcf_latest()
        if mc and fcf and mc > 0:
            return round(fcf / mc * 100, 2)
        return None

    def p_fcf(self) -> float | None:
        mc = self._mkt("market_cap")
        fcf = self.fcf_latest()
        if mc and fcf and fcf > 0:
            return round(mc / fcf, 2)
        return None

    def peg_ratio(self) -> float | None:
        """PEG = Trailing P/E / EPS CAGR 3Y. Meaningful only when both positive."""
        pe = self.pe_ratio()
        eps_growth = self.eps_cagr(3)
        if pe is None or eps_growth is None:
            return None
        if pe <= 0 or eps_growth <= 0:
            return None
        return round(pe / eps_growth, 2)

    def earnings_yield(self) -> float | None:
        """Earnings Yield = 1/PE × 100 — inverse of P/E, comparable to bond yield."""
        pe = self.pe_ratio()
        if pe and pe > 0:
            return round(100.0 / pe, 2)
        return None

    def ev_to_fcf(self) -> float | None:
        """EV / FCF — capital-structure-neutral equivalent of P/FCF."""
        ev = self._mkt("enterprise_value")
        fcf = self.fcf_latest()
        if ev and fcf and fcf > 0:
            return round(ev / fcf, 2)
        return None

    # ── Historical valuation (price-implied P/E per year) ────────────────────

    def implied_pe_series(self) -> dict[str, float | None]:
        """
        Approximate historical P/E per year using current shares outstanding
        and annual EPS. Useful for trend view even though share count drifts.
        """
        shares = self._mkt("shares_outstanding")
        price_now = self._mkt("current_price")
        mc_now = self._mkt("market_cap")
        if not shares or shares <= 0:
            return {}

        # derive price per share from market cap if current_price missing
        if not price_now and mc_now:
            price_now = mc_now / shares

        if not price_now:
            return {}

        eps_s = self._income_series("diluted_eps")
        result = {}
        for y, eps in eps_s.items():
            if eps and eps > 0:
                result[y] = round(price_now / eps, 1)
            else:
                result[y] = None
        return result

    # ── Comprehensive metrics dict ────────────────────────────────────────────

    def compute_all(self) -> dict:
        years = self.available_years()
        roe = self.roe_series()
        roa = self.roa_series()
        roce = self.roce_series()
        roic = self.roic_series()
        ebitda_m = self.ebitda_margin_series()
        pat_m = self.pat_margin_series()
        gross_m = self.gross_margin_series()
        ebit_m = self.ebit_margin_series()
        fcf_s = self.fcf_series()
        d_e = self.debt_to_equity_series()
        nd_ebitda = self.net_debt_to_ebitda_series()
        int_cov = self.interest_coverage_series()
        curr_ratio = self.current_ratio_series()
        quick_r = self.quick_ratio_series()
        inv_days = self.inventory_days_series()
        rec_days = self.receivable_days_series()
        pay_days = self.payable_days_series()
        ccc = self.cash_conversion_cycle_series()
        cfo_pat = self.cfo_to_pat_series()
        fcf_pat = self.fcf_to_pat_series()
        fcf_mg = self.fcf_margin_series()
        at = self.asset_turnover_series()
        capex_rev = self.capex_to_revenue_series()
        nd = self.net_debt_series()
        impl_pe = self.implied_pe_series()
        cyclicality = self.cyclicality_analysis()
        wc_trends = self.working_capital_trends()
        roic_decomp = self.roic_decomposition()

        def trend(s): return trend_direction(_sorted_values(s)) if s else INSUFFICIENT

        diag = self._fd.get("diagnostics", {})

        return {
            "years_available": years,
            "data_years": len(years),
            "latest_fy": diag.get("latest_fy"),
            "missing_fields": diag.get("missing_fields", []),
            "data_is_stale": diag.get("is_stale", False),
            "fetched_at": self._fd.get("fetched_at"),

            # Growth
            "revenue_cagr_3y": self.revenue_cagr(3),
            "revenue_cagr_5y": self.revenue_cagr(5),
            "revenue_cagr_10y": self.revenue_cagr(10),
            "ebitda_cagr_3y": self.ebitda_cagr(3),
            "pat_cagr_3y": self.pat_cagr(3),
            "pat_cagr_5y": self.pat_cagr(5),
            "pat_cagr_10y": self.pat_cagr(10),
            "eps_cagr_3y": self.eps_cagr(3),
            "eps_cagr_5y": self.eps_cagr(5),
            "eps_cagr_10y": self.eps_cagr(10),
            "fcf_cagr_3y": self.fcf_cagr(3),

            # Profitability — latest
            "gross_margin": _latest(gross_m),
            "ebitda_margin": _latest(ebitda_m),
            "ebit_margin": _latest(ebit_m),
            "pat_margin": _latest(pat_m),
            "roe": _latest(roe),
            "roa": _latest(roa),
            "roce": _latest(roce),
            "roic": _latest(roic),
            "normalized_eps": self.normalized_eps(),

            # Profitability — series
            "gross_margin_series": gross_m,
            "ebitda_margin_series": ebitda_m,
            "ebit_margin_series": ebit_m,
            "pat_margin_series": pat_m,
            "roe_series": roe,
            "roa_series": roa,
            "roce_series": roce,
            "roic_series": roic,

            # Profitability — trends
            "roe_trend": trend(roe),
            "roa_trend": trend(roa),
            "roce_trend": trend(roce),
            "ebitda_margin_trend": trend(ebitda_m),
            "pat_margin_trend": trend(pat_m),

            # Cash Flow
            "cfo_latest": _latest(self._cf_series("operating_cash_flow")),
            "fcf_latest": self.fcf_latest(),
            "p_fcf": self.p_fcf(),
            "ev_to_fcf": self.ev_to_fcf(),
            "cfo_to_pat": _latest(cfo_pat),
            "fcf_to_pat": _latest(fcf_pat),
            "fcf_margin": _latest(fcf_mg),
            "fcf_series": fcf_s,
            "cfo_to_pat_series": cfo_pat,
            "fcf_to_pat_series": fcf_pat,
            "fcf_trend": trend(fcf_s),

            # Revenue + PAT series
            "revenue_series": self._income_series("revenue"),
            "ebitda_series": self._income_series("ebitda"),
            "pat_series": self._income_series("net_income"),
            "eps_series": self._income_series("diluted_eps"),
            "cfo_series": self._cf_series("operating_cash_flow"),
            "capex_series": self._cf_series("capital_expenditure"),

            # Balance Sheet
            "debt_to_equity": _latest(d_e),
            "net_debt": _latest(nd),
            "net_debt_to_ebitda": _latest(nd_ebitda),
            "interest_coverage": _latest(int_cov),
            "current_ratio": _latest(curr_ratio),
            "quick_ratio": self.quick_ratio_latest(),
            "cash_ratio": self.cash_ratio_latest(),
            "d_e_series": d_e,
            "net_debt_series": nd,
            "net_debt_ebitda_series": nd_ebitda,
            "int_cov_series": int_cov,
            "curr_ratio_series": curr_ratio,
            "quick_ratio_series": quick_r,
            "cash_ratio_series": self.cash_ratio_series(),
            "cash_series": self.cash_series(),
            "current_liabilities_series": self.current_liabilities_series(),
            # Debt/Equity is "lower is better" — flip the raw value-direction
            # trend before exposing it (see flip_trend()'s own docstring for
            # the real bug this fixes: a falling D/E was shown as
            # "Deteriorating" in red, the opposite of the truth).
            "debt_trend": flip_trend(trend(d_e)),

            # Efficiency
            "inventory_days": _latest(inv_days),
            "receivable_days": _latest(rec_days),
            "payable_days": _latest(pay_days),
            "cash_conversion_cycle": self.cash_conversion_cycle_latest(),
            "asset_turnover": _latest(at),
            "capex_to_revenue": _latest(capex_rev),
            "inventory_days_series": inv_days,
            "receivable_days_series": rec_days,
            "payable_days_series": pay_days,
            "ccc_series": ccc,

            # Valuation
            "pe_ratio": self.pe_ratio(),
            "forward_pe": self.forward_pe(),
            "pb_ratio": self.pb_ratio(),
            "ev_to_ebitda": self.ev_to_ebitda(),
            "ev_to_sales": self.ev_to_sales(),
            "peg_ratio": self.peg_ratio(),
            "earnings_yield": self.earnings_yield(),
            "dividend_yield": self.dividend_yield(),
            "fcf_yield": self.fcf_yield(),
            "market_cap": self._mkt("market_cap"),
            "enterprise_value": self._mkt("enterprise_value"),
            "implied_pe_series": impl_pe,

            # Historical averages
            "ebitda_margin_3y_avg": _series_avg(ebitda_m, 3),
            "ebitda_margin_5y_avg": _series_avg(ebitda_m, 5),
            "pat_margin_3y_avg": _series_avg(pat_m, 3),
            "pat_margin_5y_avg": _series_avg(pat_m, 5),
            "roce_3y_avg": _series_avg(roce, 3),
            "roce_5y_avg": _series_avg(roce, 5),
            "roe_3y_avg": _series_avg(roe, 3),
            "roe_5y_avg": _series_avg(roe, 5),
            "roa_3y_avg": _series_avg(roa, 3),
            "roa_5y_avg": _series_avg(roa, 5),
            "debt_to_equity_3y_avg": _series_avg(d_e, 3),
            "debt_to_equity_5y_avg": _series_avg(d_e, 5),
            "fcf_to_pat_3y_avg": _series_avg(fcf_pat, 3),
            "fcf_to_pat_5y_avg": _series_avg(fcf_pat, 5),
            "net_debt_to_ebitda_3y_avg": _series_avg(nd_ebitda, 3),
            "net_debt_to_ebitda_5y_avg": _series_avg(nd_ebitda, 5),
            "interest_coverage_3y_avg": _series_avg(int_cov, 3),
            "asset_turnover_3y_avg": _series_avg(at, 3),
            "inventory_days_3y_avg": _series_avg(inv_days, 3),
            "receivable_days_3y_avg": _series_avg(rec_days, 3),
            "gross_margin_3y_avg": _series_avg(gross_m, 3),
            "gross_margin_5y_avg": _series_avg(gross_m, 5),
            "implied_pe_3y_avg": _series_avg(impl_pe, 3),
            "implied_pe_5y_avg": _series_avg(impl_pe, 5),

            # ── Cyclicality Analysis ──────────────────────────────────────────
            "is_cyclical":             cyclicality["is_cyclical"],
            "ebitda_margin_cv":        cyclicality["ebitda_margin_cv"],
            "ebitda_margin_peak":      cyclicality["ebitda_margin_peak"],
            "ebitda_margin_trough":    cyclicality["ebitda_margin_trough"],
            "cycle_position":          cyclicality["cycle_position"],
            "roce_peak":               cyclicality["roce_peak"],
            "roce_trough":             cyclicality["roce_trough"],
            "roce_cycle_position":     cyclicality["roce_cycle_position"],

            # ── Working Capital Cycle Trends ──────────────────────────────────
            "inventory_days_trend":    wc_trends["inventory_days_trend"],
            "receivable_days_trend":   wc_trends["receivable_days_trend"],
            "payable_days_trend":      wc_trends["payable_days_trend"],
            "ccc_trend":               wc_trends["ccc_trend"],
            "wc_to_revenue_trend":     wc_trends["wc_to_revenue_trend"],
            "working_capital_latest":  wc_trends["working_capital_latest"],
            "wc_to_revenue_latest":    wc_trends["wc_to_revenue_latest"],
            "ccc_series":              ccc,

            # ── ROIC Decomposition ────────────────────────────────────────────
            "nopat_margin_latest":     roic_decomp["nopat_margin_latest"],
            "capital_turnover_latest": roic_decomp["capital_turnover_latest"],
            "nopat_margin_3y_avg":     roic_decomp["nopat_margin_3y_avg"],
            "capital_turnover_3y_avg": roic_decomp["capital_turnover_3y_avg"],
            "nopat_margin_series":     roic_decomp["nopat_margin_series"],
            "capital_turnover_series": roic_decomp["capital_turnover_series"],

            # ── Piotroski F-Score ──────────────────────────────────────────────
            "piotroski": self.piotroski_f_score(),
        }



def compute_metrics(financial_data: dict) -> dict:
    """Entry point for the calculation engine."""
    calc = MetricsCalculator(financial_data)
    return calc.compute_all()
