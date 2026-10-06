"""Brings stored full analyses in line with two 2026-10-06 changes, without
re-running them:

  1. ROCE everywhere is Screener's own published figure
     (app/calculations/screener_roce.py) — the stored metrics' ROCE value,
     series, trend and averages are replaced.
  2. Profitability is direction-aware (scoring.py::profitability_direction) —
     the stored profitability score moves by the difference between the new
     score on the corrected metrics and the old level-only score, and the
     overall score moves by that difference times the profitability weight.

    cd backend && .venv/bin/python -m scripts.backfill_roce_and_direction
"""
from app.calculations import screener_roce
from app.calculations.scoring import classify_overall_rating, compute_scores
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis, Stock
from app.sectors.registry import get_framework

_TRENDS = ("roce_trend", "roe_trend", "roa_trend", "ebitda_margin_trend", "pat_margin_trend")


def main() -> None:
    db = get_db()
    try:
        done: set[str] = set()
        for a in (db.query(FundamentalAnalysis).filter(FundamentalAnalysis.status == "COMPLETED")
                  .order_by(FundamentalAnalysis.created_at.desc()).all()):
            if a.stock_id in done or not a.scores or not a.metrics:
                continue
            done.add(a.stock_id)
            if (a.scores or {}).get("profitability_direction") is not None:
                continue  # already brought in line
            stock = db.get(Stock, a.stock_id)
            sector = get_framework(stock.sector or "", industry=stock.industry or "", basic_industry=stock.basic_industry or "").sector_name
            old = dict(a.metrics)
            new = dict(a.metrics)
            sources = dict(new.get("_metric_sources") or {})
            from_screener = screener_roce.apply_to_metrics(new, sources, db, a.stock_id)
            new["_metric_sources"] = sources
            level_only = compute_scores({k: v for k, v in old.items() if k not in _TRENDS}, sector=sector)["profitability"]
            fresh = compute_scores(dict(new), sector=sector)
            delta = fresh["profitability"] - level_only
            scores = dict(a.scores)
            before = scores.get("profitability")
            if before is not None:
                after = max(0.0, min(100.0, before + delta))
                weight = (scores.get("weights") or {}).get("profitability", 0)
                scores["profitability"] = round(after, 1)
                if scores.get("overall") is not None:
                    scores["overall"] = round(max(0.0, min(100.0, scores["overall"] + weight * (after - before))), 1)
                    scores["overall_rating"] = classify_overall_rating(scores["overall"])
                    a.overall_score = scores["overall"]
            scores["profitability_direction"] = fresh["profitability_direction"]
            a.metrics, a.scores = new, scores
            db.commit()
            try:
                from app.services.company_scores import upsert_company_score
                upsert_company_score(db, a)
                db.commit()
            except Exception:
                db.rollback()
            print(f"  {stock.symbol:<12} ROCE {old.get('roce')} -> {new.get('roce')} ({'Screener' if from_screener else 'unchanged'})  "
                  f"profitability {before} -> {scores.get('profitability')}  overall -> {scores.get('overall')}  "
                  f"direction {fresh['profitability_direction']['adjustment']}")
        print(f"{len(done)} companies")
    finally:
        db.close()


if __name__ == "__main__":
    main()
