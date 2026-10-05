"""Yahoo-only scoring of one company — see the package docstring."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculations.engine import compute_metrics
from app.calculations.scoring import compute_scores
from app.quick_analysis.approx import approximate_refinement
from app.quick_analysis.quarterly_growth import compute_quarterly_growth
from app.quick_analysis.screener_quarterly_fallback import compute_quarterly_growth_from_screener
from app.sectors.registry import get_framework

SCORE_KEYS = ("growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation", "overall")


@dataclass
class QuickScore:
    symbol: str
    sector_framework: str          # framework.sector_name — decides weights + scoring family
    scores: dict                   # compute_scores() output — RAW Yahoo-only scores, before any refinement
    refined: dict = field(default_factory=dict)  # approximate_refinement() output — the recommended quick score
    metrics: dict = field(repr=False, default_factory=dict)
    error: str | None = None


def classify(sector: str | None, industry: str | None, basic_industry: str | None) -> str:
    """Framework name the FULL pipeline would route this company to — the
    identical call orchestrator.py makes (sector_analysis stage)."""
    return get_framework(sector or "", industry=industry or "", basic_industry=basic_industry or "").sector_name


def quick_score(symbol: str, financial_data: dict, sector: str | None,
                industry: str | None = None, basic_industry: str | None = None,
                db=None, company_id: str | None = None, screener_pacer=None) -> QuickScore:
    """`financial_data` is `app.data.yfinance_client.fetch_financial_data()`'s
    output (Yahoo, consolidated). Never raises — a company Yahoo can't serve
    comes back with `error` set and empty scores, so a bulk run keeps going.

    `db`/`company_id` (both optional — every current caller passes them,
    but a bare `financial_data`-only call, e.g. in a test, still works,
    just without the Screener quarterly fallback below) enable the
    DB-persisted Screener fallback: reads `fa_metric_data_points` first,
    only fetches Screener live on a genuine miss, so a repeat scan of the
    same company never re-fetches (see screener_quarterly_fallback.py).

    `screener_pacer` (optional — `runner.py`'s bulk run passes its own
    shared `_Pacer` instance) paces the Screener fallback calls below
    across concurrent worker threads. Real 429s confirmed live 2026-09-29:
    a `--force` full rescore calls these fallbacks for nearly every
    company, and with no shared pacing 4 worker threads hit Screener
    simultaneously — the exact failure mode `runner.py`'s own Yahoo
    `_Pacer` already exists to prevent, just against a different upstream
    this one hadn't been extended to cover yet."""
    framework_name = classify(sector, industry, basic_industry)
    try:
        if not any(financial_data.get(k) for k in ("income", "balance", "cash_flow")):
            return QuickScore(symbol, framework_name, {}, error=financial_data.get("error") or "no Yahoo statements")
        metrics = compute_metrics(financial_data)
        if db is not None and company_id is not None:
            # Screener first, Yahoo as fallback — the full analysis's own override
            # step, reading the Screener rows already in the ledger (see
            # screener_annual.py; the runner refreshes them before scoring).
            from app.quick_analysis.screener_annual import apply as apply_screener_first
            apply_screener_first(metrics, db, company_id, framework_name)
        qg = compute_quarterly_growth(financial_data)
        if qg is None and db is not None and company_id is not None:
            # Yahoo had too few usable quarters (or the WeWork-shaped gap —
            # see quarterly_growth.py's docstring). Screener consolidated
            # quarterly_results() as a fallback (2026-09-28, explicit user
            # request) — CONSOLIDATED only, no standalone attempt; if
            # Screener doesn't have it either, `qg` just stays None and
            # `_growth_score()` falls back to the annual score alone, same
            # as if this fallback didn't exist.
            if screener_pacer is not None:
                screener_pacer.wait_turn()
            qg = compute_quarterly_growth_from_screener(db, company_id, symbol)
        if qg is not None:
            metrics["quarterly_growth_score"] = qg["score"]
            metrics["quarterly_growth_pct"] = qg["growth_pct"]
        scores = compute_scores(metrics, sector=framework_name)
        refined = approximate_refinement(scores, financial_data, metrics, framework_name, db=db,
                                         company_id=company_id, screener_pacer=screener_pacer)
        return QuickScore(symbol, framework_name, scores, refined, metrics)
    except Exception as e:  # noqa: BLE001 — bulk-run contract: one bad symbol never aborts the batch
        return QuickScore(symbol, framework_name, {}, error=f"{type(e).__name__}: {e}")
