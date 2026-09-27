"""CFO / Operating Profit conversion (spec §7-9) — the spec's mandatory
headline metric, genuinely new (not computed anywhere in this app before
this engine). CFO/PAT and multi-year cumulative conversion (spec §35-36).
"""
from __future__ import annotations

_CONVERSION_LOW_THRESHOLD_PCT = 50.0
_CONVERSION_HIGH_THRESHOLD_PCT = 100.0


def cfo_operating_profit_ratio(cfo: float | None, operating_profit: float | None) -> dict:
    """Spec §8's mandatory metric. Classification bands per spec §8-9:
    <50% / 50-100% / ~100% / >100% — the actual percentage is always
    preserved alongside the band, never replaced by it (spec's own
    instruction)."""
    if cfo is None or not operating_profit:
        return {"status": "MISSING_DATA", "ratio_pct": None, "band": None}
    ratio_pct = round(cfo / operating_profit * 100, 2)
    if ratio_pct < _CONVERSION_LOW_THRESHOLD_PCT:
        band = "<50%"
    elif ratio_pct < 90:
        band = "50-100%"
    elif ratio_pct <= 110:
        band = "~100%"
    else:
        band = ">100%"
    return {"status": "AVAILABLE", "ratio_pct": ratio_pct, "band": band}


def cumulative_conversion(cfo_series: dict[str, float], operating_profit_series: dict[str, float],
                           pat_series: dict[str, float], years: int) -> dict:
    """Spec §36 — cumulative CFO / cumulative Operating Profit and
    cumulative CFO / cumulative PAT over the most recent `years` periods.
    Never CAGR (the spec explicitly forbids CAGR on cash-flow figures that
    can cross zero) — a straight sum-then-ratio instead."""
    common_periods = sorted(set(cfo_series) & set(operating_profit_series))[-years:]
    if len(common_periods) < 2:
        return {"status": "MISSING_DATA", "periods_used": len(common_periods)}

    cum_cfo = sum(cfo_series[p] for p in common_periods)
    cum_op = sum(operating_profit_series[p] for p in common_periods)
    pat_periods = [p for p in common_periods if p in pat_series]
    cum_pat = sum(pat_series[p] for p in pat_periods) if len(pat_periods) == len(common_periods) else None

    return {
        "status": "AVAILABLE",
        "periods_used": len(common_periods),
        "cumulative_cfo": round(cum_cfo, 2),
        "cumulative_operating_profit": round(cum_op, 2),
        "cumulative_cfo_to_operating_profit_pct": round(cum_cfo / cum_op * 100, 2) if cum_op else None,
        "cumulative_pat": round(cum_pat, 2) if cum_pat is not None else None,
        "cumulative_cfo_to_pat_pct": round(cum_cfo / cum_pat * 100, 2) if cum_pat else None,
    }


def classify_conversion_trend(current_ratio_pct: float | None, prior_ratio_pct: float | None,
                               tolerance_pct: float = 5.0) -> str:
    """Spec §35's 4-way classification — STRONG/WEAK is about the LEVEL,
    IMPROVING/DETERIORATING is about the TREND; this function only handles
    the trend half (callers combine with the level via `band` above)."""
    if current_ratio_pct is None or prior_ratio_pct is None:
        return "UNKNOWN"
    delta = current_ratio_pct - prior_ratio_pct
    if abs(delta) <= tolerance_pct:
        return "STABLE_CASH_CONVERSION"
    return "IMPROVING_CASH_CONVERSION" if delta > 0 else "DETERIORATING_CASH_CONVERSION"
