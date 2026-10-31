"""Stock Quality framework scores (app/framework/), with the convergence read
(app/convergence/) and the Stage Screener's results alongside them."""
import csv
import io
import threading
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.convergence import runner as convergence_runner
from app.convergence import settings as convergence_settings
from app.convergence.score import CLASSES
from app.framework import sector_rank, store
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import CanslimScore, ConvergenceHistory, ConvergenceScore, FrameworkScore, StageHistory, StageScore, Stock

router = APIRouter(prefix="/api/framework")
_recalc = threading.Lock()

SCORES = ("quality", "fundamental", "quantitative", "relative_strength", "technical", "valuation")


def _row(score, stock: Stock) -> dict:
    out = {
        "stock_id": stock.id, "symbol": stock.symbol, "company_name": stock.company_name, "sector": stock.sector,
        "market_cap": float(stock.market_cap) if stock.market_cap is not None else None,
        "as_of": score.as_of, "basis": score.basis, "latest_fy": score.latest_fy, "sector_framework": score.sector_framework,
        "trend": score.trend, "classification": score.classification, "action": score.action,
        "valuation_view": score.valuation_view, "reconstructed": score.reconstructed,
        "quality_direction": score.quality_direction,
        "quality_change_6m": float(score.quality_change_6m) if score.quality_change_6m is not None else None,
        "quality_change_12m": float(score.quality_change_12m) if score.quality_change_12m is not None else None,
    }
    out.update({name: float(v) if (v := getattr(score, name)) is not None else None for name in (*SCORES, "business_quality")})
    return out


def _num(v) -> float | None:
    return float(v) if v is not None else None


def _with_convergence(row: dict, c: ConvergenceScore | None, st: StageScore | None) -> dict:
    return {**row, "combined": _num(c.combined) if c else None, "research_class": c.classification if c else None, "confidence_label": c.confidence_label if c else None,
            "risk_reward": _num(c.risk_reward) if c else None, "stage": st.stage if st else None, "sub_stage": st.sub_stage if st else None, "cmp": _num(st.close) if st else None,
            "rs_improving": st.rs_improving if st else None}


def _rows(db, q, sector, trend, direction, classification, action, research_class, stage, sort, order) -> tuple[list[dict], dict, list[str]]:
    stocks = {s.id: s for s in db.query(Stock).filter(Stock.is_active.is_(True))}
    latest = [r for r in store.latest_for_all(db) if r.stock_id in stocks]
    reads = {c.stock_id: c for c in db.query(ConvergenceScore)}
    stages = {c.stock_id: c for c in db.query(StageScore)}
    rows = [_with_convergence(_row(r, stocks[r.stock_id]), reads.get(r.stock_id), stages.get(r.stock_id)) for r in latest]
    ranked = sector_rank.ranks([(r["stock_id"], stocks[r["stock_id"]].basic_industry, stocks[r["stock_id"]].industry, r["quality"]) for r in rows])
    counts = {name: 0 for name in CLASSES}
    for r in rows:
        r["sector_rank"] = ranked.get(r["stock_id"])
        if r["research_class"]:
            counts[r["research_class"]] += 1
    if q:
        needle = q.strip().lower()
        rows = [r for r in rows if needle in r["symbol"].lower() or needle in r["company_name"].lower()]
    if sector:
        rows = [r for r in rows if r["sector"] == sector]
    if trend:
        rows = [r for r in rows if r["trend"] == trend.upper()]
    if direction:
        rows = [r for r in rows if r["quality_direction"] == direction.upper()]
    if classification:
        rows = [r for r in rows if r["classification"] == classification]
    if action:
        rows = [r for r in rows if r["action"] == action]
    if research_class:
        rows = [r for r in rows if r["research_class"] == research_class]
    if stage is not None:
        rows = [r for r in rows if r["stage"] == (stage or None)]
    key = sort if sort in (*SCORES, "market_cap", "symbol", "quality_change_6m", "quality_change_12m", "combined", "risk_reward", "stage", "cmp") else "quality"
    present = [r for r in rows if r[key] is not None]
    present.sort(key=lambda r: r[key], reverse=order == "desc")
    return present + [r for r in rows if r[key] is None], counts, sorted({s.sector for s in stocks.values() if s.sector})  # unscored rows always last


