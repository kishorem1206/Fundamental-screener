"""
Scoring engine — translates calculated metrics into 0-100 component scores.
Universal defaults + sector-specific scoring for banks, NBFCs, insurance.

N/A handling:
  When a metric is None, it is excluded from the weighted average denominator
  rather than scored as 0. This prevents punishing a company for metrics that
  don't apply to its business model (e.g. EBITDA margin for banks).

Financial sector special handling:
  Banks  → _bank_*_score() functions (ROA/ROE focused, D/E thresholds ~10x)
  NBFCs  → _nbfc_*_score() functions (similar to banks, D/E thresholds ~6x)
  Others → universal _*_score() functions
"""
from __future__ import annotations
from typing import Any


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _score_metric(value: float | None, thresholds: list[tuple[float, float]]) -> float:
    """
    Map a metric value to a 0-100 score using a piecewise linear thresholds table.
    thresholds: [(value_breakpoint, score_at_breakpoint), ...] sorted ascending by value.
    """
    if value is None:
        return 50.0  # neutral for missing
    if not thresholds:
        return 50.0
    # Below minimum
    if value <= thresholds[0][0]:
        return thresholds[0][1]
    # Above maximum
    if value >= thresholds[-1][0]:
        return thresholds[-1][1]
    # Interpolate
    for i in range(1, len(thresholds)):
        lo_v, lo_s = thresholds[i - 1]
        hi_v, hi_s = thresholds[i]
        if lo_v <= value <= hi_v:
            if hi_v == lo_v:
                return lo_s
            t = (value - lo_v) / (hi_v - lo_v)
            return lo_s + t * (hi_s - lo_s)
    return 50.0


# ── Universal scoring thresholds ──────────────────────────────────────────────

GROWTH_SCORE_CONFIG = {
    "revenue_cagr_3y":  [(0, 20), (5, 40), (10, 60), (15, 75), (20, 90), (30, 100)],
    "pat_cagr_3y":      [(0, 20), (5, 40), (10, 60), (15, 75), (20, 90), (30, 100)],
    "eps_cagr_3y":      [(0, 20), (5, 40), (10, 65), (15, 80), (20, 95), (25, 100)],
    "fcf_cagr_3y":      [(0, 20), (5, 45), (10, 65), (15, 80), (20, 90), (25, 100)],
}

PROFITABILITY_SCORE_CONFIG = {
    "ebitda_margin":    [(0, 10), (5, 30), (10, 50), (15, 65), (20, 80), (25, 90), (35, 100)],
    "pat_margin":       [(0, 10), (2, 25), (5, 45), (10, 65), (15, 80), (20, 95), (25, 100)],
    "roe":              [(0, 10), (8, 30), (12, 50), (15, 65), (20, 80), (25, 90), (30, 100)],
    "roce":             [(0, 10), (8, 30), (12, 50), (15, 65), (20, 80), (25, 90), (30, 100)],
}

CASHFLOW_SCORE_CONFIG = {
    "cfo_to_pat":       [(-50, 0), (0, 20), (50, 50), (70, 65), (80, 75), (90, 85), (100, 90), (120, 100)],
    "fcf_to_pat":       [(-50, 0), (0, 20), (50, 50), (70, 65), (80, 75), (90, 85), (100, 95), (120, 100)],
    "fcf_margin":       [(-10, 0), (0, 20), (3, 40), (5, 55), (8, 70), (12, 85), (15, 100)],
}

BALANCE_SHEET_SCORE_CONFIG = {
    # Lower D/E is better (inverted): score = (1 - D/E) scaled
    "debt_to_equity_inv": [(0.0, 100), (0.5, 80), (1.0, 60), (1.5, 40), (2.0, 25), (3.0, 10), (5.0, 0)],
    "interest_coverage":  [(0, 0), (1, 20), (2, 40), (3, 55), (5, 70), (8, 85), (10, 92), (15, 100)],
    "current_ratio":      [(0, 0), (0.5, 20), (1.0, 50), (1.2, 65), (1.5, 80), (2.0, 90), (3.0, 100)],
}

EFFICIENCY_SCORE_CONFIG = {
    "asset_turnover":   [(0.0, 10), (0.3, 30), (0.5, 50), (0.8, 65), (1.0, 75), (1.5, 85), (2.0, 100)],
    # lower inventory/receivable days is better
    "inv_days_inv":     [(0, 100), (15, 90), (30, 80), (45, 65), (60, 50), (90, 30), (120, 10), (200, 0)],
    "rec_days_inv":     [(0, 100), (15, 90), (30, 80), (60, 60), (90, 40), (120, 20), (180, 0)],
}

# Cost-to-income ratio thresholds — best-in-class Indian private banks run
# ~35-40% (HDFC/Kotak/ICICI, confirmed on real ingested data), PSU/mid-tier
# banks 45-55%, stressed ones 65%+. Lower is better (inverted).
BANK_EFFICIENCY_CONFIG = {
    "cost_to_income_ratio_inv": [(30, 100), (35, 90), (40, 80), (45, 65), (50, 50), (55, 35), (65, 20), (80, 5)],
    # Bank NIM (higher = better) — real ingested range confirmed live:
    # ICICI 4.36%, Kotak 4.53-4.60%, Axis 3.46%, SBI ~2.9%. A tight band
    # since banks' NIM is structurally similar (deposit-funded lending).
    "nim_bank": [(2.0, 20), (2.5, 40), (3.0, 55), (3.5, 70), (4.0, 85), (4.5, 95), (5.5, 100)],
    # NBFC NIM (higher = better) — deliberately a much wider band than
    # banks': this group spans Housing Finance (funded like a bank, NIM
    # ~3-4%) to gold-loan/microfinance NBFCs (wholesale-funded, lend at a
    # much wider spread, NIM often 8-14%+). A coarser proxy across a
    # genuinely heterogeneous group — better than no NIM signal at all,
    # but a Housing Finance company's NIM will read as structurally lower
    # here than a gold-loan NBFC's even when both are healthy for their
    # own sub-sector; there is no ready NIM-normalization across NBFC
    # sub-types in the data available to this app today.
    "nim_nbfc": [(2.0, 30), (4.0, 55), (6.0, 70), (8.0, 85), (10.0, 95), (13.0, 100)],
}

