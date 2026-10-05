"""Yahoo-derived approximation of the full pipeline's score-refinement stage.

The full pipeline nudges profitability / balance sheet / cash flow by up to
+/-10 points using three intelligence engines that read the Screener ledger
(see app/calculations/score_refinement.py). This module reproduces the same
step from Yahoo statements, reusing the SAME formulas — `_bounded_blend`, the
archetype classifiers and the proxy tables are imported, not copied — and
only substituting Yahoo-derived INPUTS:

  balance sheet  archetype (STRONG/MIDDLE/WEAK) from cash/total-assets and
                 debt/equity, exactly as the full engine does. Two honest
                 limits: Yahoo has no long-term-investments line, so
                 cash+investments is understated (STRONG is under-detected);
                 and the engine's own red-flag penalty is unknowable here.
  cash flow      conversion band (CFO / EBITDA), CFO volatility, and archetype
                 from Yahoo CFO/FCF/financing series (4-5 fiscal years vs the
                 ledger's ~12).
  profitability  the P&L master score itself (sector-peer margin percentiles,
                 doubling velocity, cost-structure resilience) needs Screener
                 segment/structure data this module still can't derive from
                 Yahoo alone. But ONE of its five inputs — earnings quality
                 (EQI, "how much of profit is genuinely core") — is
                 derivable whenever the Screener ledger has other_income/PBT
                 on record (see other_income_flag.py), often already true as
                 a side effect of the quarterly-growth Screener fallback
                 (screener_quarterly_fallback.py) this package also calls.
                 2026-09-28, explicit user request, surfaced by I S T
                 Limited: Other Income was 78-88% of PBT across its last 3
                 quarters, something pat_margin/ROE/ROCE never flagged.
  governance     promoter pledge / promoter-holding-decline penalty applied
                 directly to `overall` (see governance_scoring.py) — reads
                 the `governance_events` the FULL pipeline's "shareholding"
                 ingestion stage already wrote (NSE promoter/pledge data);
                 this module never scrapes it itself. `None` — no penalty —
                 for a company that hasn't been through a full analysis yet.

Financial institutions get no balance-sheet or profitability refinement,
mirroring the full engine (archetype is NOT_APPLICABLE for banks/NBFCs;
"other income" for a bank is largely fee/commission income, a normal core
revenue line, not the same red flag it is for a non-financial company).
"""
from __future__ import annotations

from app.calculations.balance_sheet_intelligence import sector_routing
from app.calculations.balance_sheet_intelligence.archetype import classify_archetype
from app.calculations.cash_flow_intelligence.archetype import classify_cash_flow_archetype
from app.calculations.cash_flow_intelligence.conversion import cfo_operating_profit_ratio
from app.calculations.cash_flow_intelligence.volatility import classify_cfo_volatility
from app.calculations.governance_scoring import clamp_score, compute_governance_penalty
from app.calculations.score_refinement import (
    _BS_ARCHETYPE_PROXY, _bounded_blend, _derive_cashflow_proxy_score,
)
from app.calculations.scoring import classify_overall_rating, recompute_overall
from app.quick_analysis.other_income_flag import compute_other_income_dependency

# The engine's red-flag penalty (5 pts per triggered flag) can't be observed
# from Yahoo. Across the 18 analysed companies the balance-sheet proxy sat at
# 43-48 for the MIDDLE archetype, i.e. 0-1 flags; 3.0 is the observed mean.
ASSUMED_BS_FLAG_PENALTY = 3.0

# Same idea for cash flow: the engine subtracts 5 points per TRIGGERED
# forensic/red flag (capped at 15), which needs the Screener ledger. Sweeping
# 0-4 assumed flags over the 18 analysed companies, cash-flow error fell
# steadily from 6.8 (0 flags) to 5.1 (2 flags) to 4.6 (4 flags); 2 is used
# deliberately below the best-fitting value, since it is a single constant
# fitted on a small sample. Recalibrate when more companies are analysed.
ASSUMED_CF_TRIGGERED_FLAGS = 2


def _latest(series: dict | None) -> float | None:
    vals = [(k, v) for k, v in (series or {}).items() if v is not None]
    return sorted(vals)[-1][1] if vals else None


def _latest_balance(financial_data: dict, key: str) -> float | None:
    return _latest((financial_data.get("balance") or {}).get(key))


def balance_sheet_proxy(financial_data: dict, metrics: dict, framework_name: str) -> tuple[float | None, str | None]:
    if sector_routing.is_financial_institution(framework_name):
        return None, None
    cash, assets = _latest_balance(financial_data, "cash"), _latest_balance(financial_data, "total_assets")
    cash_pct = (cash / assets * 100) if cash is not None and assets else None
    archetype = classify_archetype(cash_pct, metrics.get("debt_to_equity"), None, None, None, None)["classification"]
    proxy = _BS_ARCHETYPE_PROXY.get(archetype)
    return (max(0.0, proxy - ASSUMED_BS_FLAG_PENALTY) if proxy is not None else None), archetype


