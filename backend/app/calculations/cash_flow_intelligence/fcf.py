"""Free Cash Flow (spec §19-20) — Screener's own reported `free_cash_flow`
is the primary figure (top-level `.cash_flow()` ingestion), cross-checked
against `CFO − |Capex|` computed here from the real schedule data; FCF
quality classification from multi-period history.
"""
from __future__ import annotations

_DIVERGENCE_TOLERANCE_PCT = 5.0


def compute_fcf(reported_fcf: float | None, cfo: float | None, capex: float | None) -> dict:
    """`capex` (fixed_assets_purchased) arrives negative-signed from
    Screener — FCF = CFO + capex (adding a negative number), matching the
    spec's own `FCF = CFO - Fixed Assets Purchased` when capex is
    expressed as a positive outflow magnitude."""
    computed_fcf = None
    if cfo is not None and capex is not None:
        computed_fcf = round(cfo + capex, 2)

    divergence_pct = None
    if reported_fcf is not None and computed_fcf is not None and reported_fcf:
        divergence_pct = round(abs(reported_fcf - computed_fcf) / abs(reported_fcf) * 100, 2)

    return {
        "reported_fcf": reported_fcf,
        "computed_fcf": computed_fcf,
        "divergence_pct": divergence_pct,
        "divergent": divergence_pct is not None and divergence_pct > _DIVERGENCE_TOLERANCE_PCT,
    }


def classify_fcf_quality(fcf_series: dict[str, float | None]) -> dict:
    """Spec §20 — never from one period. `CONSISTENT_POSITIVE_FCF` needs
    every available period positive; `PERSISTENT_NEGATIVE_FCF` needs every
    period negative; anything mixed is `VOLATILE_FCF` (or `INTERMITTENT_FCF`
    when positive/negative periods alternate rather than trend)."""
    values = [v for v in fcf_series.values() if v is not None]
    if len(values) < 2:
        return {"classification": "INSUFFICIENT_DATA", "periods_available": len(values)}

    positive_count = sum(1 for v in values if v > 0)
    negative_count = sum(1 for v in values if v < 0)

    if positive_count == len(values):
        classification = "CONSISTENT_POSITIVE_FCF"
    elif negative_count == len(values):
        classification = "PERSISTENT_NEGATIVE_FCF"
    else:
        # sign changes between consecutive periods -> alternating (intermittent);
        # otherwise a volatile-but-trending mix
        sorted_periods = sorted(fcf_series.items())
        signs = [1 if v > 0 else (-1 if v < 0 else 0) for _, v in sorted_periods if v is not None]
        flips = sum(1 for a, b in zip(signs, signs[1:]) if a != b and a != 0 and b != 0)
        classification = "INTERMITTENT_FCF" if flips >= max(1, len(signs) // 2) else "VOLATILE_FCF"

    return {
        "classification": classification,
        "periods_available": len(values),
        "positive_periods": positive_count,
        "negative_periods": negative_count,
    }
