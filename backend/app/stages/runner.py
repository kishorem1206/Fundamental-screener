"""Classify every active stock from stored daily prices (about a minute, nothing fetched).

    cd backend && .venv/bin/python -m app.stages.runner
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.framework import price_stats
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import StageHistory, StageScore
from app.prices.benchmarks import BROAD_MARKET
from app.stages import classify as cl
from app.stages import indicators, settings

_CHUNK = 1000     # rows a statement: a stage_scores row has 34 columns and a statement takes 65,535 values


def _num(x, places: int = 2) -> float | None:
    return None if x is None or not math.isfinite(x) else round(float(x), places)


def _universe(db) -> list[str]:
    return [r[0] for r in db.execute(text("select id from stocks where is_active"))]


def _daily(db, ids: list[str]) -> dict[str, list]:
    out: dict[str, list] = {}
    for sid, *bar in db.execute(text("""select stock_id, bar_date, open, high, low, close, adj_close, volume from price_bars_daily
        where stock_id = any(:ids) order by stock_id, bar_date"""), {"ids": ids}):
        out.setdefault(sid, []).append(bar)
    return out


def _benchmark(db) -> dict[date, float]:
    """The index's last close of each week, keyed by that week's Friday."""
    rows = db.execute(text("select bar_date, close from index_bars_daily where index_name = :n order by bar_date"), {"n": BROAD_MARKET})
    weeks = indicators.to_weeks([(d, c, c, c, c, c, 0) for d, c in rows])
    return {w.end: w.close for w in weeks}


def _is_open_week(week_end: date, as_of: date) -> bool:
    return as_of < week_end


def _opportunity(r: cl.Reading, cfg: dict) -> tuple[bool, bool]:
    """(Stage 2 Opportunity, near a breakout or new high). Nearness ranks a stock
    higher but is not required: the brief says "preferably"."""
    f = r.facts
    if r.stage != 2:
        return False, False
    near = (f["high_distance"] is not None and f["high_distance"] >= -cfg["opportunity_high_pct"])
    ok = (f["above"] and f["slope"] is not None and f["slope"] > 0 and (f["rs_change"] or 0) > 0 and (f["updown"] or 0) >= cfg["updown_bull"] and r.sub_stage != cl.WEAKENING)
    return bool(ok), near


def latest_row(sid: str, s: indicators.Series, readings: list[cl.Reading], as_of: date, cfg: dict, now: datetime) -> dict:
    last, week = readings[-1], s.weeks[-1]
    r, reason = last, last.reason
    if (as_of - week.last_bar).days > cfg["stale_days"]:
        r, reason = cl.Reading(t=last.t, facts=last.facts), f"No trade since {week.last_bar.isoformat()}"
    f = r.facts
    breakout = next((x for x in reversed(readings[-int(cfg["opportunity_breakout_weeks"]):]) if x.event in ("breakout", "breakout_volume")), None)
    opportunity, near = _opportunity(r, cfg)
    near = near or (r.stage == 2 and breakout is not None)
    signal = cl.next_signal(r, cfg) if f else None
    return {"stock_id": sid, "as_of": as_of, "week_end": week.end, "provisional": _is_open_week(week.end, as_of), "stage": r.stage, "sub_stage": r.sub_stage,
            "confidence": r.confidence, "reason": reason, "prev_stage": r.came_from if r.stage else None, "stage_since": s.weeks[r.since].end if r.stage else None,
            "weeks_in_stage": r.age if r.stage else None, "next_stage": signal["to"] if signal and signal["watch"] else None,
            "close": _num(f.get("close", week.close)), "sma30": _num(f.get("sma")), "sma10": _num(f.get("sma10")), "sma_slope_pct": _num(f.get("slope")), "sma_distance_pct": _num(f.get("distance")),
            "rs": _num(f.get("rs")), "rs_change": _num(f.get("rs_change")), "rs_improving": None if f.get("rs_change") is None else f["rs_change"] > 0, "rsi": _num(f.get("rsi")),
            "volume_ratio": _num(f.get("volume_ratio")), "high_52w": _num(f.get("high_52")), "low_52w": _num(f.get("low_52")), "high_distance_pct": _num(f.get("high_distance")),
            "weeks_above_sma": f.get("weeks_above"), "resistance": _num(f.get("resistance")), "support": _num(f.get("support")), "opportunity": opportunity, "near_breakout": near,
            "detail": {"scores": r.scores, "conditions": r.conditions, "signal": signal, "pending": r.pending, "macd": _num(f.get("macd")), "macd_signal": _num(f.get("macd_signal")),
                       "updown": _num(f.get("updown")), "range_pct": _num(f.get("range_pct")), "contraction": _num(f.get("contraction")), "higher_highs": f.get("hh"), "higher_lows": f.get("hl"),
                       "failed_highs": f.get("failed_highs"), "last_breakout": s.weeks[breakout.t].end.isoformat() if breakout else None},
            "computed_at": now}


def history_rows(sid: str, s: indicators.Series, readings: list[cl.Reading], as_of: date) -> list[dict]:
    return [{"stock_id": sid, "week_end": w.end, "open": _num(w.open), "high": _num(w.high), "low": _num(w.low), "close": _num(w.close), "volume": int(w.volume),
             "sma30": _num(s.sma_long[r.t]), "sma10": _num(s.sma_short[r.t]), "rs": _num(s.rs[r.t]), "stage": r.stage, "sub_stage": r.sub_stage, "confidence": r.confidence,
             "event": r.event, "provisional": _is_open_week(w.end, as_of)} for w, r in zip(s.weeks, readings)]


def run(db, log=print) -> dict:
    cfg = settings.load(db)
    as_of = price_stats.as_of(db)
    ids = _universe(db)
    bench, daily = _benchmark(db), _daily(db, ids)
    now = datetime.now(timezone.utc)
    latest, history = [], []
    for sid in ids:
        weeks = indicators.to_weeks(daily.get(sid, []))
        if not weeks:
            continue
        series = indicators.build(weeks, bench, cfg)
        readings = cl.replay(series, cfg)
        latest.append(latest_row(sid, series, readings, as_of, cfg, now))
        history += history_rows(sid, series, readings, as_of)
    db.execute(text("delete from stage_history"))
    db.execute(text("delete from stage_scores"))
    for table, rows in ((StageScore, latest), (StageHistory, history)):
        for start in range(0, len(rows), _CHUNK):
            db.execute(insert(table).values(rows[start:start + _CHUNK]))
    db.commit()
    counts: dict = {}
    for row in latest:
        counts[row["stage"]] = counts.get(row["stage"], 0) + 1
    return {"stocks": len(latest), "as_of": as_of.isoformat(), "weeks": len(history), "stages": {("unclassified" if k is None else f"stage_{k}"): v for k, v in sorted(counts.items(), key=lambda x: str(x[0]))},
            "provisional": bool(latest and latest[0]["provisional"])}


def main() -> None:
    db = get_db()
    try:
        print("STAGES:", run(db, log=lambda m: print(m, flush=True)), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