def cash_flow_proxy(financial_data: dict, metrics: dict, framework_name: str) -> tuple[float | None, str | None]:
    if sector_routing.is_financial_institution(framework_name):
        return None, None  # full engine's conversion/archetype signals are for operating businesses
    cfo_series = {k: v for k, v in (metrics.get("cfo_series") or {}).items() if v is not None}
    ebitda = _latest(metrics.get("ebitda_series"))
    conversion = cfo_operating_profit_ratio(_latest(cfo_series), ebitda)
    volatility = classify_cfo_volatility(cfo_series)

    fcf = [v for v in (metrics.get("fcf_series") or {}).values() if v is not None]
    fcf_quality = "CONSISTENT_POSITIVE_FCF" if fcf and all(v > 0 for v in fcf) else None
    capex = _latest((financial_data.get("cash_flow") or {}).get("capital_expenditure"))
    cfo = _latest(cfo_series)
    capex_to_cfo = abs(capex) / cfo * 100 if capex is not None and cfo and cfo > 0 else None
    cff = _latest((financial_data.get("cash_flow") or {}).get("financing_cash_flow"))
    debt_class = "NET_BORROWING" if cff is not None and cff > 0 else None

    archetype = classify_cash_flow_archetype(
        volatility.get("classification"), fcf_quality, conversion.get("ratio_pct"), capex_to_cfo,
        debt_class, False, False,
    )["classification"]
    proxy = _derive_cashflow_proxy_score({
        "conversion": {"latest": {"band": conversion.get("band")}},
        "archetype": {"classification": archetype},
        "volatility": {"classification": volatility.get("classification")},
        "risk_flags": [{"status": "TRIGGERED"}] * ASSUMED_CF_TRIGGERED_FLAGS,
    })
    return proxy, archetype


def profitability_proxy(db, company_id: str | None, symbol: str | None, framework_name: str,
                        screener_pacer=None) -> tuple[float | None, dict | None]:
    """Earnings-quality-only proxy (see module docstring) — `None` when
    `db`/`company_id`/`symbol` weren't passed in, the company is a
    financial institution, or neither the ledger nor a fresh Screener
    ingest has other_income/PBT for it. Second return value is the raw
    dependency dict (for `red_flags`/`refinement` detail), not an
    "archetype" string like the other two proxies — there's no archetype
    concept here. `screener_pacer` — see scorer.py's docstring — paces the
    ingest-on-miss fallback across concurrent worker threads."""
    if db is None or company_id is None or not symbol or sector_routing.is_financial_institution(framework_name):
        return None, None
    dependency = compute_other_income_dependency(db, company_id, symbol, screener_pacer=screener_pacer)
    if dependency is None:
        return None, None
    return dependency["proxy_score"], dependency


def approximate_refinement(scores: dict, financial_data: dict, metrics: dict, framework_name: str,
                           db=None, company_id: str | None = None, screener_pacer=None) -> dict:
    """Returns a NEW scores dict shaped like the full pipeline's refined
    scores, with `refinement` recording base/proxy/adjustment per category.
    `db`/`company_id` are optional (every current caller passes them) —
    enables the profitability earnings-quality proxy; omit for a bare
    scores-only call and profitability is simply left unrefined, as before
    this feature existed."""
    refined = dict(scores)
    detail: dict[str, dict] = {}
    other_income_dependency = None
    for category, (proxy, extra) in (
        ("balance_sheet", balance_sheet_proxy(financial_data, metrics, framework_name)),
        ("cash_flow", cash_flow_proxy(financial_data, metrics, framework_name)),
        ("profitability", profitability_proxy(db, company_id, financial_data.get("symbol"), framework_name,
                                              screener_pacer=screener_pacer)),
    ):
        if category == "profitability":
            other_income_dependency = extra
            archetype = None
        else:
            archetype = extra
        base = scores[category]
        value, adjustment = _bounded_blend(base, proxy)
        refined[category] = round(value, 1)
        detail[category] = {"base_score": base, "proxy_score": None if proxy is None else round(proxy, 2),
                            "adjustment": adjustment, "archetype": archetype}
    if other_income_dependency and other_income_dependency["flagged"]:
        detail["profitability"]["other_income_dependency"] = other_income_dependency
        refined["red_flags"] = [
            *(scores.get("red_flags") or []),
            f"High Other-Income Dependency ({round(other_income_dependency['ratio'] * 100)}% of "
            f"{other_income_dependency['period_type']} PBT, {other_income_dependency['period']})",
        ]
    overall = recompute_overall(
        {c: refined[c] for c in ("growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation")},
        scores["weights"],
    )
    # Promoter-governance penalty (2026-09-28) — DB-read-only, no extra
    # scraping: reads whatever `governance_events` the FULL pipeline's own
    # "shareholding" ingestion already wrote for this company (NSE
    # promoter/pledge data, unrelated to the Yahoo/Screener sources this
    # module otherwise reads). `None` — no penalty applied — for a company
    # that's never been through a full analysis, same graceful-absence
    # contract as the other two proxies above.
    governance_result = compute_governance_penalty(db, company_id) if db is not None and company_id else None
    governance_penalty = (governance_result or {}).get("penalty") or 0.0
    if governance_penalty:
        overall = clamp_score(overall - governance_penalty)
    if governance_result and governance_result.get("flags"):
        refined["red_flags"] = [
            *(refined.get("red_flags") or []),
            *(f"{f['severity'].title()} — {f['description']}" for f in governance_result["flags"]),
        ]
    detail["governance"] = governance_result
    refined["overall"] = overall
    refined["overall_rating"] = classify_overall_rating(overall)
    refined["refinement"] = detail
    return refined
