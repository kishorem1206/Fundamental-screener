"""Weinstein stage screener for every stock with prices (app/stages/). Reads stored results;
nothing is recomputed on a request, and nothing here feeds another score."""
import csv
import io
import threading
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import StageHistory, StageScore, StageWatch, Stock
from app.stages import classify, runner, settings

router = APIRouter(prefix="/api/stages")

_NUMBERS = ("close", "sma30", "sma10", "sma_slope_pct", "sma_distance_pct", "rs", "rs_change", "rsi", "volume_ratio", "high_52w", "low_52w", "high_distance_pct", "resistance", "support", "confidence")
_SORT = (*_NUMBERS, "stage", "weeks_in_stage", "weeks_above_sma")
_TEXT_SORT = {"symbol": Stock.symbol, "company_name": Stock.company_name, "sector": Stock.sector}
_PRESETS = ("opportunities", "new_stage_2", "stage_2_rs", "transition_watch")

_recalc = threading.Lock()


def _num(v) -> float | None:
    return float(v) if v is not None else None


def _filtered(db, q, sector, stage, sub_stage, min_confidence, min_rs, preset, watchlist):
    query = db.query(StageScore, Stock).join(Stock, Stock.id == StageScore.stock_id)
    if q and q.strip():
        needle = f"%{q.strip()}%"
        query = query.filter(or_(Stock.symbol.ilike(needle), Stock.company_name.ilike(needle)))
    if sector:
        query = query.filter(Stock.sector == sector)
    if stage is not None:
        query = query.filter(StageScore.stage.is_(None) if stage == 0 else StageScore.stage == stage)
    if sub_stage:
        query = query.filter(StageScore.sub_stage == sub_stage)
    if min_confidence:
        query = query.filter(StageScore.confidence >= min_confidence)
    if min_rs is not None:
        query = query.filter(StageScore.rs >= min_rs)
    if watchlist:
        query = query.join(StageWatch, StageWatch.stock_id == StageScore.stock_id)
    if preset == "opportunities":
        query = query.filter(StageScore.opportunity.is_(True))
    elif preset == "new_stage_2":
        query = query.filter(StageScore.stage == 2, StageScore.prev_stage.isnot(None), StageScore.weeks_in_stage <= settings.load(db)["new_weeks"])
    elif preset == "stage_2_rs":
        query = query.filter(StageScore.stage == 2, StageScore.rs_improving.is_(True))
    elif preset == "transition_watch":
        query = query.filter(StageScore.next_stage.isnot(None))
    return query


def _ordered(query, sort_by, order, preset):
    column = _TEXT_SORT.get(sort_by) or getattr(StageScore, sort_by if sort_by in _SORT else "confidence")
    primary = (column.asc() if order == "asc" else column.desc()).nullslast()
    # near a high first: across 2,613 stocks those beat the market far more often (see the methodology note)
    return query.order_by(StageScore.near_breakout.desc(), primary, Stock.symbol) if preset == "opportunities" and sort_by == "confidence" else query.order_by(primary, Stock.symbol)


def _row(c: StageScore, s: Stock, watched: set[str]) -> dict:
    return {"stock_id": s.id, "symbol": s.symbol, "company_name": s.company_name, "sector": s.sector, "basic_industry": s.basic_industry,
            **{k: _num(getattr(c, k)) for k in _NUMBERS}, "stage": c.stage, "sub_stage": c.sub_stage, "reason": c.reason, "prev_stage": c.prev_stage,
            "stage_since": c.stage_since.isoformat() if c.stage_since else None, "weeks_in_stage": c.weeks_in_stage, "weeks_above_sma": c.weeks_above_sma,
            "rs_improving": c.rs_improving, "next_stage": c.next_stage, "opportunity": c.opportunity, "near_breakout": c.near_breakout, "provisional": c.provisional,
            "pending": (c.detail or {}).get("pending"), "watched": s.id in watched}


