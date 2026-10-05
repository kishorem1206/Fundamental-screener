"""Score Refinement — the explicit "fold the new engines' metrics into the
overall score" deliverable. This is the FINAL orchestrator stage (after
`pl_intelligence_scoring`/`balance_sheet_intelligence_scoring`/
`cash_flow_intelligence_scoring` have all already run this analysis) that
re-reads their already-computed results and blends them into the existing
`scoring.py`-produced `profitability`/`balance_sheet`/`cash_flow` category
scores, then recomputes `overall` via `scoring.recompute_overall()` using
the SAME, UNCHANGED weight dict `compute_scores()` already chose
(`UNIVERSAL_WEIGHTS` or a `SECTOR_WEIGHTS` entry — none of the 35 weight
dicts are touched by this module).

Chosen over reordering the pipeline (which would mean computing all three
intelligence engines BEFORE the "scoring" stage, touching 12 already-tuned
stages for no real benefit) — this module is purely additive: it reads
`analysis.scores` (already persisted) plus the three engines' already-
computed result dicts, and overwrites `analysis.scores`/`overall_score` in
place with a refined version.

Every blend is a BOUNDED pull of the base category score toward a 0-100
"proxy score" derived from that engine's own classifications (archetype,
volatility, conversion band, red-flag count) — never an unbounded
override. A single category score can move by at most `_MAX_ADJUSTMENT`
points from this refinement, and every blend's base/proxy/adjustment is
recorded in the returned `refinement` dict for traceability. When an
engine has no usable signal (e.g. no Screener data for that company yet),
its proxy is `None` and the base score is left untouched — never pulled
toward an arbitrary 50.
"""
from __future__ import annotations

from app.calculations.scoring import classify_overall_rating, recompute_overall

_MAX_ADJUSTMENT = 10.0  # points a single category score may move from this refinement
_BLEND_FACTOR = 0.5     # how far the base score moves toward the proxy, before capping


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))

# ── Cash Flow Intelligence proxy ────────────────────────────────────────────

_CF_ARCHETYPE_PROXY = {
    "CASH_COMPOUNDER": 90.0, "CASH_HARVEST": 82.0, "GROWTH_REINVESTMENT": 68.0,
    "ASSET_LIQUIDATION_SUPPORTED": 40.0, "WORKING_CAPITAL_TRAP": 30.0,
    "DEBT_FUNDED_BUSINESS": 15.0, "MIXED": 50.0,
}
_CF_VOLATILITY_PROXY = {
    "STABLE_CFO": 85.0, "DECLINING_CFO": 40.0, "VOLATILE_CFO": 45.0, "NEGATIVE_CFO_PATTERN": 15.0,
}
_CF_CONVERSION_BAND_PROXY = {"<50%": 30.0, "50-100%": 65.0, "~100%": 88.0, ">100%": 78.0}
_CF_RED_FLAG_PENALTY_PER_FLAG = 5.0
_CF_RED_FLAG_PENALTY_CAP = 15.0

# ── Balance Sheet Intelligence proxy ────────────────────────────────────────

_BS_ARCHETYPE_PROXY = {"STRONG": 88.0, "TRANSFORMING": 68.0, "MIDDLE": 48.0, "WEAK": 20.0}
_BS_RED_FLAG_PENALTY_PER_FLAG = 5.0
_BS_RED_FLAG_PENALTY_CAP = 15.0

# ── P&L Intelligence proxy ──────────────────────────────────────────────────
# `master_pl_score` is already a 0-100 figure (weighted M1-M5 blend, see
# `pl_intelligence/scoring.py::compute_master_score()`) — used directly as
# the proxy, no further derivation needed.


def _bounded_blend(base: float, proxy: float | None) -> tuple[float, float]:
    """Pulls `base` toward `proxy` by `_BLEND_FACTOR`, then caps the total
    movement at +/- `_MAX_ADJUSTMENT`. Returns (refined_score, adjustment)."""
    if proxy is None:
        return base, 0.0
    raw_adjustment = (proxy - base) * _BLEND_FACTOR
    adjustment = max(-_MAX_ADJUSTMENT, min(_MAX_ADJUSTMENT, raw_adjustment))
    return _clamp(base + adjustment), round(adjustment, 2)