VALUATION_SCORE_CONFIG = {
    # Lower P/E is better (inverted) for value, but too low may be distress
    "pe_ratio_inv":     [(0, 60), (8, 80), (15, 90), (20, 80), (25, 70), (35, 50), (50, 30), (80, 10), (100, 0)],
    "ev_ebitda_inv":    [(0, 60), (5, 90), (8, 85), (12, 75), (16, 60), (20, 45), (25, 30), (35, 10)],
    "pb_ratio_inv":     [(0, 50), (0.5, 80), (1.0, 90), (2.0, 75), (3.0, 60), (5.0, 40), (8.0, 20), (15, 0)],
    "fcf_yield":        [(0, 10), (1, 30), (2, 50), (3, 65), (4, 75), (5, 85), (8, 100)],
}


# Recent-quarters-dominate blend (2026-09-27, explicit user brief): a
# multi-year CAGR can mask a real recent slowdown (Anthem Biosciences'
# revenue_cagr_3y of 26% alone scored ~93/100 while its trailing 4 quarters
# of revenue are flat-to-down against the 4 before that). `_QUARTERLY_GROWTH_WEIGHT`
# lets `app/calculations/quarterly_growth.py`'s recency-weighted quarterly
# score dominate the blend when it's available, without discarding the
# annual view entirely — a company can't score well on growth purely
# because of one strong recent quarter if its multi-year trend disagrees.
_QUARTERLY_GROWTH_WEIGHT = 0.65


def _annual_growth_score(m: dict) -> float:
    scores = []
    w = [0.35, 0.3, 0.2, 0.15]
    keys = ["revenue_cagr_3y", "pat_cagr_3y", "eps_cagr_3y", "fcf_cagr_3y"]
    for key, weight in zip(keys, w):
        val = m.get(key)
        if val is not None:
            s = _score_metric(val, GROWTH_SCORE_CONFIG[key])
            scores.append((s, weight))
    if not scores:
        return 50.0
    total_w = sum(w for _, w in scores)
    return _clamp(sum(s * w for s, w in scores) / total_w)


def _growth_score(m: dict) -> float:
    """Blends the annual (FY CAGR) growth score with the quarterly growth
    score `app/calculations/quarterly_growth.py::compute_quarterly_growth()`
    computes and merges into `m` (as `quarterly_growth_score`) before this
    runs — see that module's docstring for the recent-quarters-first
    method. Exposes both raw component scores back onto `m` (mutated in
    place, same convention `screener_metrics_override.py` already uses) so
    the two numbers can be shown separately, not just the blend. Falls back
    to the annual score alone when no quarterly score is available (a
    recently-listed company with under 8 quarters on record, or a company
    whose quarterly ingestion hasn't run yet) — same degrade-gracefully
    contract as everywhere else in this module."""
    annual = _annual_growth_score(m)
    m["growth_score_annual"] = round(annual, 1)

    quarterly = m.get("quarterly_growth_score")
    if quarterly is None:
        return annual

    m["growth_score_quarterly"] = round(quarterly, 1)
    blended = _QUARTERLY_GROWTH_WEIGHT * quarterly + (1 - _QUARTERLY_GROWTH_WEIGHT) * annual
    return _clamp(blended)


def _profitability_score(m: dict) -> float:
    scores = []
    configs = [
        ("ebitda_margin", 0.3),
        ("pat_margin", 0.2),
        ("roe", 0.25),
        ("roce", 0.25),
    ]
    for key, weight in configs:
        val = m.get(key)
        if val is not None:
            s = _score_metric(val, PROFITABILITY_SCORE_CONFIG[key])
            scores.append((s, weight))
    if not scores:
        return 50.0
    total_w = sum(w for _, w in scores)
    return _clamp(sum(s * w for s, w in scores) / total_w)


def _cashflow_score(m: dict) -> float:
    scores = []
    configs = [
        ("cfo_to_pat", 0.35),
        ("fcf_to_pat", 0.35),
        ("fcf_margin", 0.3),
    ]
    for key, weight in configs:
        val = m.get(key)
        if val is not None:
            s = _score_metric(val, CASHFLOW_SCORE_CONFIG[key])
            scores.append((s, weight))
    if not scores:
        return 50.0
    total_w = sum(w for _, w in scores)
    return _clamp(sum(s * w for s, w in scores) / total_w)


def _balance_sheet_score(m: dict) -> float:
    scores = []
    de = m.get("debt_to_equity")
    if de is not None:
        s = _score_metric(de, BALANCE_SHEET_SCORE_CONFIG["debt_to_equity_inv"])
        scores.append((s, 0.35))
    ic = m.get("interest_coverage")
    if ic is not None:
        s = _score_metric(ic, BALANCE_SHEET_SCORE_CONFIG["interest_coverage"])
        scores.append((s, 0.35))
    cr = m.get("current_ratio")
    if cr is not None:
        s = _score_metric(cr, BALANCE_SHEET_SCORE_CONFIG["current_ratio"])
        scores.append((s, 0.3))
    if not scores:
        return 50.0
    total_w = sum(w for _, w in scores)
    return _clamp(sum(s * w for s, w in scores) / total_w)


