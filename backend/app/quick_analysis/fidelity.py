"""How close is the Yahoo-only quick score to the full pipeline's score?

For every company that has a completed full analysis, replay the exact Yahoo
data that analysis used (`FundamentalAnalysis.financial_data`) through the
quick scorer, then compare against the full result at two points so the error
can be attributed:

  full_base   = scores right after `compute_scores()` — i.e. WITH Screener
                metric overrides but BEFORE intelligence-engine refinement
  full_final  = scores after refinement (what the report shows)

  quick vs full_base  -> error caused by missing Screener overrides only
  full_base vs final  -> error caused by missing refinement only
  quick vs full_final -> total error

Using stored Yahoo data (not a live fetch) isolates input-source differences
from price/market movement. Overall is compared after re-deriving the full
result's overall under the CURRENT weight tables, since older analyses used
the pre-2026-09-23 weights.

    cd backend && .venv/bin/python -m app.quick_analysis.fidelity
"""
from __future__ import annotations

import statistics

from app.calculations.scoring import SECTOR_WEIGHTS, UNIVERSAL_WEIGHTS, classify_overall_rating, recompute_overall
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import CompanyScore, FundamentalAnalysis, Stock
from app.quick_analysis.scorer import quick_score

CATEGORIES = ("growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation")


def _spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for rank, i in enumerate(order):
            r[i] = float(rank)
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def collect(db) -> list[dict]:
    out = []
    for cs, stock in db.query(CompanyScore, Stock).join(Stock, Stock.id == CompanyScore.stock_id).all():
        analysis = db.get(FundamentalAnalysis, cs.analysis_id)
        if analysis is None or not analysis.scores or not analysis.financial_data:
            continue
        full = analysis.scores
        refinement = full.get("refinement", {})
        quick = quick_score(stock.symbol, analysis.financial_data, stock.sector, stock.industry, stock.basic_industry,
                            db=db, company_id=stock.id)
        if quick.error:
            out.append({"symbol": stock.symbol, "error": quick.error})
            continue
        base = {c: refinement.get(c, {}).get("base_score", full.get(c)) for c in CATEGORIES}
        final = {c: full.get(c) for c in CATEGORIES}
        weights = SECTOR_WEIGHTS.get(quick.sector_framework, UNIVERSAL_WEIGHTS)
        out.append({
            "symbol": stock.symbol,
            "framework": quick.sector_framework,
            "framework_match": quick.sector_framework == (analysis.sector_analysis or {}).get("sector_name"),
            "quick": {c: quick.scores[c] for c in CATEGORIES},
            "refined": {c: quick.refined[c] for c in CATEGORIES},
            "weights": weights,
            "prof_adjustment": refinement.get("profitability", {}).get("adjustment", 0.0),
            "bs_adj_full": refinement.get("balance_sheet", {}).get("adjustment", 0.0),
            "cf_adj_full": refinement.get("cash_flow", {}).get("adjustment", 0.0),
            "bs_adj_approx": quick.refined["refinement"]["balance_sheet"]["adjustment"],
            "cf_adj_approx": quick.refined["refinement"]["cash_flow"]["adjustment"],
            "base": base, "final": final,
            "quick_overall": quick.scores["overall"],
            "refined_overall": quick.refined["overall"],
            "full_overall": recompute_overall(final, weights),
        })
    return out


def _variant_overalls(ok: list[dict]) -> dict[str, list[float]]:
    """raw / approx-refined / approx-refined + leave-one-out profitability
    shift. The shift for company i is the mean full-pipeline profitability
    adjustment over the OTHER companies, so no company is scored with a
    constant that was fitted on itself."""
    shifted = []
    for i, r in enumerate(ok):
        others = [o["prof_adjustment"] for j, o in enumerate(ok) if j != i]
        shift = statistics.mean(others)
        cats = dict(r["refined"])
        cats["profitability"] = max(0.0, min(100.0, cats["profitability"] + shift))
        shifted.append(recompute_overall(cats, r["weights"]))
    return {
        "raw (no refinement)": [r["quick_overall"] for r in ok],
        "approx refinement (BS+CF)": [r["refined_overall"] for r in ok],
        "approx + profitability shift (LOO)": shifted,
    }


def report(rows: list[dict]) -> None:
    ok = [r for r in rows if "error" not in r]
    for r in rows:
        if "error" in r:
            print(f"  ! {r['symbol']}: {r['error']}")
    print(f"\ncompanies compared: {len(ok)}   sector-framework routing identical: "
          f"{sum(r['framework_match'] for r in ok)}/{len(ok)}\n")

    print("Per-category error vs the full pipeline's FINAL score (raw / approx-refined):")
    print(f"{'category':14} {'MAE raw':>8} {'MAE approx':>11} {'bias raw':>9} {'bias approx':>12} {'within 10 (approx)':>19}")
    for c in CATEGORIES:
        raw = [r["quick"][c] - r["final"][c] for r in ok if r["final"][c] is not None]
        app = [r["refined"][c] - r["final"][c] for r in ok if r["final"][c] is not None]
        print(f"{c:14} {statistics.mean(abs(d) for d in raw):8.1f} {statistics.mean(abs(d) for d in app):11.1f} "
              f"{statistics.mean(raw):+9.1f} {statistics.mean(app):+12.1f} {sum(abs(d) <= 10 for d in app):>15}/{len(app)}")

    f = [r["full_overall"] for r in ok]
    print(f"\n{'overall vs full':38} {'MAE':>5} {'bias':>6} {'max':>5} {'<=5':>5} {'rank rho':>9} {'band =':>7} {'top-6':>6}")
    k = max(3, len(ok) // 3)
    top_f = {r["symbol"] for r in sorted(ok, key=lambda r: -r["full_overall"])[:k]}
    for name, q in _variant_overalls(ok).items():
        d = [a - b for a, b in zip(q, f)]
        top_q = {r["symbol"] for r, _ in sorted(zip(ok, q), key=lambda t: -t[1])[:k]}
        band = sum(classify_overall_rating(a) == classify_overall_rating(b) for a, b in zip(q, f))
        print(f"{name:38} {statistics.mean(abs(x) for x in d):5.1f} {statistics.mean(d):+6.1f} {max(abs(x) for x in d):5.1f} "
              f"{sum(abs(x) <= 5 for x in d):>3}/{len(ok)} {_spearman(q, f):9.2f} {band:>4}/{len(ok)} {len(top_q & top_f):>4}/{k}")

    print(f"\n{'symbol':11} {'framework':24} {'raw':>6} {'approx':>7} {'full':>6} {'err':>6}   BS adj (approx/full)  CF adj (approx/full)")
    for r in sorted(ok, key=lambda r: -abs(r["refined_overall"] - r["full_overall"])):
        print(f"{r['symbol']:11} {r['framework']:24} {r['quick_overall']:6.1f} {r['refined_overall']:7.1f} {r['full_overall']:6.1f} "
              f"{r['refined_overall'] - r['full_overall']:+6.1f}   {r['bs_adj_approx']:+6.1f} /{r['bs_adj_full']:+6.1f}      "
              f"{r['cf_adj_approx']:+6.1f} /{r['cf_adj_full']:+6.1f}")


if __name__ == "__main__":
    session = get_db()
    try:
        report(collect(session))
    finally:
        session.close()