def _derive_cashflow_proxy_score(cfi_result: dict) -> float | None:
    """0-100 proxy from conversion band + archetype + volatility (weighted
    0.35/0.40/0.25), minus a red-flag penalty (5 pts/triggered flag, capped
    at 15). `None` when none of these three signals are available at all."""
    if not cfi_result:
        return None
    components: list[tuple[float, float]] = []
    band = ((cfi_result.get("conversion") or {}).get("latest") or {}).get("band")
    if band in _CF_CONVERSION_BAND_PROXY:
        components.append((_CF_CONVERSION_BAND_PROXY[band], 0.35))
    archetype = (cfi_result.get("archetype") or {}).get("classification")
    if archetype in _CF_ARCHETYPE_PROXY:
        components.append((_CF_ARCHETYPE_PROXY[archetype], 0.40))
    volatility = (cfi_result.get("volatility") or {}).get("classification")
    if volatility in _CF_VOLATILITY_PROXY:
        components.append((_CF_VOLATILITY_PROXY[volatility], 0.25))
    if not components:
        return None
    total_w = sum(w for _, w in components)
    proxy = sum(s * w for s, w in components) / total_w
    triggered = sum(1 for f in (cfi_result.get("risk_flags") or []) if f.get("status") == "TRIGGERED")
    proxy -= min(_CF_RED_FLAG_PENALTY_CAP, triggered * _CF_RED_FLAG_PENALTY_PER_FLAG)
    return max(0.0, min(100.0, proxy))


def refine_cashflow_score(base_score: float, cfi_result: dict | None) -> dict:
    """Blends `cash_flow_intelligence`'s conversion/archetype/volatility/
    red-flag signals into the base `cash_flow` category score from
    `scoring.py::_cashflow_score()` (which only sees the coarser
    cfo_to_pat/fcf_to_pat/fcf_margin aggregate metrics)."""
    proxy = _derive_cashflow_proxy_score(cfi_result or {})
    refined, adjustment = _bounded_blend(base_score, proxy)
    return {
        "base_score": base_score, "proxy_score": round(proxy, 2) if proxy is not None else None,
        "adjustment": adjustment, "refined_score": round(refined, 1),
        "source": "cash_flow_intelligence" if proxy is not None else None,
    }


def _derive_balance_sheet_proxy_score(bsi_result: dict) -> float | None:
    """0-100 proxy from the archetype classification, minus a red-flag
    penalty. `NOT_APPLICABLE` (banks — see `balance_sheet_intelligence`'s
    own sector-routing) yields no proxy, leaving the base score untouched
    — appropriate since `compute_scores()` already routes banks to their
    own `_bank_balance_sheet_score()` with bank-specific D/E thresholds."""
    if not bsi_result:
        return None
    archetype = (bsi_result.get("archetype") or {}).get("classification")
    proxy = _BS_ARCHETYPE_PROXY.get(archetype)
    if proxy is None:
        return None
    triggered = sum(1 for f in (bsi_result.get("risk_flags") or []) if f.get("status") == "TRIGGERED")
    proxy -= min(_BS_RED_FLAG_PENALTY_CAP, triggered * _BS_RED_FLAG_PENALTY_PER_FLAG)
    return max(0.0, min(100.0, proxy))


def refine_balance_sheet_score(base_score: float, bsi_result: dict | None) -> dict:
    """Blends `balance_sheet_intelligence`'s archetype/red-flag signals
    into the base `balance_sheet` category score from
    `scoring.py::_balance_sheet_score()` (which only sees D/E, interest
    coverage, and current ratio)."""
    proxy = _derive_balance_sheet_proxy_score(bsi_result or {})
    refined, adjustment = _bounded_blend(base_score, proxy)
    return {
        "base_score": base_score, "proxy_score": round(proxy, 2) if proxy is not None else None,
        "adjustment": adjustment, "refined_score": round(refined, 1),
        "source": "balance_sheet_intelligence" if proxy is not None else None,
    }