def _efficiency_score(m: dict) -> float:
    scores = []
    at = m.get("asset_turnover")
    if at is not None:
        scores.append((_score_metric(at, EFFICIENCY_SCORE_CONFIG["asset_turnover"]), 0.4))
    inv = m.get("inventory_days")
    if inv is not None:
        scores.append((_score_metric(inv, EFFICIENCY_SCORE_CONFIG["inv_days_inv"]), 0.3))
    rec = m.get("receivable_days")
    if rec is not None:
        scores.append((_score_metric(rec, EFFICIENCY_SCORE_CONFIG["rec_days_inv"]), 0.3))
    if not scores:
        return 50.0
    total_w = sum(w for _, w in scores)
    return _clamp(sum(s * w for s, w in scores) / total_w)


def _valuation_score(m: dict) -> float:
    scores = []
    pe = m.get("pe_ratio")
    if pe and pe > 0:
        scores.append((_score_metric(pe, VALUATION_SCORE_CONFIG["pe_ratio_inv"]), 0.35))
    ev_ebitda = m.get("ev_to_ebitda")
    if ev_ebitda and ev_ebitda > 0:
        scores.append((_score_metric(ev_ebitda, VALUATION_SCORE_CONFIG["ev_ebitda_inv"]), 0.3))
    pb = m.get("pb_ratio")
    if pb and pb > 0:
        scores.append((_score_metric(pb, VALUATION_SCORE_CONFIG["pb_ratio_inv"]), 0.2))
    fy = m.get("fcf_yield")
    if fy is not None:
        scores.append((_score_metric(fy, VALUATION_SCORE_CONFIG["fcf_yield"]), 0.15))
    if not scores:
        return 50.0
    total_w = sum(w for _, w in scores)
    return _clamp(sum(s * w for s, w in scores) / total_w)


# ── Universal component weights ───────────────────────────────────────────────
#
# Valuation's weight was cut to 40% of its previous value across every dict
# in this file (2026-09-23, explicit user directive): "fundamentally good
# stocks will be in high valuation most of the times which is given by the
# public which doesn't depend on companies financials" — i.e. a stock
# trading expensive BECAUSE it's genuinely high-quality shouldn't have its
# overall quality score dragged down much by that same market-set price.
# `valuation_view` (CHEAP/ATTRACTIVE/FAIR/EXPENSIVE/VERY_EXPENSIVE) remains
# the dedicated signal for "is this cheap or expensive" — `overall` is now
# deliberately weighted toward the five fundamentals-only categories
# instead. Freed weight was redistributed proportionally across
# growth/profitability/cash_flow/balance_sheet/efficiency (each dict still
# sums to exactly 1.00) rather than handed disproportionately to any one
# category. See `Important md files/AGENTS.md` §12 for the worked example
# and `Important md files/ARCHITECTURE.md` for the historical note.
UNIVERSAL_WEIGHTS = {
    "growth":        0.25,
    "profitability": 0.21,
    "cash_flow":     0.19,
    "balance_sheet": 0.19,
    "efficiency":    0.10,
    "valuation":     0.06,
}

