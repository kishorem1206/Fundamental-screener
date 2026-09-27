"""Deterministic "what changed" flags over a quarterly series — a small,
cheap rule set, same spirit as `pl_intelligence/rules.py`'s flag pattern but
on a quarterly cadence. Every flag is a plain arithmetic threshold check,
no LLM, no external data.
"""
from __future__ import annotations

import statistics

_MARGIN_INFLECTION_PP = 3.0  # QoQ OPM swing beyond this = "inflection"
_OTHER_INCOME_DEPENDENCY_RATIO = 0.25  # other_income/PBT beyond this = flagged
_TAX_RATE_BAND_PP = 5.0  # qtr_tax_pct swing vs trailing average beyond this = anomaly


def sequential_deceleration_flags(qoq_sales_growth: dict[str, float]) -> list[dict]:
    """Fires on a period where QoQ sales growth turns negative immediately
    after 2+ consecutive positive-growth quarters."""
    periods = sorted(qoq_sales_growth.keys())
    flags = []
    for i in range(2, len(periods)):
        p0, p1, p2 = periods[i - 2], periods[i - 1], periods[i]
        if qoq_sales_growth[p0] > 0 and qoq_sales_growth[p1] > 0 and qoq_sales_growth[p2] < 0:
            flags.append({
                "flag": "sequential_deceleration",
                "period": p2,
                "detail": f"QoQ sales growth turned negative ({qoq_sales_growth[p2]}%) after two consecutive positive quarters",
            })
    return flags


def margin_inflection_flags(qoq_opm: dict[str, float]) -> list[dict]:
    flags = []
    for period, delta in qoq_opm.items():
        if abs(delta) >= _MARGIN_INFLECTION_PP:
            direction = "expanded" if delta > 0 else "contracted"
            flags.append({
                "flag": "margin_inflection",
                "period": period,
                "detail": f"Operating margin {direction} {abs(delta)} pp quarter-on-quarter",
            })
    return flags


def other_income_dependency_flags(other_income: dict[str, float], pbt: dict[str, float]) -> list[dict]:
    flags = []
    for period, oi in other_income.items():
        pbt_v = pbt.get(period)
        if pbt_v is None or pbt_v <= 0 or oi is None:
            continue
        ratio = oi / pbt_v
        if ratio >= _OTHER_INCOME_DEPENDENCY_RATIO:
            flags.append({
                "flag": "other_income_dependency",
                "period": period,
                "detail": f"Other income was {round(ratio * 100, 1)}% of PBT — earnings quality signal, not core-business strength",
            })
    return flags


def tax_rate_anomaly_flags(tax_pct: dict[str, float]) -> list[dict]:
    periods = sorted(tax_pct.keys())
    flags = []
    for i, period in enumerate(periods):
        trailing = [tax_pct[p] for p in periods[max(0, i - 4):i]]
        if len(trailing) < 2:
            continue
        avg = statistics.mean(trailing)
        delta = tax_pct[period] - avg
        if abs(delta) >= _TAX_RATE_BAND_PP:
            flags.append({
                "flag": "tax_rate_anomaly",
                "period": period,
                "detail": f"Tax rate {tax_pct[period]}% vs trailing average {round(avg, 1)}% — likely a one-off item, not a sustainable PAT change",
            })
    return flags


def compute_flags(
    *, qoq_sales_growth: dict[str, float], qoq_opm: dict[str, float],
    other_income: dict[str, float], pbt: dict[str, float], tax_pct: dict[str, float],
) -> list[dict]:
    flags = []
    flags += sequential_deceleration_flags(qoq_sales_growth)
    flags += margin_inflection_flags(qoq_opm)
    flags += other_income_dependency_flags(other_income, pbt)
    flags += tax_rate_anomaly_flags(tax_pct)
    return sorted(flags, key=lambda f: f["period"], reverse=True)
