"""Build every stock's convergence read from stored scores (seconds, nothing fetched).
Run after the scores and the Stage Screener have refreshed.

    cd backend && .venv/bin/python -m app.convergence.runner
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.convergence import risk_reward, score, settings
from app.framework import price_stats, store
from app.framework.decisions import values
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import ConvergenceHistory, ConvergenceScore, StageScore, Stock
from app.prices.benchmarks import BROAD_MARKET

_CHUNK = 1000
_NUMBERS = ("close", "sma30", "sma10", "sma_distance_pct", "rs", "rs_change", "high_52w", "resistance", "support", "confidence")
_WINDOWS = {"1M": "1M", "3M": "3M", "6M": "6M", "12M": "1Y"}


def stage_row(c: StageScore | None) -> dict | None:
    if c is None:
        return None
    return {**{k: float(v) if (v := getattr(c, k)) is not None else None for k in _NUMBERS}, "stage": c.stage, "sub_stage": c.sub_stage, "reason": c.reason, "next_stage": c.next_stage,
            "rs_improving": c.rs_improving, "provisional": c.provisional, "weeks_in_stage": c.weeks_in_stage, "detail": c.detail}


def rs_windows(returns: dict, bench: dict) -> dict:
    return {label: (lambda x: round(x, 1) if x is not None else None)(price_stats.excess(returns.get(w), bench.get(w))) for label, w in _WINDOWS.items()}


def read_one(fw_row, stage: dict | None, returns: dict, bench: dict, unread: bool, cfg: dict) -> dict:
    fw = {**values(fw_row), "detail": fw_row.detail or {}}
    swing = (((fw["detail"].get("technical") or {}).get("components") or {}).get("trend_structure") or {}).get("last_swing_low")
    s = stage or {}
    rr = risk_reward.compute(s.get("close"), s.get("stage"), s.get("sma30"), s.get("sma10"), s.get("high_52w"), s.get("resistance"), s.get("support"), swing, cfg)
    windows = rs_windows(returns, bench)
    return {"rr": rr, "windows": windows, **score.build(fw, stage, rr, windows, unread, cfg)}


def _unread(db) -> set[str]:
    return {r[0] for r in db.execute(text("select distinct stock_id from results_calendar where status = 'PENDING' and board_date < current_date"))}


def run(db, log=print) -> dict:
    cfg = settings.load(db)
    method = settings.version(cfg)
    end = price_stats.as_of(db)
    ids = {sid for (sid,) in db.query(Stock.id).filter(Stock.is_active.is_(True))}
    stages = {c.stock_id: stage_row(c) for c in db.query(StageScore)}
    returns, bench = price_stats.universe_returns(end), price_stats.window_returns(price_stats.index_year(BROAD_MARKET, end), end)
    unread = _unread(db)
    now = datetime.now(timezone.utc)
    latest, history, counts = [], [], {}
    for r in store.latest_for_all(db):
        if r.stock_id not in ids:
            continue
        read = read_one(r, stages.get(r.stock_id), returns.get(r.stock_id, {}), bench, r.stock_id in unread, cfg)
        rr, stage = read["rr"], stages.get(r.stock_id) or {}
        latest.append({"stock_id": r.stock_id, "as_of": end, "method_version": method, "combined": read["combined"], "classification": read["classification"], "confidence": read["confidence"],
                       "confidence_label": read["confidence_label"], "risk_reward": rr["ratio"], "upside_pct": rr["upside_pct"], "downside_pct": rr["downside_pct"], "target": rr["target"],
                       "invalidation": rr["invalidation"], "detail": {k: v for k, v in read.items() if k not in ("combined", "classification", "confidence", "confidence_label")}, "computed_at": now})
        history.append({"stock_id": r.stock_id, "as_of": end, "method_version": method, "quality": r.quality, "fundamental": r.fundamental, "technical": r.technical, "relative_strength": r.relative_strength,
                        "valuation": r.valuation, "stage": stage.get("stage"), "sub_stage": stage.get("sub_stage"), "risk_reward": rr["ratio"], "combined": read["combined"], "classification": read["classification"]})
        counts[read["classification"]] = counts.get(read["classification"], 0) + 1
    db.execute(text("delete from convergence_scores"))
    db.execute(text("delete from convergence_history where as_of = :d"), {"d": end})
    for table, rows in ((ConvergenceScore, latest), (ConvergenceHistory, history)):
        for start in range(0, len(rows), _CHUNK):
            db.execute(insert(table).values(rows[start:start + _CHUNK]))
    db.commit()
    return {"stocks": len(latest), "as_of": end.isoformat(), "method": method, "classes": {k: counts.get(k, 0) for k in score.CLASSES}}


def main() -> None:
    db = get_db()
    try:
        print("CONVERGENCE:", run(db), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