# Sector weight overrides — keyed by SectorFramework.sector_name. Mirrored
# exactly (same values, per sector_name) in each SectorFramework subclass's
# own `SECTOR_WEIGHTS` class attribute under app/sectors/ — that copy feeds
# the display-only `sector_analysis.sector_weights` API field, THIS dict is
# what actually computes `scores["overall"]` (see `recompute_overall()`
# below and `compute_scores()`'s `SECTOR_WEIGHTS.get(sector, UNIVERSAL_WEIGHTS)`
# lookup). Keep the two in sync by hand when either changes — confirmed via
# a 2026-09-23 audit that they had already drifted apart for Fintech and
# Utilities before this rewrite; both are now identical again.
SECTOR_WEIGHTS = {
    "Automobile": {
        "growth": 0.25, "profitability": 0.22, "cash_flow": 0.17,
        "balance_sheet": 0.13, "efficiency": 0.17, "valuation": 0.06,
    },
    # Banks: ROE/ROA dominate; traditional FCF and efficiency not applicable
    "Banks": {
        "growth": 0.22, "profitability": 0.36, "cash_flow": 0.06,
        "balance_sheet": 0.27, "efficiency": 0.03, "valuation": 0.06,
    },
    # NBFCs: similar to banks but slightly different balance sheet weight
    "NBFCs": {
        "growth": 0.25, "profitability": 0.31, "cash_flow": 0.06,
        "balance_sheet": 0.29, "efficiency": 0.03, "valuation": 0.06,
    },
    "Housing Finance": {
        "growth": 0.24, "profitability": 0.29, "cash_flow": 0.06,
        "balance_sheet": 0.32, "efficiency": 0.03, "valuation": 0.06,
    },
    "Microfinance": {
        "growth": 0.22, "profitability": 0.26, "cash_flow": 0.05,
        "balance_sheet": 0.37, "efficiency": 0.05, "valuation": 0.05,
    },
    "Gold Loans": {
        "growth": 0.27, "profitability": 0.30, "cash_flow": 0.09,
        "balance_sheet": 0.23, "efficiency": 0.06, "valuation": 0.05,
    },
    "Insurance": {
        "growth": 0.25, "profitability": 0.32, "cash_flow": 0.05,
        "balance_sheet": 0.26, "efficiency": 0.06, "valuation": 0.06,
    },
    # Fintech: efficiency is forced neutral (asset-light, no inventory/
    # receivable-days concept), so its weight is minimal here — growth and
    # cash_flow (FCF/PAT — the spec's own core chain endpoint) carry more.
    # Valuation still gets the highest weight of any sector here (0.10,
    # after the universal cut) since P/E is unreliable for a pre/newly-
    # profitable business and EV/Sales needs to do real work — but even
    # this "valuation matters most" sector now weighs it far less than
    # before the 2026-09-23 cut (was 0.25).
    "Fintech": {
        "growth": 0.29, "profitability": 0.21, "cash_flow": 0.25,
        "balance_sheet": 0.12, "efficiency": 0.03, "valuation": 0.10,
    },
    "Information Technology": {
        "growth": 0.27, "profitability": 0.27, "cash_flow": 0.21,
        "balance_sheet": 0.11, "efficiency": 0.08, "valuation": 0.06,
    },
    "Healthcare": {
        "growth": 0.25, "profitability": 0.22, "cash_flow": 0.20,
        "balance_sheet": 0.17, "efficiency": 0.10, "valuation": 0.06,
    },
    "Fast Moving Consumer Goods": {
        "growth": 0.22, "profitability": 0.26, "cash_flow": 0.21,
        "balance_sheet": 0.13, "efficiency": 0.13, "valuation": 0.05,
    },
    "Auto Ancillaries": {
        "growth": 0.24, "profitability": 0.22, "cash_flow": 0.17,
        "balance_sheet": 0.15, "efficiency": 0.17, "valuation": 0.05,
    },
    "Consumer Durables": {
        "growth": 0.25, "profitability": 0.23, "cash_flow": 0.17,
        "balance_sheet": 0.15, "efficiency": 0.14, "valuation": 0.06,
    },
    "Chemicals": {
        "growth": 0.24, "profitability": 0.23, "cash_flow": 0.17,
        "balance_sheet": 0.16, "efficiency": 0.14, "valuation": 0.06,
    },
    "Specialty Chemicals": {
        "growth": 0.25, "profitability": 0.26, "cash_flow": 0.17,
        "balance_sheet": 0.15, "efficiency": 0.11, "valuation": 0.06,
    },
    "Metals": {
        "growth": 0.21, "profitability": 0.23, "cash_flow": 0.20,
        "balance_sheet": 0.21, "efficiency": 0.10, "valuation": 0.05,
    },
    "Mining": {
        "growth": 0.19, "profitability": 0.23, "cash_flow": 0.23,
        "balance_sheet": 0.20, "efficiency": 0.10, "valuation": 0.05,
    },
    "Cement": {
        "growth": 0.22, "profitability": 0.23, "cash_flow": 0.19,
        "balance_sheet": 0.19, "efficiency": 0.12, "valuation": 0.05,
    },
    "Oil & Gas": {
        "growth": 0.18, "profitability": 0.22, "cash_flow": 0.24,
        "balance_sheet": 0.21, "efficiency": 0.10, "valuation": 0.05,
    },
    "Power": {
        "growth": 0.20, "profitability": 0.21, "cash_flow": 0.23,
        "balance_sheet": 0.22, "efficiency": 0.10, "valuation": 0.04,
    },
    "Utilities": {
        "growth": 0.20, "profitability": 0.21, "cash_flow": 0.23,
        "balance_sheet": 0.22, "efficiency": 0.10, "valuation": 0.04,
    },
    "Renewable Energy": {
        "growth": 0.26, "profitability": 0.19, "cash_flow": 0.21,
        "balance_sheet": 0.20, "efficiency": 0.10, "valuation": 0.04,
    },
    "Telecom": {
        "growth": 0.24, "profitability": 0.24, "cash_flow": 0.22,
        "balance_sheet": 0.22, "efficiency": 0.05, "valuation": 0.03,
    },
    "Retail": {
        "growth": 0.26, "profitability": 0.22, "cash_flow": 0.19,
        "balance_sheet": 0.16, "efficiency": 0.13, "valuation": 0.04,
    },
    "Real Estate": {
        "growth": 0.24, "profitability": 0.19, "cash_flow": 0.22,
        "balance_sheet": 0.25, "efficiency": 0.07, "valuation": 0.03,
    },
    "Construction": {
        "growth": 0.24, "profitability": 0.20, "cash_flow": 0.20,
        "balance_sheet": 0.22, "efficiency": 0.10, "valuation": 0.04,
    },
    "Infrastructure": {
        "growth": 0.22, "profitability": 0.20, "cash_flow": 0.25,
        "balance_sheet": 0.22, "efficiency": 0.08, "valuation": 0.03,
    },
    "Capital Goods": {
        "growth": 0.24, "profitability": 0.23, "cash_flow": 0.17,
        "balance_sheet": 0.19, "efficiency": 0.12, "valuation": 0.05,
    },
    "Industrials": {
        "growth": 0.24, "profitability": 0.23, "cash_flow": 0.17,
        "balance_sheet": 0.19, "efficiency": 0.12, "valuation": 0.05,
    },
    "Defence": {
        "growth": 0.27, "profitability": 0.22, "cash_flow": 0.17,
        "balance_sheet": 0.19, "efficiency": 0.10, "valuation": 0.05,
    },
    "Aviation": {
        "growth": 0.24, "profitability": 0.23, "cash_flow": 0.22,
        "balance_sheet": 0.22, "efficiency": 0.07, "valuation": 0.02,
    },
    "Hotels & Restaurants": {
        "growth": 0.24, "profitability": 0.23, "cash_flow": 0.20,
        "balance_sheet": 0.19, "efficiency": 0.10, "valuation": 0.04,
    },
    "Logistics": {
        "growth": 0.24, "profitability": 0.22, "cash_flow": 0.19,
        "balance_sheet": 0.19, "efficiency": 0.12, "valuation": 0.04,
    },
    "Media & Entertainment": {
        "growth": 0.27, "profitability": 0.23, "cash_flow": 0.21,
        "balance_sheet": 0.16, "efficiency": 0.08, "valuation": 0.05,
    },
    "Electronics": {
        "growth": 0.26, "profitability": 0.22, "cash_flow": 0.17,
        "balance_sheet": 0.19, "efficiency": 0.12, "valuation": 0.04,
    },
    # Previously ONLY defined in the matching SectorFramework subclass's
    # display-only `SECTOR_WEIGHTS` (app/sectors/diversified.py,
    # commodities_forest_materials.py, services.py, textiles.py) — these 4
    # sector_names had NO entry here at all, so any company routed to them
    # silently used UNIVERSAL_WEIGHTS for its real `overall` score instead
    # of its own sector's calibration (found during the 2026-09-23 audit
    # that produced this rewrite). Added here, using each sector's own
    # pre-cut values as the base for the same valuation-weight
    # transformation applied everywhere else in this dict.
    "Diversified": {
        "growth": 0.21, "profitability": 0.23, "cash_flow": 0.18,
        "balance_sheet": 0.18, "efficiency": 0.13, "valuation": 0.07,
    },
    "Forest Materials": {
        "growth": 0.21, "profitability": 0.23, "cash_flow": 0.19,
        "balance_sheet": 0.19, "efficiency": 0.13, "valuation": 0.05,
    },
    "Services": {
        "growth": 0.24, "profitability": 0.21, "cash_flow": 0.20,
        "balance_sheet": 0.19, "efficiency": 0.12, "valuation": 0.04,
    },
    "Textiles": {
        "growth": 0.27, "profitability": 0.22, "cash_flow": 0.15,
        "balance_sheet": 0.15, "efficiency": 0.16, "valuation": 0.05,
    },
}

