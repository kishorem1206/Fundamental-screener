"""A company's Screener annual history from the ledger, one basis throughout.

Consolidated when Screener has at least five consolidated years, otherwise
standalone — never a mix of the two inside one series. Return on capital
employed is Screener's own published yearly ROCE (calculations/screener_roce.py),
left out for a year whose net worth was negative, which is flagged instead.
Return on equity is net profit / average net worth from the same statements.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import MetricDataPoint

_KEYS = {
    "pnl_sales": "sales", "pnl_operating_profit": "operating_profit", "pnl_opm": "opm", "pnl_pbt": "pbt",
    "pnl_interest": "interest", "pnl_net_profit": "net_profit", "pnl_eps": "eps", "pnl_dividend_payout": "payout",
    "equity_capital": "equity_capital", "reserves": "reserves", "borrowings": "borrowings",
    "cf_free_cash_flow": "fcf", "cf_operating_cash_flow": "cfo", "total_assets": "total_assets",
}
# Days after a period end by which its results are public (SEBI LODR: 45 days for
# a quarter, 60 for the year's audited results) — used for point-in-time reads.
ANNUAL_LAG_DAYS, QUARTER_LAG_DAYS = 60, 45
_MIN_CONSOLIDATED_YEARS = 5


def _published_by(period: str, as_of, lag_days: int) -> bool:
    from datetime import date, timedelta

    return as_of is None or date.fromisoformat(period) + timedelta(days=lag_days) <= as_of


def annual(db: Session, company_id: str, as_of=None) -> dict:
    """{"basis": ..., "years": [...ascending ISO year-ends], "rows": {year: {field: value}}}

    With `as_of`, only the years whose results were public by that date —
    the history as an investor could have read it then."""
    rows = (db.query(MetricDataPoint.metric_key, MetricDataPoint.period, MetricDataPoint.statement_type,
                     MetricDataPoint.value, MetricDataPoint.retrieved_at)
            .filter(MetricDataPoint.company_id == company_id, MetricDataPoint.source == "SCREENER",
                    MetricDataPoint.metric_key.in_(list(_KEYS)))
            .order_by(MetricDataPoint.retrieved_at.desc()).all())
    by_basis: dict[str, dict[str, dict]] = {"CONSOLIDATED": {}, "STANDALONE": {}}
    for key, period, basis, value, _ in rows:
        if value is None or period == "TTM" or basis not in by_basis or len(period) != 10:
            continue
        if not _published_by(period, as_of, ANNUAL_LAG_DAYS):
            continue
        by_basis[basis].setdefault(period, {}).setdefault(_KEYS[key], float(value))  # newest read wins
    cons = {p: r for p, r in by_basis["CONSOLIDATED"].items() if "sales" in r}
    basis = "CONSOLIDATED" if len(cons) >= _MIN_CONSOLIDATED_YEARS else "STANDALONE"
    table = {p: r for p, r in by_basis[basis].items() if "sales" in r}
    years = sorted(table)
    # ROCE is Screener's own published yearly figure (calculations/screener_roce.py), not a formula of ours
    from app.calculations import screener_roce
    published = screener_roce.series(db, company_id)["values"]
    for prev, cur in zip(years, years[1:]):
        a, b = table[prev], table[cur]
        if any(x.get("equity_capital", 0) + x.get("reserves", 0) <= 0 for x in (a, b) if "reserves" in x):
            # equity wiped out by losses: a return on what is left is meaningless (and flatters)
            b["negative_net_worth"] = True
        else:
            if cur in published:
                b["roce"] = published[cur]
            nw = [x.get("equity_capital", 0) + x.get("reserves", 0) for x in (a, b) if "reserves" in x]
            if len(nw) == 2 and sum(nw) > 0 and "net_profit" in b:
                b["roe"] = b["net_profit"] / (sum(nw) / 2) * 100
        for x in (a, b):
            if "reserves" in x:
                x["capital_employed"] = x.get("equity_capital", 0) + x["reserves"] + x.get("borrowings", 0)
                x["net_worth"] = x.get("equity_capital", 0) + x["reserves"]
    return {"basis": basis if years else None, "years": years, "rows": table,
            "source": f"Screener.in annual statements ({basis.title()})" if years else None}


def cagr(table: dict, field: str, span: int) -> float | None:
    years = [y for y in table["years"] if table["rows"][y].get(field) is not None]
    if len(years) < span + 1:
        return None
    start, end = table["rows"][years[-span - 1]][field], table["rows"][years[-1]][field]
    if start <= 0 or end <= 0:
        return None
    return ((end / start) ** (1 / span) - 1) * 100


_QKEYS = {"qtr_sales": "sales", "qtr_operating_profit": "operating_profit", "qtr_net_profit": "net_profit",
          "qtr_eps": "eps", "qtr_opm": "opm"}


def quarterly(db: Session, company_id: str, as_of=None) -> dict:
    """Screener quarterly results, one basis throughout (consolidated when it
    has at least eight quarters, else standalone)."""
    rows = (db.query(MetricDataPoint.metric_key, MetricDataPoint.period, MetricDataPoint.statement_type, MetricDataPoint.value)
            .filter(MetricDataPoint.company_id == company_id, MetricDataPoint.source == "SCREENER",
                    MetricDataPoint.metric_key.in_(list(_QKEYS)))
            .order_by(MetricDataPoint.retrieved_at.desc()).all())
    by_basis: dict[str, dict[str, dict]] = {"CONSOLIDATED": {}, "STANDALONE": {}}
    for key, period, basis, value in rows:
        if value is None or basis not in by_basis or len(period) != 10 or not _published_by(period, as_of, QUARTER_LAG_DAYS):
            continue
        by_basis[basis].setdefault(period, {}).setdefault(_QKEYS[key], float(value))
    cons = {p: r for p, r in by_basis["CONSOLIDATED"].items() if "sales" in r}
    basis = "CONSOLIDATED" if len(cons) >= 8 else "STANDALONE"
    table = {p: r for p, r in by_basis[basis].items() if "sales" in r}
    return {"basis": basis, "quarters": sorted(table), "rows": table,
            "source": f"Screener.in quarterly results ({basis.title()})"}
