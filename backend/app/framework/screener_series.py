"""A company's Screener annual history from the ledger, one basis throughout.

Consolidated when Screener has at least five consolidated years, otherwise
standalone — never a mix of the two inside one series. Return on capital
employed is worked out here (left out for a year whose net worth was negative,
which is flagged instead) from the same statements, the way Screener
defines it: (profit before tax + interest) / average (equity + reserves +
borrowings).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import MetricDataPoint

_KEYS = {
    "pnl_sales": "sales", "pnl_operating_profit": "operating_profit", "pnl_opm": "opm", "pnl_pbt": "pbt",
    "pnl_interest": "interest", "pnl_net_profit": "net_profit", "pnl_eps": "eps", "pnl_dividend_payout": "payout",
    "equity_capital": "equity_capital", "reserves": "reserves", "borrowings": "borrowings",
}
_MIN_CONSOLIDATED_YEARS = 5


def annual(db: Session, company_id: str) -> dict:
    """{"basis": ..., "years": [...ascending ISO year-ends], "rows": {year: {field: value}}}"""
    rows = (db.query(MetricDataPoint.metric_key, MetricDataPoint.period, MetricDataPoint.statement_type,
                     MetricDataPoint.value, MetricDataPoint.retrieved_at)
            .filter(MetricDataPoint.company_id == company_id, MetricDataPoint.source == "SCREENER",
                    MetricDataPoint.metric_key.in_(list(_KEYS)))
            .order_by(MetricDataPoint.retrieved_at.desc()).all())
    by_basis: dict[str, dict[str, dict]] = {"CONSOLIDATED": {}, "STANDALONE": {}}
    for key, period, basis, value, _ in rows:
        if value is None or period == "TTM" or basis not in by_basis or len(period) != 10:
            continue
        by_basis[basis].setdefault(period, {}).setdefault(_KEYS[key], float(value))  # newest read wins
    cons = {p: r for p, r in by_basis["CONSOLIDATED"].items() if "sales" in r}
    basis = "CONSOLIDATED" if len(cons) >= _MIN_CONSOLIDATED_YEARS else "STANDALONE"
    table = {p: r for p, r in by_basis[basis].items() if "sales" in r}
    years = sorted(table)
    for prev, cur in zip(years, years[1:]):
        a, b = table[prev], table[cur]
        if any(x.get("equity_capital", 0) + x.get("reserves", 0) <= 0 for x in (a, b) if "reserves" in x):
            # equity wiped out by losses: a return on what is left is meaningless (and flatters)
            b["negative_net_worth"] = True
        elif "pbt" in b and "interest" in b:
            caps = [x.get("equity_capital", 0) + x.get("reserves", 0) + x.get("borrowings", 0) for x in (a, b)
                    if "reserves" in x]
            if len(caps) == 2 and sum(caps) > 0:
                b["roce"] = (b["pbt"] + b["interest"]) / (sum(caps) / 2) * 100
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