# ── Financial-sector specific scoring configs ─────────────────────────────────

BANK_PROFITABILITY_CONFIG = {
    "roe": [(0, 5), (6, 20), (10, 40), (13, 60), (16, 75), (18, 87), (22, 100)],
    "roa": [(0, 5), (0.3, 20), (0.6, 40), (0.9, 60), (1.1, 75), (1.4, 88), (1.8, 100)],
    "pat_margin": [(0, 10), (5, 30), (10, 50), (15, 68), (20, 82), (25, 100)],
}
BANK_BALANCE_SHEET_CONFIG = {
    # Banks run 8-12x D/E naturally via deposits — different thresholds
    "debt_to_equity": [(0, 60), (5, 80), (10, 85), (13, 75), (16, 55), (20, 30), (25, 5)],
}
BANK_VALUATION_CONFIG = {
    # P/B is primary valuation for banks; quality banks command premium
    "pb_ratio": [(0.3, 40), (0.7, 60), (1.2, 78), (2.0, 85), (3.0, 76), (4.5, 58), (7.0, 30), (12, 5)],
    "pe_ratio": [(0, 50), (6, 72), (10, 88), (16, 82), (22, 68), (30, 50), (45, 28), (80, 8)],
}

NBFC_PROFITABILITY_CONFIG = {
    "roe": [(0, 5), (5, 18), (10, 40), (14, 60), (17, 76), (20, 88), (25, 100)],
    "roa": [(0, 5), (0.5, 22), (1.0, 42), (1.8, 60), (2.5, 78), (3.2, 92), (4.0, 100)],
    "pat_margin": [(0, 10), (5, 30), (10, 50), (15, 68), (20, 84), (25, 100)],
}
NBFC_BALANCE_SHEET_CONFIG = {
    # NBFCs: 3-7x D/E is typical; above 10x is concerning
    "debt_to_equity": [(0, 60), (2, 80), (4, 90), (6, 80), (8, 60), (10, 38), (14, 15), (18, 0)],
    "interest_coverage": [(0, 5), (1.0, 30), (1.3, 55), (1.6, 72), (2.0, 85), (2.5, 95), (3.0, 100)],
}
NBFC_VALUATION_CONFIG = {
    "pb_ratio": [(0.3, 35), (0.7, 55), (1.2, 72), (2.0, 82), (3.0, 78), (4.5, 60), (7.0, 35), (12, 5)],
    "pe_ratio": [(0, 45), (8, 68), (14, 85), (20, 80), (28, 65), (38, 45), (55, 22), (80, 5)],
}

# Fintech_Analysis_Framework.md §24: "Use P/S, EV/Sales, P/E when profitable,
# FCF yield, unit-economics-based valuation. Avoid valuation based solely on
# revenue growth." EV/Sales thresholds are deliberately much lower than
# EV/EBITDA's (typical Indian-listed fintech range ~2-12x vs EV/EBITDA's
# 5-35x, since sales includes all the cost lines EBITDA already stripped out).
FINTECH_VALUATION_CONFIG = {
    "ev_to_sales": [(0, 60), (2, 85), (4, 80), (6, 68), (9, 52), (13, 35), (18, 15), (25, 0)],
}


def classify_overall_rating(score: float) -> str:
    """Extracted out of `compute_scores()`'s inline `rating()` closure so
    `score_refinement.py` can re-derive `overall_rating` after recomputing
    `overall` — otherwise a refined score could silently carry a stale
    rating computed from the PRE-refinement overall."""
    if score >= 80: return "STRONG"
    if score >= 65: return "GOOD"
    if score >= 50: return "FAIR"
    if score >= 35: return "WEAK"
    return "POOR"


def recompute_overall(component_scores: dict, weights: dict) -> float:
    """Weighted sum over the 6 category scores using an arbitrary weights
    dict (`UNIVERSAL_WEIGHTS` or a `SECTOR_WEIGHTS` entry) — extracted out
    of `compute_scores()`'s own inline calculation below so
    `score_refinement.py`'s final orchestrator stage can recompute
    `overall` from REFINED component scores using the exact same formula,
    without duplicating it. `component_scores` missing a category defaults
    that category to 50.0 (neutral), matching every other N/A-handling
    convention in this module."""
    overall = sum(component_scores.get(cat, 50.0) * w for cat, w in weights.items())
    return round(_clamp(overall), 1)


def _weighted_avg(scored_pairs: list[tuple[float, float]]) -> float:
    """Weighted average from [(score, weight)] pairs, normalising over available weights."""
    if not scored_pairs:
        return 50.0
    total_w = sum(w for _, w in scored_pairs)
    if total_w == 0:
        return 50.0
    return _clamp(sum(s * w for s, w in scored_pairs) / total_w)


# ── Bank-specific component scorers ───────────────────────────────────────────