@router.get("/overview")
def overview():
    db = get_db()
    try:
        cfg = settings.load(db)
        counts = {k: v for k, v in db.query(StageScore.stage, func.count()).group_by(StageScore.stage)}
        subs = {k: v for k, v in db.query(StageScore.sub_stage, func.count()).filter(StageScore.sub_stage.isnot(None)).group_by(StageScore.sub_stage)}
        first = db.query(StageScore).first()
        stage_2 = db.query(StageScore).filter(StageScore.stage == 2)
        return {"total": sum(counts.values()), "unclassified": counts.get(None, 0), "stages": {str(k): counts.get(k, 0) for k in (1, 2, 3, 4)}, "sub_stages": subs,
                "new_stage_2": stage_2.filter(StageScore.prev_stage.isnot(None), StageScore.weeks_in_stage <= cfg["new_weeks"]).count(),
                "stage_2_rs": stage_2.filter(StageScore.rs_improving.is_(True)).count(),
                "opportunities": db.query(StageScore).filter(StageScore.opportunity.is_(True)).count(),
                "transition_watch": db.query(StageScore).filter(StageScore.next_stage.isnot(None)).count(),
                "as_of": first.as_of.isoformat() if first else None, "week_end": first.week_end.isoformat() if first else None,
                "provisional": first.provisional if first else False, "computed_at": first.computed_at.isoformat() if first else None,
                "new_weeks": int(cfg["new_weeks"]), "recalculating": _recalc.locked(),
                "sectors": [r[0] for r in db.query(Stock.sector).join(StageScore, StageScore.stock_id == Stock.id).filter(Stock.sector.isnot(None)).distinct().order_by(Stock.sector)]}
    finally:
        db.close()


@router.get("/scores")
def scores(q: str | None = None, sector: str | None = None, stage: int | None = Query(None, ge=0, le=4), sub_stage: str | None = None, min_confidence: float = 0,
           min_rs: float | None = None, preset: str | None = None, watchlist: bool = False, sort_by: str = "confidence", order: str = "desc",
           limit: int = Query(100, ge=1, le=500), offset: int = 0):
    """`stage` 0 means Unclassified."""
    if preset and preset not in _PRESETS:
        raise HTTPException(400, f"preset must be one of {', '.join(_PRESETS)}")
    db = get_db()
    try:
        query = _filtered(db, q, sector, stage, sub_stage, min_confidence, min_rs, preset, watchlist)
        total = query.count()
        watched = {r[0] for r in db.query(StageWatch.stock_id)}
        rows = _ordered(query, sort_by, order, preset).offset(offset).limit(limit).all()
        return {"total": total, "results": [_row(c, s, watched) for c, s in rows]}
    finally:
        db.close()


_EXPORT = (("Symbol", "symbol"), ("Company", "company_name"), ("Sector", "sector"), ("Basic industry", "basic_industry"), ("CMP", "close"), ("Stage", "stage"), ("Sub-stage", "sub_stage"),
           ("Confidence", "confidence"), ("30W SMA", "sma30"), ("SMA slope %", "sma_slope_pct"), ("Distance from SMA %", "sma_distance_pct"), ("Relative strength", "rs"), ("RS improving", "rs_improving"),
           ("Weekly RSI", "rsi"), ("Volume ratio", "volume_ratio"), ("52W high distance %", "high_distance_pct"), ("Previous stage", "prev_stage"), ("Stage since", "stage_since"), ("Opportunity", "opportunity"))


