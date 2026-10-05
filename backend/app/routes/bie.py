"""Business Intelligence Engine endpoints (app/bie): build a company's
sourced facts and download its sector-first report."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import BieFact, Stock

from app.bie import jobs
from app.bie.jobs import JOBS as _JOBS, OWN_BUILD as _OWN_BUILD, built_at as _built_at

router = APIRouter(prefix="/api/bie")


def _stock(db, symbol: str) -> Stock:
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper(), Stock.is_active.is_(True)).first()
    if stock is None:
        raise HTTPException(status_code=404, detail=f"Unknown symbol '{symbol}'")
    return stock


@router.get("/reports")
def reports():
    """Companies whose own facts are on file, newest build first."""
    db = get_db()
    try:
        rows = (db.query(Stock.symbol, Stock.company_name, Stock.basic_industry, func.max(BieFact.created_at))
                .join(BieFact, BieFact.company_id == Stock.id).filter(BieFact.fact_type.in_(_OWN_BUILD))
                .group_by(Stock.symbol, Stock.company_name, Stock.basic_industry).order_by(func.max(BieFact.created_at).desc()).all())
        return {"reports": [{"symbol": s, "company_name": n, "basic_industry": b, "built_at": at.isoformat()} for s, n, b, at in rows],
                "building": [s for s, j in _JOBS.items() if j["state"] == "running"]}
    finally:
        db.close()


@router.post("/{symbol}/build")
def build(symbol: str, background: BackgroundTasks):
    """Fetch, archive, extract and verify this company's filings (takes a few minutes)."""
    symbol = symbol.upper()
    db = get_db()
    try:
        _stock(db, symbol)
    finally:
        db.close()
    if not jobs.claim(symbol):
        return {"symbol": symbol, "status": "already running"}
    background.add_task(jobs.run, symbol)
    return {"symbol": symbol, "status": "started"}


@router.get("/{symbol}/status")
def status(symbol: str):
    db = get_db()
    try:
        stock = _stock(db, symbol)
        rows = db.query(BieFact.verification_status).filter(BieFact.company_id == stock.id).all()
        counts: dict[str, int] = {}
        for (s,) in rows:
            counts[s] = counts.get(s, 0) + 1
        built_at = _built_at(db, stock.id)
        retried = jobs.retry_pending(stock.symbol) if built_at is not None else False
        return {"symbol": stock.symbol, "facts": len(rows), "verification": counts, "built": built_at is not None,
                "built_at": built_at.isoformat() if built_at else None, "job": _JOBS.get(stock.symbol),
                "model_steps_pending": jobs.is_pending(stock.symbol), "model_steps_retry_started": retried}
    finally:
        db.close()


@router.get("/{symbol}/report.pdf")
def report(symbol: str):
    """Render the report from the facts on file and return the PDF."""
    from app.bie.report.render import render_report
    db = get_db()
    try:
        stock = _stock(db, symbol)
        if _built_at(db, stock.id) is None:
            raise HTTPException(status_code=409, detail="This company's deep report has not been built yet")
        path = render_report(db, stock.id)
    finally:
        db.close()
    return FileResponse(path, media_type="application/pdf", filename=path.rsplit("/", 1)[-1])


@router.get("/{symbol}/summary")
def summary(symbol: str):
    """What the Deep Report page of a stock's analysis shows: the headline, the valuation lenses, sector measures,
    the assessment and the exhibits, all from the same build the PDF is rendered from."""
    from app.bie.report.builder import build_report
    db = get_db()
    try:
        stock = _stock(db, symbol)
        if _built_at(db, stock.id) is None:
            raise HTTPException(status_code=409, detail="This company's deep report has not been built yet")
        ticker, company_name = stock.symbol, stock.company_name
        r = build_report(db, stock.id)
        db.commit()
    finally:
        db.close()
    v, lf = r["valuation"], r["latest_fy"]
    modelled = bool(v) and "skipped" not in v
    top = r["segments"][0]["top"] if r["segments"] else None
    out = {
        "symbol": ticker, "company_name": company_name, "generated": r["generated"].isoformat(), "basis": r["basis"],
        "classification": r["classification"], "cutoff": r["cutoff"].isoformat() if r["cutoff"] else None,
        "headline": (f"{top['name']} earns {top['result_share']:.0%} of segment profit on {top['revenue_share']:.0%} of segment revenue."
                     if top and top.get("result_share") is not None and top.get("revenue_share") is not None
                     else (f"One reportable segment: {r['single_segment']}." if r.get("single_segment") else None)),
        "latest_year": {"label": lf["label"], "revenue": lf["revenue"], "profit": lf["profit"], "revenue_growth": lf.get("revenue_growth")} if lf else None,
        "evidence": {k: r["evidence"][k] for k in ("facts", "reported", "calculated", "verified", "failed")}, "sources": len(r["sources"]),
        "segments": [{"name": s["name"], "revenue": s["revenue"], "result": s["result"], "margin": s["margin"], "revenue_share": s["revenue_share"],
                      "result_share": s["result_share"]} for s in (r["segments"][0]["rows"] if r["segments"] else [])],
        "sector_measures": [{**{k: m[k] for k in ("label", "value", "unit", "quote", "kind", "page", "period", "period_kind", "earlier", "earlier_period", "by_model")},
                             "date": m["date"].isoformat(), "earlier_date": m["earlier_date"].isoformat() if m["earlier_date"] else None}
                            for m in r["sector_measures"]],
        "outlook": [{"text": g["text"], "page": g["page"], "quarter": g["quarter"]} for g in (r["guidance"] or [])[:5]],
        "questions": r["assessment"]["questions"], "narrative_by": r["assessment"]["narrative"]["author"],
        "risks": [{"kind": x["kind"], "severity": x["severity"], "text": x["text"]} for x in r["assessment"]["risks"]],
        "triggers": r["assessment"]["triggers"],
        "exhibits": [{"n": e["n"], "title": e["title"], "unit": e["unit"], "note": e["note"], "svg": e["svg"]} for e in r["exhibits"]],
        "valuation": None,
    }
    if modelled:
        base = v["scenarios"]["Base"]
        out["valuation"] = {
            "price": v["price"], "price_date": v["price_date"].isoformat(), "is_lender": v["is_lender"], "by_segment": v["by_segment"],
            "overrides": len(v["overrides"]), "weights": base.get("weights"),
            "scenarios": {name: {k: sc.get(k) for k in ("dcf", "sotp", "relative", "average", "gap")} for name, sc in v["scenarios"].items()},
            "forecast": [{"label": y["label"], "revenue": y["revenue"] / 1e7, "profit": y["pat"] / 1e7, "eps": y["eps"]} for y in base["rows"]],
            "breaks": [{"name": b["name"], "growth": b["growth"], "history_growth": b["history_growth"], "margin": b["margin"],
                        "history_margin": b["history_margin"]} for b in v["breaks"]],
            "bridge": [{"label": i["label"], "value": i["value"] / 1e7, "basis": i["basis"]} for i in v["equity_bridge"]["items"]],
        }
    return out