def _bank_profitability_score(m: dict) -> float:
    pairs = []
    roe = m.get("roe")
    if roe is not None:
        pairs.append((_score_metric(roe, BANK_PROFITABILITY_CONFIG["roe"]), 0.50))
    roa = m.get("roa")
    if roa is not None:
        pairs.append((_score_metric(roa, BANK_PROFITABILITY_CONFIG["roa"]), 0.40))
    pm = m.get("pat_margin")
    if pm is not None:
        pairs.append((_score_metric(pm, BANK_PROFITABILITY_CONFIG["pat_margin"]), 0.10))
    return _weighted_avg(pairs)


def _bank_balance_sheet_score(m: dict) -> float:
    pairs = []
    de = m.get("debt_to_equity")
    if de is not None:
        pairs.append((_score_metric(de, BANK_BALANCE_SHEET_CONFIG["debt_to_equity"]), 1.0))
    return _weighted_avg(pairs)


def _bank_cash_flow_score(m: dict) -> float:
    # Traditional FCF/PAT is NOT meaningful for banks — return neutral
    return 50.0


def _bank_efficiency_score(m: dict) -> float:
    """Cost-to-income ratio (lower = better) — the standard banking
    efficiency metric, merged into `m` from the BSE-quarterly-filing-
    sourced banking ledger (`app/sectors/banking_data_bridge.py`) by the
    orchestrator right before `compute_scores()` runs; see that bridge's
    docstring for the source/confidence tiers. Falls back to a neutral 50
    when unavailable — most banks don't have this on record yet (a pilot-
    sector rollout, ~9 of ~190 financial-sector stocks as of 2026-09-27).

    This used to be an unconditional `return 50.0` regardless of data
    availability (asset turnover, this function's universal-formula
    equivalent, genuinely doesn't apply to a bank's balance sheet — but
    that's a different claim than "efficiency doesn't matter for banks,"
    which was never true; cost-to-income is exactly the metric analysts
    use for this). Fixing the metric, not just the weight, per the
    2026-09-27 review: "efficiency is important, but the current metric
    implementation is wrong" — the weight was already cut in the same
    session on the (now outdated) assumption this would stay a constant.

    NIM (2026-09-27, explicit follow-up request) blended in at 40% —
    cost-to-income stays primary (60%) since it's the purer cost-discipline
    read, NIM leans more toward pricing power/spread, which already has
    some presence in profitability; renormalizes to whichever one is
    actually on record when only one is available, same convention as
    every other multi-metric scorer in this module (`_weighted_avg`)."""
    pairs = []
    cti = m.get("cost_to_income_ratio")
    if cti is not None:
        pairs.append((_score_metric(cti, BANK_EFFICIENCY_CONFIG["cost_to_income_ratio_inv"]), 0.60))
    nim = m.get("nim")
    if nim is not None:
        pairs.append((_score_metric(nim, BANK_EFFICIENCY_CONFIG["nim_bank"]), 0.40))
    if not pairs:
        return 50.0
    return _weighted_avg(pairs)


def _bank_valuation_score(m: dict) -> float:
    pairs = []
    pb = m.get("pb_ratio")
    if pb and pb > 0:
        pairs.append((_score_metric(pb, BANK_VALUATION_CONFIG["pb_ratio"]), 0.60))
    pe = m.get("pe_ratio")
    if pe and pe > 0:
        pairs.append((_score_metric(pe, BANK_VALUATION_CONFIG["pe_ratio"]), 0.40))
    return _weighted_avg(pairs)


# ── NBFC-specific component scorers ───────────────────────────────────────────

def _nbfc_profitability_score(m: dict) -> float:
    pairs = []
    roe = m.get("roe")
    if roe is not None:
        pairs.append((_score_metric(roe, NBFC_PROFITABILITY_CONFIG["roe"]), 0.50))
    roa = m.get("roa")
    if roa is not None:
        pairs.append((_score_metric(roa, NBFC_PROFITABILITY_CONFIG["roa"]), 0.40))
    pm = m.get("pat_margin")
    if pm is not None:
        pairs.append((_score_metric(pm, NBFC_PROFITABILITY_CONFIG["pat_margin"]), 0.10))
    return _weighted_avg(pairs)


def _nbfc_balance_sheet_score(m: dict) -> float:
    pairs = []
    de = m.get("debt_to_equity")
    if de is not None:
        pairs.append((_score_metric(de, NBFC_BALANCE_SHEET_CONFIG["debt_to_equity"]), 0.60))
    ic = m.get("interest_coverage")
    if ic is not None:
        pairs.append((_score_metric(ic, NBFC_BALANCE_SHEET_CONFIG["interest_coverage"]), 0.40))
    return _weighted_avg(pairs)


def _nbfc_cash_flow_score(m: dict) -> float:
    # Traditional FCF/PAT less meaningful; use PAT margin as proxy
    pm = m.get("pat_margin")
    if pm is not None:
        return _clamp(_score_metric(pm, NBFC_PROFITABILITY_CONFIG["pat_margin"]))
    return 50.0


def _nbfc_efficiency_score(m: dict) -> float:
    """Same metric/weights/rationale as `_bank_efficiency_score()` — NBFCs
    report cost-to-income and NIM too, ingested through the same pipeline
    (orchestrator.py gates it on sector in {"Banks", "NBFCs", "Housing
    Finance", "Microfinance", "Gold Loans"}). Uses `nim_nbfc`, a much wider
    threshold band than banks' — see that config's own comment on why."""
    pairs = []
    cti = m.get("cost_to_income_ratio")
    if cti is not None:
        pairs.append((_score_metric(cti, BANK_EFFICIENCY_CONFIG["cost_to_income_ratio_inv"]), 0.60))
    nim = m.get("nim")
    if nim is not None:
        pairs.append((_score_metric(nim, BANK_EFFICIENCY_CONFIG["nim_nbfc"]), 0.40))
    if not pairs:
        return 50.0
    return _weighted_avg(pairs)