@router.get("/export")
def export(format: str = "csv", q: str | None = None, sector: str | None = None, stage: int | None = Query(None, ge=0, le=4), sub_stage: str | None = None, min_confidence: float = 0,
           min_rs: float | None = None, preset: str | None = None, watchlist: bool = False, sort_by: str = "confidence", order: str = "desc"):
    """The filtered list, every row."""
    db = get_db()
    try:
        rows = _ordered(_filtered(db, q, sector, stage, sub_stage, min_confidence, min_rs, preset, watchlist), sort_by, order, preset).all()
        table = [[h for h, _ in _EXPORT]] + [[_row(c, s, set()).get(k) for _, k in _EXPORT] for c, s in rows]
    finally:
        db.close()
    if format == "xlsx":
        from openpyxl import Workbook
        book = Workbook()
        sheet = book.active
        sheet.title = "Stage screener"
        for row in table:
            sheet.append(row)
        buffer = io.BytesIO()
        book.save(buffer)
        return StreamingResponse(io.BytesIO(buffer.getvalue()), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": 'attachment; filename="stage_screener.xlsx"'})
    text = io.StringIO()
    csv.writer(text).writerows(table)
    return StreamingResponse(iter([text.getvalue()]), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="stage_screener.csv"'})


def _spells(weeks: list[StageHistory]) -> list[dict]:
    out: list[dict] = []
    for w in weeks:
        if w.stage is None:
            continue
        if out and out[-1]["stage"] == w.stage:
            out[-1].update(end=w.week_end.isoformat(), weeks=out[-1]["weeks"] + 1, last=_num(w.close))
        else:
            out.append({"stage": w.stage, "start": w.week_end.isoformat(), "end": w.week_end.isoformat(), "weeks": 1, "first": _num(w.close), "last": _num(w.close)})
    return out


@router.get("/stock")
def stock(stock_id: str):
    db = get_db()
    try:
        found = db.query(StageScore, Stock).join(Stock, Stock.id == StageScore.stock_id).filter(StageScore.stock_id == stock_id).first()
        if not found:
            raise HTTPException(404, "This stock has no prices for the stage screener")
        c, s = found
        watched = {r[0] for r in db.query(StageWatch.stock_id).filter(StageWatch.stock_id == stock_id)}
        weeks = db.query(StageHistory).filter(StageHistory.stock_id == stock_id).order_by(StageHistory.week_end).all()
        detail = c.detail or {}
        conditions = (detail.get("conditions") or {}).get(str(c.stage), []) if c.stage else []
        return {**_row(c, s, watched), "as_of": c.as_of.isoformat(), "week_end": c.week_end.isoformat(), "detail": {k: v for k, v in detail.items() if k != "conditions"},
                "explanation": classify.explain(c.stage, c.sub_stage, c.weeks_in_stage, c.stage_since.isoformat() if c.stage_since else None, _num(c.confidence), c.reason, conditions),
                "supporting": [x for x in conditions if x["met"] is True], "contradicting": [x for x in conditions if x["met"] is False], "not_read": [x for x in conditions if x["met"] is None],
                "spells": _spells(weeks),
                "weeks": [{"week": w.week_end.isoformat(), "open": _num(w.open), "high": _num(w.high), "low": _num(w.low), "close": _num(w.close), "volume": w.volume, "sma30": _num(w.sma30), "sma10": _num(w.sma10),
                           "rs": _num(w.rs), "stage": w.stage, "sub_stage": w.sub_stage, "confidence": _num(w.confidence), "event": w.event, "provisional": w.provisional} for w in weeks]}
    finally:
        db.close()


@router.put("/watchlist")
def watch(stock_id: str, on: bool = True):
    db = get_db()
    try:
        if not db.query(Stock.id).filter(Stock.id == stock_id).first():
            raise HTTPException(404, "Unknown stock")
        if on:
            db.execute(insert(StageWatch).values(stock_id=stock_id, added_at=datetime.now(timezone.utc)).on_conflict_do_nothing())
        else:
            db.query(StageWatch).filter(StageWatch.stock_id == stock_id).delete()
        db.commit()
        return {"stock_id": stock_id, "watched": on}
    finally:
        db.close()


@router.get("/thresholds")
def thresholds():
    db = get_db()
    try:
        current = settings.load(db)
        return {"recalculating": _recalc.locked(), "thresholds": [{"key": k, "value": current[k], "default": d, "min": low, "max": high, "group": group, "label": label}
                                                                 for k, (d, low, high, group, label) in settings.DEFAULTS.items()]}
    finally:
        db.close()


@router.put("/thresholds")
def set_thresholds(changes: dict[str, float]):
    """Saved values apply from the next recalculation."""
    db = get_db()
    try:
        return settings.save(db, changes)
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


def _recalculate() -> None:
    db = get_db()
    try:
        runner.run(db)
    finally:
        db.close()
        _recalc.release()


@router.post("/recalculate")
def recalculate():
    """Replays every stock's whole history on a background thread (about a minute)."""
    if not _recalc.acquire(blocking=False):
        raise HTTPException(409, "A recalculation is already running")
    threading.Thread(target=_recalculate, daemon=True).start()
    return {"started": True}