def refine_profitability_score(base_score: float, pli_result: dict | None) -> dict:
    """Blends `pl_intelligence`'s Master P&L Score (`master_pl_score`,
    already 0-100 — a weighted blend of sector-percentile margin, margin
    headroom, doubling velocity, earnings quality, and cost-structure
    resilience) into the base `profitability` category score from
    `scoring.py::_profitability_score()` (which only sees EBITDA margin,
    PAT margin, ROE, ROCE)."""
    master_pl_score = ((pli_result or {}).get("score") or {}).get("master_pl_score")
    refined, adjustment = _bounded_blend(base_score, master_pl_score)
    return {
        "base_score": base_score, "proxy_score": master_pl_score,
        "adjustment": adjustment, "refined_score": round(refined, 1),
        "source": "pl_intelligence" if master_pl_score is not None else None,
    }


def apply_score_refinement(scores: dict, pli_result: dict | None = None,
                            bsi_result: dict | None = None, cfi_result: dict | None = None,
                            governance_result: dict | None = None) -> dict:
    """Returns a NEW scores dict (never mutates `scores` in place) with
    `profitability`/`balance_sheet`/`cash_flow` replaced by their refined
    values and `overall` recomputed from the exact weight dict `scores`
    already carries (`scores["weights"]`, set by `compute_scores()` — the
    same `UNIVERSAL_WEIGHTS`/`SECTOR_WEIGHTS` entry, untouched). Returns
    `scores` unchanged if it carries no `weights` (e.g. the "scoring"
    stage itself failed upstream this run) — recomputing `overall` without
    the real weight dict would silently fall back to a wrong default.

    `governance_result` (see `governance_scoring.py::compute_governance_penalty()`)
    is applied as a direct penalty on `overall`, after the category blends
    below — it has no "base score" of its own to blend toward, unlike the
    three intelligence engines."""
    weights = scores.get("weights")
    if not weights:
        return scores

    profitability_refinement = refine_profitability_score(scores.get("profitability", 50.0), pli_result)
    balance_sheet_refinement = refine_balance_sheet_score(scores.get("balance_sheet", 50.0), bsi_result)
    cash_flow_refinement = refine_cashflow_score(scores.get("cash_flow", 50.0), cfi_result)

    refined_scores = dict(scores)
    refined_scores["profitability"] = profitability_refinement["refined_score"]
    refined_scores["balance_sheet"] = balance_sheet_refinement["refined_score"]
    refined_scores["cash_flow"] = cash_flow_refinement["refined_score"]
    overall = recompute_overall(
        {
            "growth": refined_scores.get("growth", 50.0),
            "profitability": refined_scores["profitability"],
            "cash_flow": refined_scores["cash_flow"],
            "balance_sheet": refined_scores["balance_sheet"],
            "efficiency": refined_scores.get("efficiency", 50.0),
            "valuation": refined_scores.get("valuation", 50.0),
        },
        weights,
    )
    governance_penalty = (governance_result or {}).get("penalty") or 0.0
    if governance_penalty:
        overall = _clamp(overall - governance_penalty)
    refined_scores["overall"] = overall
    refined_scores["overall_rating"] = classify_overall_rating(overall)
    refined_scores["refinement"] = {
        "profitability": profitability_refinement,
        "balance_sheet": balance_sheet_refinement,
        "cash_flow": cash_flow_refinement,
        "governance": governance_result,
        "pre_refinement_overall": scores.get("overall"),
    }
    if governance_result and governance_result.get("flags"):
        refined_scores["red_flags"] = [
            *(scores.get("red_flags") or []),
            *(f"{f['severity'].title()} — {f['description']}" for f in governance_result["flags"]),
        ]
    return refined_scores