def _nbfc_valuation_score(m: dict) -> float:
    pairs = []
    pb = m.get("pb_ratio")
    if pb and pb > 0:
        pairs.append((_score_metric(pb, NBFC_VALUATION_CONFIG["pb_ratio"]), 0.55))
    pe = m.get("pe_ratio")
    if pe and pe > 0:
        pairs.append((_score_metric(pe, NBFC_VALUATION_CONFIG["pe_ratio"]), 0.45))
    return _weighted_avg(pairs)


# ── Fintech-specific valuation ────────────────────────────────────────────────

def _fintech_valuation_score(m: dict) -> float:
    """Fintech_Analysis_Framework.md §24 — EV/Sales is the primary lens
    (works whether or not the company is profitable yet), P/E only counts
    when the company actually has positive earnings (a fintech that just
    turned profitable on a tiny PAT base would otherwise get a wildly
    distorted P/E score), FCF yield captures cash generation independent
    of accounting profit. Deliberately never scores on revenue growth
    alone — that's `_growth_score()`'s job, not valuation's."""
    pairs = []
    ev_sales = m.get("ev_to_sales")
    if ev_sales and ev_sales > 0:
        pairs.append((_score_metric(ev_sales, FINTECH_VALUATION_CONFIG["ev_to_sales"]), 0.45))
    pe = m.get("pe_ratio")
    pat_margin = m.get("pat_margin")
    if pe and pe > 0 and pat_margin is not None and pat_margin > 0:
        pairs.append((_score_metric(pe, VALUATION_SCORE_CONFIG["pe_ratio_inv"]), 0.25))
    fy = m.get("fcf_yield")
    if fy is not None:
        pairs.append((_score_metric(fy, VALUATION_SCORE_CONFIG["fcf_yield"]), 0.30))
    return _weighted_avg(pairs)


# Sector names that use financial-sector specific scoring
_BANK_SECTORS = {"Banks"}
_NBFC_SECTORS = {"NBFCs", "Housing Finance", "Microfinance", "Gold Loans"}
_INSURANCE_SECTORS = {"Insurance"}
_FINTECH_SECTORS = {"Fintech"}


def compute_scores(metrics: dict, sector: str = "") -> dict:
    """
    Compute component scores and overall score for a stock.
    Routes to sector-specific scorers for Banks and NBFCs so that inapplicable
    metrics (EBITDA margin for banks, asset turnover for NBFCs) do not distort scores.
    """
    is_bank = sector in _BANK_SECTORS
    is_nbfc = sector in _NBFC_SECTORS
    is_insurance = sector in _INSURANCE_SECTORS
    is_fintech = sector in _FINTECH_SECTORS

    growth = round(_growth_score(metrics), 1)  # universal growth metrics work for all

    if is_bank:
        profitability = round(_bank_profitability_score(metrics), 1)
        cash_flow     = round(_bank_cash_flow_score(metrics), 1)
        balance_sheet = round(_bank_balance_sheet_score(metrics), 1)
        efficiency    = round(_bank_efficiency_score(metrics), 1)
        valuation     = round(_bank_valuation_score(metrics), 1)
    elif is_nbfc or is_insurance:
        profitability = round(_nbfc_profitability_score(metrics), 1)
        cash_flow     = round(_nbfc_cash_flow_score(metrics), 1)
        balance_sheet = round(_nbfc_balance_sheet_score(metrics), 1)
        efficiency    = round(_nbfc_efficiency_score(metrics), 1)
        valuation     = round(_nbfc_valuation_score(metrics), 1)
    elif is_fintech:
        # Profitability/cash-flow/balance-sheet reuse the universal
        # formulas outright — unlike banks, a fintech's EBITDA margin,
        # FCF/PAT and D/E ARE meaningful (spec's own core chain ends in
        # FCF/PAT, not a regulatory capital ratio). Efficiency is the one
        # universal formula that doesn't fit: asset_turnover/inventory_days/
        # receivable_days assume an inventory-holding business, which an
        # asset-light fintech structurally isn't — neutral, same precedent
        # as _bank_efficiency_score/_nbfc_efficiency_score returning 50.0
        # for their own not-applicable metric sets.
        profitability = round(_profitability_score(metrics), 1)
        cash_flow     = round(_cashflow_score(metrics), 1)
        balance_sheet = round(_balance_sheet_score(metrics), 1)
        efficiency    = 50.0
        valuation     = round(_fintech_valuation_score(metrics), 1)
    else:
        profitability = round(_profitability_score(metrics), 1)
        cash_flow     = round(_cashflow_score(metrics), 1)
        balance_sheet = round(_balance_sheet_score(metrics), 1)
        efficiency    = round(_efficiency_score(metrics), 1)
        valuation     = round(_valuation_score(metrics), 1)

    weights = SECTOR_WEIGHTS.get(sector, UNIVERSAL_WEIGHTS)

    overall = recompute_overall(
        {
            "growth": growth, "profitability": profitability, "cash_flow": cash_flow,
            "balance_sheet": balance_sheet, "efficiency": efficiency, "valuation": valuation,
        },
        weights,
    )

    rating = classify_overall_rating

    def val_rating(pe, ev_ebitda, pb) -> str:
        count_exp = sum([
            1 for v in [pe, ev_ebitda, pb]
            if v and v > 0 and v > 30
        ])
        if pe and pe > 50: return "VERY_EXPENSIVE"
        if ev_ebitda and ev_ebitda > 25: return "VERY_EXPENSIVE"
        if count_exp >= 2: return "EXPENSIVE"
        if pe and pe < 12 and ev_ebitda and ev_ebitda < 8: return "CHEAP"
        if pe and pe < 18: return "ATTRACTIVE"
        return "FAIR"

    # Detect universal red flags — sector-aware thresholds
    red_flags = []
    if growth < 30:
        red_flags.append("Poor Revenue & Profit Growth")
    if profitability < 30:
        red_flags.append("Weak Profitability Metrics")
    if not (is_bank or is_nbfc or is_insurance) and cash_flow < 30:
        red_flags.append("Poor Cash Generation")
    if balance_sheet < 30:
        red_flags.append("Balance Sheet Risk")

    de = metrics.get("debt_to_equity")
    if de is not None:
        # Banks: flag above 20x (natural leverage via deposits); NBFCs above 10x; others above 2x
        de_threshold = 20.0 if is_bank else (10.0 if is_nbfc else 2.0)
        if de > de_threshold:
            red_flags.append(f"High Debt-to-Equity ({de:.1f}x)")

    ic = metrics.get("interest_coverage")
    if ic is not None:
        # NBFCs/banks have lower coverage ratios by nature; threshold 1.2x vs 2.0x
        ic_threshold = 1.2 if (is_bank or is_nbfc) else 2.0
        if ic < ic_threshold:
            red_flags.append(f"Weak Interest Coverage ({ic:.1f}x)")

    # FCF/PAT not applicable for banks/NBFCs/insurance
    if not (is_bank or is_nbfc or is_insurance):
        fcf_pat = metrics.get("fcf_to_pat")
        if fcf_pat is not None and fcf_pat < 20:
            red_flags.append("Very Low Cash Conversion")
        roce = metrics.get("roce")
        if roce is not None and roce < 5:
            red_flags.append(f"Very Low ROCE ({roce:.1f}%)")

    # Bank/NBFC specific
    if is_bank or is_nbfc:
        roa = metrics.get("roa")
        if roa is not None and roa < 0.5:
            red_flags.append(f"Very Low ROA ({roa:.2f}%)")
        roe = metrics.get("roe")
        if roe is not None and roe < 8:
            red_flags.append(f"Low ROE ({roe:.1f}%)")

    return {
        "overall": overall,
        "growth": growth,
        # Both components of the blended `growth` score above — see
        # `_growth_score()`'s docstring. `growth_quarterly` is None when too
        # few quarters were on record (`quarterly_growth.py`'s
        # `_MIN_QUARTERS`), in which case `growth` == `growth_annual`.
        "growth_annual": metrics.get("growth_score_annual"),
        "growth_quarterly": metrics.get("growth_score_quarterly"),
        "profitability": profitability,
        "cash_flow": cash_flow,
        "balance_sheet": balance_sheet,
        "efficiency": efficiency,
        "valuation": valuation,
        "overall_rating": rating(overall),
        "valuation_view": val_rating(
            metrics.get("pe_ratio"),
            metrics.get("ev_to_ebitda"),
            metrics.get("pb_ratio"),
        ),
        "sector_matched": False,  # Will be updated by orchestrator
        "red_flags": red_flags,
        "weights": weights,
    }


