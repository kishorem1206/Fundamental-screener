"""Screener.in's own ROCE — the single source for every ROCE the app shows
(2026-10-06, user's instruction: "ROCE from Screener alone for all pages").

Screener publishes a yearly "ROCE %" row in its Ratios section, stored as
`bs_ratio_roce_percent`. Before this module three different ROCE figures were
in use for the same company: Yahoo's EBIT / (total assets − current
liabilities), the balance-sheet engine's hybrid (Screener assets, Yahoo
current liabilities) and the framework's (PBT + interest) / average capital.
Sigma Solve showed 32.6%, 48% and 48.5% on three pages, and 76% against
Screener's 52% for FY2023.

Consolidated when Screener has at least two consolidated years, otherwise
standalone. Screener publishes no ROCE for banks and other lenders; callers
get an empty series for them and say so rather than substituting a formula.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import MetricDataPoint

SOURCE_LABEL = "Screener.in ratios (ROCE %)"


def series(db: Session, company_id: str) -> dict:
    """{"basis": "CONSOLIDATED" | "STANDALONE" | None, "values": {"2026-03-31": 48.0, ...}} ascending by year."""
    rows = (db.query(MetricDataPoint.period, MetricDataPoint.statement_type, MetricDataPoint.value)
            .filter(MetricDataPoint.company_id == company_id, MetricDataPoint.metric_key == "bs_ratio_roce_percent",
                    MetricDataPoint.source == "SCREENER", MetricDataPoint.value.isnot(None))
            .order_by(MetricDataPoint.retrieved_at.desc()).all())
    by_basis: dict[str, dict[str, float]] = {"CONSOLIDATED": {}, "STANDALONE": {}}
    for period, basis, value in rows:
        if basis in by_basis and period and len(period) == 10:
            by_basis[basis].setdefault(period, float(value))  # newest read wins
    for basis in ("CONSOLIDATED", "STANDALONE"):
        if len(by_basis[basis]) >= 2:
            return {"basis": basis, "values": dict(sorted(by_basis[basis].items()))}
    for basis in ("CONSOLIDATED", "STANDALONE"):
        if by_basis[basis]:
            return {"basis": basis, "values": dict(sorted(by_basis[basis].items()))}
    return {"basis": None, "values": {}}


def apply_to_metrics(metrics: dict, sources: dict, db: Session, company_id: str) -> bool:
    """Sets every ROCE field of `metrics` from Screener's row: the latest
    value, the five-year series, its trend, the 3- and 5-year averages and the
    peak / trough / cycle position. Returns False (and touches nothing) when
    Screener has no ROCE for the company."""
    from app.calculations.engine import trend_direction

    s = series(db, company_id)
    values = list(s["values"].items())
    if not values:
        return False
    recent = {f"FY{p[:4]}": v for p, v in values[-5:]}
    vals = list(recent.values())
    fields = {
        "roce": vals[-1], "roce_series": recent,
        "roce_3y_avg": round(sum(vals[-3:]) / len(vals[-3:]), 2), "roce_5y_avg": round(sum(vals) / len(vals), 2),
        "roce_peak": max(vals), "roce_trough": min(vals),
    }
    if len(vals) >= 2:
        fields["roce_trend"] = trend_direction(vals[-3:])  # last three years: a long turnaround series would read as volatile
        span = max(vals) - min(vals)
        fields["roce_cycle_position"] = round((vals[-1] - min(vals)) / span * 100, 1) if span > 0 else None
    for key, value in fields.items():
        if value is not None:
            metrics[key] = value
            sources[key] = "SCREENER_RATIOS"
    metrics["roce_basis"] = s["basis"]
    return True