@router.get("/scores")
def list_scores(
    q: str | None = None, sector: str | None = None, trend: str | None = None, direction: str | None = None,
    classification: str | None = None, action: str | None = None, research_class: str | None = None, stage: int | None = Query(None, ge=0, le=4),
    sort: str = Query("quality"), order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0),
):
    """Latest framework scores for every scored stock, one row each. `stage` 0 means Unclassified."""
    db = get_db()
    try:
        rows, counts, sectors = _rows(db, q, sector, trend, direction, classification, action, research_class, stage, sort, order)
        market = db.query(CanslimScore).filter(CanslimScore.m.isnot(None)).first()
        return {"total": len(rows), "scores": rows[offset:offset + limit], "sectors": sectors, "class_counts": counts,
                "market": (market.detail or {}).get("m") if market else None}
    finally:
        db.close()


_EXPORT = (("Symbol", "symbol"), ("Company", "company_name"), ("Sector", "sector"), ("CMP", "cmp"), ("Combined", "combined"), ("Research class", "research_class"), ("Confidence", "confidence_label"),
           ("Quality", "quality"), ("Fundamental", "fundamental"), ("Technical", "technical"), ("Stage", "stage"), ("Sub-stage", "sub_stage"), ("Relative strength", "relative_strength"),
           ("RS improving", "rs_improving"), ("Valuation", "valuation"), ("Valuation view", "valuation_view"), ("Reward/risk", "risk_reward"), ("Decision", "classification"), ("Action", "action"))