def compute_data_quality(financial_data: dict, metrics: dict) -> float:
    """Score 0-100 for data quality based on completeness, depth, and freshness."""
    checks = []

    inc = financial_data.get("income", {})
    bal = financial_data.get("balance", {})
    cf = financial_data.get("cash_flow", {})

    def has_data(series: dict, min_years: int = 2) -> bool:
        vals = [v for v in series.values() if v is not None]
        return len(vals) >= min_years

    # Core income statement (weighted higher — 4 pts)
    checks.append(has_data(inc.get("revenue", {}), 3))
    checks.append(has_data(inc.get("net_income", {}), 3))
    checks.append(has_data(inc.get("ebitda", {}), 2))
    checks.append(has_data(inc.get("ebit", {}), 2))

    # Balance sheet
    checks.append(has_data(bal.get("total_assets", {}), 2))
    checks.append(has_data(bal.get("total_equity", {}), 2))
    checks.append(has_data(bal.get("total_debt", {}), 2))

    # Cash flow
    checks.append(has_data(cf.get("operating_cash_flow", {}), 2))
    checks.append(has_data(cf.get("capital_expenditure", {}), 2))
    checks.append(has_data(cf.get("free_cash_flow", {}), 2))

    # Market data
    mkt = financial_data.get("market", {})
    checks.append(mkt.get("market_cap") is not None)
    checks.append(mkt.get("trailing_pe") is not None)
    checks.append(mkt.get("price_to_book") is not None)

    # Key metrics computed
    checks.append(metrics.get("roce") is not None)
    checks.append(metrics.get("roe") is not None)
    checks.append(metrics.get("revenue_cagr_3y") is not None)
    checks.append(metrics.get("debt_to_equity") is not None)

    # Depth bonus: ≥5 years of revenue data
    revenue_vals = [v for v in inc.get("revenue", {}).values() if v is not None]
    checks.append(len(revenue_vals) >= 5)

    score = sum(1 for c in checks if c) / len(checks) * 100

    # Staleness penalty: stale data loses 15 points
    diag = financial_data.get("diagnostics", {})
    if diag.get("is_stale"):
        score = max(0.0, score - 15.0)

    # Missing critical fields penalty: -5 pts each, max -20
    n_missing = len(diag.get("missing_fields", []))
    score = max(0.0, score - min(20.0, n_missing * 5.0))

    return round(score, 1)


def compute_confidence(data_quality: float, metrics: dict, sector_matched: bool) -> float:
    """Compute analysis confidence score 0-100."""
    base = data_quality * 0.6

    # Bonus for validated metrics
    n_metrics = sum(1 for v in [
        metrics.get("roce"), metrics.get("roe"), metrics.get("ebitda_margin"),
        metrics.get("revenue_cagr_3y"), metrics.get("fcf_to_pat"),
        metrics.get("debt_to_equity"),
    ] if v is not None)
    metric_bonus = min(25.0, n_metrics * 4)

    sector_bonus = 5.0 if sector_matched else 0.0
    years = metrics.get("data_years", 0)
    depth_bonus = min(10.0, years * 2.5)

    confidence = base + metric_bonus * 0.25 + sector_bonus + depth_bonus
    return round(min(100.0, confidence), 1)
