"""What the Market & Macro page shows."""
from __future__ import annotations

import re
from datetime import date

from sqlalchemy.orm import Session

from app.infrastructure.database.models import BieFact, MacroPoint
from app.ingestion import news_feeds
from app.macro.catalogue import GROUPS, SERIES
from app.macro.fpi import sector_flows

_POINTS = 120
_STALE_DAYS = {"daily": 10, "monthly": 100, "quarterly": 200, "annual": 800}


def _curve(db: Session) -> dict | None:
    """Latest CCIL tenor-wise yields for central government bonds."""
    facts = db.query(BieFact).filter(BieFact.scope == "MACRO", BieFact.key == "gsec_yield_pct").all()
    if not facts:
        return None
    latest = max(f.period_end for f in facts)
    best: dict[str, float] = {}
    for f in facts:
        attrs = f.attributes or {}
        if f.period_end == latest and attrs.get("is_central_government"):
            best.setdefault(attrs.get("tenor_bucket") or "", float(f.value_num))
    points = sorted(best.items(), key=lambda kv: float((re.search(r"[\d.]+", kv[0]) or [0])[0]) if re.search(r"[\d.]+", kv[0]) else 0)
    return {"as_of": latest.isoformat(), "points": [{"tenor": k, "yield": v} for k, v in points], "source": "CCIL tenor-wise indicative yields"}


def _imf(db: Session) -> list[dict]:
    rows = db.query(BieFact).filter(BieFact.scope == "MACRO", BieFact.key == "real_gdp_growth_pct").all()
    latest: dict[str, float] = {}
    for f in sorted(rows, key=lambda r: r.created_at):
        latest[f.dimension] = float(f.value_num)
    return [{"year": y, "growth": v} for y, v in sorted(latest.items())]


def overview(db: Session) -> dict:
    series: dict[str, list[MacroPoint]] = {}
    for p in db.query(MacroPoint).order_by(MacroPoint.on_date):
        series.setdefault(p.series, []).append(p)
    groups = []
    for name in GROUPS:
        items = []
        for sid, (label, unit, group, source, freq) in SERIES.items():
            pts = series.get(sid)
            if group != name or not pts:
                continue
            last, before = pts[-1], pts[-2] if len(pts) > 1 else None
            step = max(1, len(pts) // _POINTS)
            history = pts[::-1][::step][::-1]
            items.append({"id": sid, "label": label, "unit": unit, "source": source, "frequency": freq,
                          "value": float(last.value), "date": last.on_date.isoformat(),
                          "stale": (date.today() - last.on_date).days > _STALE_DAYS.get(freq, 10**6),
                          "previous": float(before.value) if before else None,
                          "change": round(float(last.value) - float(before.value), 4) if before else None,
                          "history": [{"date": p.on_date.isoformat(), "value": float(p.value)} for p in history]})
        if items:
            groups.append({"group": name, "series": items})
    missing = [SERIES[s][0] for s in SERIES if s not in series]
    return {"groups": groups, "yield_curve": _curve(db), "imf_gdp": _imf(db), "sector_flows": sector_flows(db), "headlines": news_feeds.latest(db), "not_read": missing,
            "not_available": ["Bank credit growth: RBI's DBIE has no feed this app can read"]}
