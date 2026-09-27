"""Yahoo-only scoring of one company — see the package docstring."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculations.engine import compute_metrics
from app.calculations.scoring import compute_scores
from app.quick_analysis.approx import approximate_refinement
from app.quick_analysis.quarterly_growth import compute_quarterly_growth
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
                industry: str | None = None, basic_industry: str | None = None) -> QuickScore:
    """`financial_data` is `app.data.yfinance_client.fetch_financial_data()`'s
    output (Yahoo, consolidated). Never raises — a company Yahoo can't serve
    comes back with `error` set and empty scores, so a bulk run keeps going."""
    framework_name = classify(sector, industry, basic_industry)
    try:
        if not any(financial_data.get(k) for k in ("income", "balance", "cash_flow")):
            return QuickScore(symbol, framework_name, {}, error=financial_data.get("error") or "no Yahoo statements")
        metrics = compute_metrics(financial_data)
        qg = compute_quarterly_growth(financial_data)
        if qg is not None:
            metrics["quarterly_growth_score"] = qg["score"]
            metrics["quarterly_growth_pct"] = qg["growth_pct"]
        scores = compute_scores(metrics, sector=framework_name)
        refined = approximate_refinement(scores, financial_data, metrics, framework_name)
        return QuickScore(symbol, framework_name, scores, refined, metrics)
    except Exception as e:  # noqa: BLE001 — bulk-run contract: one bad symbol never aborts the batch
        return QuickScore(symbol, framework_name, {}, error=f"{type(e).__name__}: {e}")