@router.get("/export")
def export(format: str = "csv", q: str | None = None, sector: str | None = None, trend: str | None = None, direction: str | None = None, classification: str | None = None,
           research_class: str | None = None, stage: int | None = Query(None, ge=0, le=4), sort: str = "combined", order: str = Query("desc", pattern="^(asc|desc)$")):
    """The filtered list, every row."""
    db = get_db()
    try:
        rows = _rows(db, q, sector, trend, direction, classification, None, research_class, stage, sort, order)[0]
    finally:
        db.close()
    table = [[h for h, _ in _EXPORT]] + [[r.get(k) for _, k in _EXPORT] for r in rows]
    if format == "xlsx":
        from openpyxl import Workbook
        book = Workbook()
        book.active.title = "Combined score"
        for row in table:
            book.active.append(row)
        buffer = io.BytesIO()
        book.save(buffer)
        return StreamingResponse(io.BytesIO(buffer.getvalue()), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": 'attachment; filename="combined_score.xlsx"'})
    text = io.StringIO()
    csv.writer(text).writerows(table)
    return StreamingResponse(iter([text.getvalue()]), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="combined_score.csv"'})


@router.get("/convergence/settings")
def get_settings():
    db = get_db()
    try:
        current = convergence_settings.load(db)
        return {"version": convergence_settings.version(current), "recalculating": _recalc.locked(),
                "settings": [{"key": k, "value": current[k], "default": d, "min": low, "max": high, "group": group, "label": label}
                             for k, (d, low, high, group, label) in convergence_settings.DEFAULTS.items()]}
    finally:
        db.close()


@router.put("/convergence/settings")
def put_settings(changes: dict[str, float]):
    """Saved values apply from the next recalculation."""
    db = get_db()
    try:
        return convergence_settings.save(db, changes)
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


def _recalculate() -> None:
    db = get_db()
    try:
        convergence_runner.run(db)
    finally:
        db.close()
        _recalc.release()


@router.post("/convergence/recalculate")
def recalculate():
    """Rebuilds today's read on a background thread (a few seconds). Older days stay as they were."""
    if not _recalc.acquire(blocking=False):
        raise HTTPException(409, "A recalculation is already running")
    threading.Thread(target=_recalculate, daemon=True).start()
    return {"started": True}


_ORDER = {name: i for i, name in enumerate(reversed(CLASSES[:-1]))}


def _convergence_view(read: ConvergenceScore, history: list[dict], moves: list[dict], canslim: float | None) -> dict:
    return {**(read.detail or {}), "combined": _num(read.combined), "classification": read.classification, "confidence": _num(read.confidence), "confidence_label": read.confidence_label,
            "as_of": read.as_of.isoformat(), "method_version": read.method_version, "history": history, "moves": moves, "canslim": canslim}


def _timeline(db, stock_id: str) -> tuple[list[dict], list[dict]]:
    """Each date with a stored reading, newest first, and the classification's moves.
    Older dates come from `fw_scores` and `stage_history` with what was recorded
    then; reward/risk, combined and class exist only from the day tracking began."""
    days: dict = {}
    for r in db.query(FrameworkScore).filter(FrameworkScore.stock_id == stock_id).order_by(FrameworkScore.as_of):
        if r.as_of not in days or r.basis == store.FULL:
            days[r.as_of] = {"on": r.as_of.isoformat(), "quality": _num(r.quality), "fundamental": _num(r.fundamental), "technical": _num(r.technical),
                             "relative_strength": _num(r.relative_strength), "valuation": _num(r.valuation)}
    weeks = {w.week_end: w for w in db.query(StageHistory).filter(StageHistory.stock_id == stock_id)}
    for day, row in days.items():
        week = weeks.get(day + timedelta(days=4 - day.weekday()))
        row.update(stage=week.stage if week else None, sub_stage=week.sub_stage if week else None)
    tracked = db.query(ConvergenceHistory).filter(ConvergenceHistory.stock_id == stock_id).order_by(ConvergenceHistory.as_of).all()
    for t in tracked:
        days[t.as_of] = {"on": t.as_of.isoformat(), "quality": _num(t.quality), "fundamental": _num(t.fundamental), "technical": _num(t.technical), "relative_strength": _num(t.relative_strength),
                         "valuation": _num(t.valuation), "stage": t.stage, "sub_stage": t.sub_stage, "risk_reward": _num(t.risk_reward), "combined": _num(t.combined),
                         "classification": t.classification, "method_version": t.method_version}
    moves = [{"on": b.as_of.isoformat(), "from": a.classification, "to": b.classification,
              "direction": "upgrade" if _ORDER.get(b.classification, -1) > _ORDER.get(a.classification, -1) else "downgrade"}
             for a, b in zip(tracked, tracked[1:]) if a.classification != b.classification]
    return [days[d] for d in sorted(days, reverse=True)], moves[::-1]


@router.get("/{symbol}")
def stock_scores(symbol: str):
    """One stock's latest scores with every input behind them."""
    db = get_db()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if stock is None:
            raise HTTPException(404, f"Unknown symbol '{symbol}'")
        score = store.latest(db, stock.id)
        if score is None:
            raise HTTPException(404, f"No framework scores for '{symbol}' yet")
        peers = [(r.stock_id, s.basic_industry, s.industry, float(r.quality) if r.quality is not None else None)
                 for r in store.latest_for_all(db) if (s := db.get(Stock, r.stock_id)) is not None and s.sector == stock.sector]
        from app.framework.decisions import best_alternative, replacement, values

        from app.risk.record import for_stock

        alt = best_alternative(db, stock, stock.id)
        try:
            risk = for_stock(db, stock.id)  # read fresh: a new order shows before the next scoring
        except Exception:  # noqa: BLE001 — tables not migrated yet
            db.rollback()
            risk = None
        out = {**_row(score, stock), "sector_rank": sector_rank.ranks(peers).get(stock.id), "detail": score.detail,
               "best_alternative": alt, "risk": risk}
        read, stage = db.get(ConvergenceScore, stock.id), db.get(StageScore, stock.id)
        out = _with_convergence(out, read, stage)
        if read:
            history, moves = _timeline(db, stock.id)
            canslim = db.get(CanslimScore, stock.id)
            out["convergence"] = _convergence_view(read, history, moves, _num(canslim.canslim) if canslim else None)
        try:
            from app.macro.fpi import flow_for_sector

            from app.ingestion.estimate_revisions_client import for_stock as estimates_for

            out["sector_flow"] = flow_for_sector(db, stock.sector)  # shown beside Relative Strength, never scored
            out["estimates"] = estimates_for(db, stock.id)  # analysts' opinion: shown, never scored
        except Exception:  # noqa: BLE001 — tables not migrated yet
            db.rollback()
        if alt and score.classification in ("Replacement Candidate", "Improving / Watch", "Avoid"):
            out["replacement"] = replacement({**values(score), "symbol": stock.symbol, "valuation_view": score.valuation_view},
                                             alt, score.detail, store.latest(db, alt["stock_id"]))
        return out
    finally:
        db.close()


@router.post("/{symbol}/explain")
def explain_stock(symbol: str, model: bool = True):
    """Plain-language reasoning for the stock's decision (gpt-oss, checked
    against the decision; fixed text when the model is unavailable)."""
    from app.framework.decisions import best_alternative, values
    from app.framework.explain import explain

    db = get_db()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        row = store.latest(db, stock.id) if stock else None
        if row is None:
            raise HTTPException(404, f"No framework scores for '{symbol}' yet")
        return explain(db, row, values(row), best_alternative(db, stock, stock.id), use_model=model)
    finally:
        db.close()


@router.get("/{symbol}/integrated-report.pdf")
def integrated_report(symbol: str):
    """One PDF: the Stock Quality framework section, the editorial report (when a
    full analysis exists) and the deep report (when built)."""
    from app.reporting.integrated.build import build

    db = get_db()
    try:
        path = build(db, symbol)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    finally:
        db.close()
    return FileResponse(path, media_type="application/pdf", filename=path.rsplit("/", 1)[-1])