@router.get("/{symbol}/model.xlsx")
def model(symbol: str):
    """The model behind the report as an Excel workbook: history, assumptions, forecast statements, valuation and charts."""
    from app.bie.report.workbook import build_workbook
    db = get_db()
    try:
        stock = _stock(db, symbol)
        if _built_at(db, stock.id) is None:
            raise HTTPException(status_code=409, detail="This company's deep report has not been built yet")
        path = build_workbook(db, stock.id)
    finally:
        db.close()
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=path.rsplit("/", 1)[-1])


# ── phase 4.5: assumption control ────────────────────────────────────────────

from pydantic import BaseModel  # noqa: E402


class OverrideIn(BaseModel):
    metric: str
    value: float
    reason: str
    unit: str = "Company"
    scenario: str = "All"
    fiscal_year: int | None = None
    evidence_url: str | None = None
    confidence: str = "MEDIUM"


@router.get("/{symbol}/assumptions")
def assumptions(symbol: str, scenario: str = "Base"):
    """System estimate beside the value in force for every assumption, with the overrides and their effect."""
    from app.bie.overrides import control_centre
    db = get_db()
    try:
        return control_centre(db, _stock(db, symbol).id, scenario)
    finally:
        db.close()


@router.post("/{symbol}/overrides")
def create_override(symbol: str, body: OverrideIn):
    from app.bie.overrides import OverrideError, set_override
    db = get_db()
    try:
        try:
            row = set_override(db, _stock(db, symbol).id, **body.model_dump())
        except OverrideError as e:
            raise HTTPException(status_code=400, detail=str(e))
        db.commit()
        return {"id": row.id}
    finally:
        db.close()


@router.delete("/{symbol}/overrides/{override_id}")
def delete_override(symbol: str, override_id: str):
    """Reset to the model: the override is retired, not erased, and stays in the history."""
    from app.bie.overrides import reset_override
    db = get_db()
    try:
        _stock(db, symbol)
        if not reset_override(db, override_id):
            raise HTTPException(status_code=404, detail="No active override with that id")
        db.commit()
        return {"reset": override_id}
    finally:
        db.close()


@router.get("/{symbol}/overrides/history")
def override_history(symbol: str):
    from app.bie.overrides import history
    db = get_db()
    try:
        return {"history": history(db, _stock(db, symbol).id)}
    finally:
        db.close()


@router.get("/{symbol}/what-if")
def what_if_route(symbol: str, metric: str, values: str, unit: str = "Company", scenario: str = "All", fiscal_year: int | None = None):
    """Base-case value under each trial value of one assumption (comma-separated), without saving anything."""
    from app.bie.overrides import METRICS, what_if
    if metric not in METRICS:
        raise HTTPException(status_code=400, detail=f"metric must be one of {sorted(METRICS)}")
    try:
        trial = [float(x) for x in values.split(",")][:9]
    except ValueError:
        raise HTTPException(status_code=400, detail="values must be comma-separated numbers")
    db = get_db()
    try:
        return {"results": what_if(db, _stock(db, symbol).id, metric=metric, values=trial, unit=unit, scenario=scenario, fiscal_year=fiscal_year)}
    finally:
        db.close()


@router.get("/{symbol}/assumption-ranking")
def assumption_ranking(symbol: str):
    """Which assumptions move the value most."""
    from app.bie.overrides import ranking
    db = get_db()
    try:
        return {"ranking": ranking(db, _stock(db, symbol).id)}
    finally:
        db.close()
