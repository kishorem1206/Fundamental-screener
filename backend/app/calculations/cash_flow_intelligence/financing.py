"""Financing Cash Flow — CFF breakdown (spec §24), debt financing
classification (spec §25, using GROSS raised/repaid — this engine's whole
reason for choosing Screener's schedules over yfinance), dividend/buyback
cash outflow (spec §27-28).
"""
from __future__ import annotations

_NET_BORROWING_FLAT_TOLERANCE = 1.0  # Cr — below this, call it NEUTRAL rather than a directional signal from rounding noise


def cff_breakdown(cff_period: dict[str, float | None]) -> dict:
    return {
        "borrowings_raised": cff_period.get("borrowings_raised"),
        "borrowings_repaid": cff_period.get("borrowings_repaid"),
        "interest_paid": cff_period.get("interest_paid"),
        "dividends_paid": cff_period.get("dividends_paid"),
        "financial_liabilities": cff_period.get("financial_liabilities"),
        "other_financing": cff_period.get("other_financing"),
    }


def debt_financing_analysis(borrowings_raised: float | None, borrowings_repaid: float | None) -> dict:
    """Spec §25: Net Debt Cash Flow = Raised - |Repaid| (repaid already
    arrives negative-signed from Screener, so this is a straight sum), a
    genuinely GROSS-figure-derived classification — yfinance could only
    ever give the net figure directly, never this breakdown."""
    if borrowings_raised is None or borrowings_repaid is None:
        return {"status": "MISSING_DATA", "classification": None}
    net_debt_cash_flow = round(borrowings_raised + borrowings_repaid, 2)
    if abs(net_debt_cash_flow) <= _NET_BORROWING_FLAT_TOLERANCE:
        classification = "NEUTRAL"
    elif net_debt_cash_flow > 0:
        classification = "NET_BORROWING"
    else:
        classification = "NET_DELEVERAGING"
    return {
        "status": "AVAILABLE",
        "borrowings_raised": borrowings_raised,
        "borrowings_repaid": borrowings_repaid,
        "net_debt_cash_flow": net_debt_cash_flow,
        "classification": classification,
    }


def dividend_analysis(dividends_paid: float | None, cfo: float | None, fcf: float | None) -> dict:
    """Spec §27. `dividends_paid` arrives negative-signed (an outflow);
    ratios use the absolute value against a positive CFO/FCF base."""
    if dividends_paid is None:
        return {"status": "MISSING_DATA"}
    abs_dividends = abs(dividends_paid)
    dividend_to_cfo = round(abs_dividends / cfo * 100, 2) if cfo else None
    dividend_to_fcf = round(abs_dividends / fcf * 100, 2) if fcf else None
    return {
        "status": "AVAILABLE",
        "dividends_paid": dividends_paid,
        "dividend_to_cfo_pct": dividend_to_cfo,
        "dividend_to_fcf_pct": dividend_to_fcf,
    }


def buyback_analysis(share_redemption: float | None, fcf: float | None, cfo: float | None) -> dict:
    """Spec §28. `share_redemption` is the closest Screener proxy
    ("Redemption/Cancellation of Shares," investing schedule) — surfaced
    as-is, never relabeled as a clean buyback figure (see
    `canonical_fields.NO_TRUE_BUYBACK_LINE_REASON`)."""
    if share_redemption is None or share_redemption == 0:
        return {"status": "MISSING_INPUT", "reason": "no share-redemption/buyback-adjacent line for this period"}
    abs_value = abs(share_redemption)
    return {
        "status": "PARTIAL",
        "buyback_proxy_value": share_redemption,
        "buyback_to_fcf_pct": round(abs_value / fcf * 100, 2) if fcf else None,
        "buyback_to_cfo_pct": round(abs_value / cfo * 100, 2) if cfo else None,
        "confidence": "LOW",
    }
