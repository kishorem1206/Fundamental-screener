"""Portfolio analysis — the end of the framework's decision flow (section 16):
compare with what is owned, size the position, check sector allocation, check
total asset allocation, then give the final action.

  Section 12  every stock held is set against the best same-sector stock that
              passes the core gate. "Better company" (Quality) and "better
              current opportunity" (readiness to buy, relative strength,
              technicals, valuation) are reported separately; a replacement is
              suggested only when the candidate is clearly better.
  Section 13  a size band per decision (High 6-8%, Medium 4-5%, Small 2-3%,
              Tactical up to 1.5% of the equity book), stepped down for high
              volatility or a holding that moves with the rest of the
              portfolio; capped per stock and per sector; with a liquidity check.
  Section 14  allocation across equity, equity funds, debt, gold, cash and
              international against the user's own targets (nothing is judged
              against a target that has not been set), portfolio volatility and
              one-year drawdown against the user's drawdown tolerance.
"""
from __future__ import annotations

import math
import statistics
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.framework import price_stats, store
from app.framework.decisions import best_alternative, values
from app.infrastructure.database.models import FrameworkScore, PortfolioHolding, PortfolioSettings, Stock

DEFAULTS = {
    "max_stock_pct": 10.0, "max_sector_pct": 25.0, "drawdown_tolerance_pct": 25.0, "targets": {},
    "size_bands": {"High": [6.0, 8.0], "Medium": [4.0, 5.0], "Small": [2.0, 3.0], "Tactical only": [0.0, 1.5]},
    "high_volatility_pct": 45.0, "max_correlation": 0.8, "max_share_of_daily_turnover": 0.10,
}
_STEP_DOWN = {"High": "Medium", "Medium": "Small", "Small": "Small", "Tactical only": "Tactical only"}
_READY = {"Add gradually": 0, "Add on confirmation": 1, "Hold": 2, "Watch": 3, "Reduce": 4, "Replace": 5, "Avoid": 6}


def settings(db: Session) -> dict:
    row = db.get(PortfolioSettings, "default")
    return {**DEFAULTS, **(row.settings if row else {})}


def save_settings(db: Session, new: dict) -> dict:
    allowed = {k: v for k, v in new.items() if k in DEFAULTS}
    row = db.get(PortfolioSettings, "default")
    merged = {**(row.settings if row else {}), **allowed}
    if row is None:
        db.add(PortfolioSettings(id="default", settings=merged, updated_at=datetime.now(timezone.utc)))
    else:
        row.settings, row.updated_at = merged, datetime.now(timezone.utc)
    db.commit()
    return {**DEFAULTS, **merged}


def opportunity(v: dict) -> float | None:
    parts = [v.get(k) for k in ("relative_strength", "technical", "valuation") if v.get(k) is not None]
    return sum(parts) / len(parts) if parts else None


def clearly_better(mine: dict, mine_class: str | None, cand: dict) -> tuple[bool, str]:
    """Section 12: is the candidate clearly better than what is owned?"""
    if cand.get("classification") not in ("Core Quality", "Investable"):
        return False, "candidate does not pass the core gate"
    mq, cq = mine.get("quality"), cand.get("quality")
    if mq is not None and cq is not None and cq < mq - 5:
        return False, f"candidate is the weaker business (Quality {cq:.0f} against {mq:.0f})"
    mf, cf = mine.get("fundamental"), cand.get("fundamental")
    if mf is not None and cf is not None and cf < mf - 10:
        return False, f"candidate's fundamentals are weaker ({cf:.0f} against {mf:.0f})"
    if mine_class in ("Replacement Candidate", "Avoid"):
        return True, "the holding fails the gate and the candidate passes it"
    mo, co = opportunity(mine), opportunity(cand)
    if mo is not None and co is not None and co - mo >= 10:
        return True, f"same or better business, and a better opportunity now ({co:.0f} against {mo:.0f} on strength, timing and price)"
    return False, "not clearly better: keep the existing holding"


def _daily_returns(db: Session, ids: list[str], end: date) -> dict[str, dict[date, float]]:
    rows = db.execute(text("select stock_id, bar_date, adj_close from price_bars_daily where stock_id = any(:ids) "
                           "and bar_date > :f and bar_date <= :e order by stock_id, bar_date"),
                      {"ids": ids, "f": end - timedelta(days=372), "e": end}).all()
    closes: dict[str, list[tuple[date, float]]] = {}
    for sid, d, v in rows:
        closes.setdefault(sid, []).append((d, float(v)))
    return {sid: {b[0]: b[1] / a[1] - 1 for a, b in zip(s, s[1:]) if a[1] > 0} for sid, s in closes.items()}


def _corr(a: dict, b: dict) -> float | None:
    days = sorted(set(a) & set(b))
    if len(days) < 60:
        return None
    x, y = [a[d] for d in days], [b[d] for d in days]
    try:
        return statistics.correlation(x, y)
    except statistics.StatisticsError:
        return None


def _portfolio_risk(rets: dict, weights: dict[str, float]) -> dict:
    days = sorted(set().union(*[set(r) for r in rets.values()])) if rets else []
    if len(days) < 120:
        return {"reason": "too little stored price history for the holdings"}
    total = sum(weights.values())
    series = []
    for d in days:
        avail = {s: w for s, w in weights.items() if d in rets.get(s, {})}
        cover = sum(avail.values())
        if cover >= 0.7 * total:
            series.append((d, sum(rets[s][d] * w for s, w in avail.items()) / cover))
    if len(series) < 120:
        return {"reason": "too little overlapping price history"}
    vol = statistics.pstdev([r for _, r in series]) * math.sqrt(252) * 100
    level, path = 1.0, []
    for d, r in series:
        level *= 1 + r
        path.append((d, level))
    dd, peak, trough = price_stats.max_drawdown(path)
    return {"volatility_pct": round(vol, 1), "max_fall_1y_pct": round(dd, 1), "peak": peak and peak.isoformat(),
            "trough": trough and trough.isoformat(), "return_1y_pct": round((path[-1][1] - 1) * 100, 1),
            "basis": "the listed stocks held, at today's weights, over the last year (funds and other assets not included)"}


def _turnover(db: Session, sid: str, end: date) -> float | None:
    rows = db.execute(text("select close * volume from price_bars_daily where stock_id = :s and bar_date <= :e "
                           "and volume > 0 order by bar_date desc limit 20"), {"s": sid, "e": end}).scalars().all()
    return statistics.median(float(v) for v in rows) if len(rows) >= 10 else None


def analyse(db: Session) -> dict:
    cfg = settings(db)
    holdings = db.query(PortfolioHolding).all()
    total = sum(float(h.value) for h in holdings)
    if not holdings or total <= 0:
        return {"holdings": [], "total": 0, "settings": cfg, "empty": True}

    by_class: dict[str, float] = {}
    for h in holdings:
        by_class[h.asset_class] = by_class.get(h.asset_class, 0) + float(h.value)
    allocation = []
    for cls, val in sorted(by_class.items(), key=lambda x: -x[1]):
        pct = val / total * 100
        target = (cfg["targets"] or {}).get(cls)
        status = None
        if target is not None:
            status = "over" if pct > target + 5 else "under" if pct < target - 5 else "on target"
        allocation.append({"asset_class": cls, "value": round(val, 2), "pct": round(pct, 1), "target_pct": target, "status": status})

    equity_book = by_class.get("EQUITY", 0) + by_class.get("EQUITY_FUND", 0)
    stocks = {h.stock_id: db.get(Stock, h.stock_id) for h in holdings if h.stock_id}
    sector_value: dict[str, float] = {}
    for h in holdings:
        if h.asset_class == "EQUITY":
            sec = (stocks.get(h.stock_id).sector if h.stock_id and stocks.get(h.stock_id) else None) or "Unclassified"
            sector_value[sec] = sector_value.get(sec, 0) + float(h.value)
        elif h.asset_class == "EQUITY_FUND":
            sector_value["Equity funds (diversified)"] = sector_value.get("Equity funds (diversified)", 0) + float(h.value)
    sectors = [{"sector": s, "value": round(v, 2), "pct_of_equity": round(v / equity_book * 100, 1) if equity_book else None,
                "over_limit": bool(equity_book and s != "Equity funds (diversified)" and v / equity_book * 100 > cfg["max_sector_pct"])}
               for s, v in sorted(sector_value.items(), key=lambda x: -x[1])]
    sector_pct = {s["sector"]: s["pct_of_equity"] or 0 for s in sectors}

    end = price_stats.as_of(db) or date.today()
    held_ids = [h.stock_id for h in holdings if h.stock_id and h.asset_class == "EQUITY"]
    rets = _daily_returns(db, held_ids, end) if held_ids else {}
    weights = {}
    for h in holdings:
        if h.stock_id and h.asset_class == "EQUITY":
            weights[h.stock_id] = weights.get(h.stock_id, 0) + float(h.value)

    rows = []
    for h in sorted(holdings, key=lambda x: -float(x.value)):
        out = {"id": h.id, "source": h.source, "name": h.name, "symbol": h.symbol, "asset_class": h.asset_class,
               "class_basis": h.class_basis, "quantity": h.quantity and float(h.quantity), "avg_price": h.avg_price and float(h.avg_price),
               "last_price": h.last_price and float(h.last_price), "value": float(h.value), "pct_of_total": round(float(h.value) / total * 100, 2),
               "as_of": h.as_of.isoformat(), "stock_id": h.stock_id}
        if h.asset_class == "EQUITY" and equity_book:
            out["pct_of_equity"] = round(float(h.value) / equity_book * 100, 2)
        if h.stock_id and h.asset_class == "EQUITY":
            out.update(_stock_view(db, h, stocks[h.stock_id], out, cfg, sector_pct, rets, weights, equity_book, end))
        rows.append(out)

    risk = _portfolio_risk(rets, weights) if weights else {"reason": "no listed stocks held"}
    if "max_fall_1y_pct" in risk:
        risk["within_drawdown_tolerance"] = -risk["max_fall_1y_pct"] <= cfg["drawdown_tolerance_pct"]
    return {"total": round(total, 2), "equity_book": round(equity_book, 2), "allocation": allocation, "sectors": sectors,
            "holdings": rows, "risk": risk, "settings": cfg, "candidates": candidates(db, holdings, cfg, sector_pct),
            "prices_as_of": end.isoformat(), "empty": False}


def _stock_view(db, h, stock, out, cfg, sector_pct, rets, weights, equity_book, end) -> dict:
    row = store.latest(db, h.stock_id)
    if row is None:
        return {"framework": None, "final_action": "Watch", "final_reason": "no framework scores for this stock yet"}
    v = values(row)
    decision = (row.detail or {}).get("decision") or {}
    size = decision.get("size")
    notes = []
    vol = (((row.detail or {}).get("quantitative") or {}).get("components") or {}).get("volatility", {}).get("annualised_pct")
    if size in _STEP_DOWN and vol and vol > cfg["high_volatility_pct"]:
        size, _ = _STEP_DOWN[size], notes.append(f"volatility {vol:.0f}% a year: one size smaller")
    others = {s: w for s, w in weights.items() if s != h.stock_id}
    corr_rest = None
    if h.stock_id in rets and others:
        tot = sum(others.values())
        rest = {}
        for s, w in others.items():
            for d, r in rets.get(s, {}).items():
                rest[d] = rest.get(d, 0) + r * w / tot
        corr_rest = _corr(rets[h.stock_id], rest)
        if size in _STEP_DOWN and corr_rest is not None and corr_rest > cfg["max_correlation"]:
            size, _ = _STEP_DOWN[size], notes.append(f"moves closely with the rest of the portfolio (correlation {corr_rest:.2f}): one size smaller")
    closest = None
    for s in others:
        c = _corr(rets.get(h.stock_id, {}), rets.get(s, {}))
        if c is not None and (closest is None or c > closest[1]):
            closest = (s, c)
    band = cfg["size_bands"].get(size) if size else None
    weight = out.get("pct_of_equity") or 0
    sector = stock.sector or "Unclassified"
    turnover = _turnover(db, h.stock_id, end)
    if turnover and float(h.value) > cfg["max_share_of_daily_turnover"] * turnover:
        notes.append(f"position is {float(h.value) / turnover:.0%} of a typical day's traded value: slow to exit")

    alt = best_alternative(db, stock, h.stock_id)
    better, why_better = (clearly_better(v, row.classification, alt) if alt else (False, "no same-sector stock passes the core gate"))
    comparison = None
    if alt:
        comparison = {"candidate": alt["symbol"], "candidate_name": alt["company_name"], "candidate_classification": alt["classification"],
                      "candidate_action": alt["action"], "clearly_better": better, "why": why_better,
                      "better_company": (alt.get("quality") or 0) > (v.get("quality") or 0),
                      "better_opportunity": (opportunity(alt) or 0) > (opportunity(v) or 0),
                      "scores": {k: {"held": v.get(k), "candidate": alt.get(k)} for k in
                                 ("quality", "fundamental", "quantitative", "relative_strength", "technical", "valuation")}}

    action, reason = row.action or "Watch", "; ".join(decision.get("why") or [])
    if row.classification in ("Replacement Candidate", "Avoid"):
        if better:
            action, reason = "Replace", f"replace with {alt['symbol']}: {why_better}"
        elif row.classification == "Avoid":
            action, reason = "Reduce", "fails the quality gate and is declining; no clearly better same-sector replacement found"
        else:
            action, reason = "Watch", "below the gate, but no clearly better same-sector replacement: keep and watch"
    elif weight > cfg["max_stock_pct"]:
        action, reason = "Reduce", f"{weight:.1f}% of the equity book is above the {cfg['max_stock_pct']:.0f}% limit per stock"
    elif action in ("Add gradually", "Add on confirmation"):
        if band and weight >= band[1]:
            action, reason = "Hold", f"already at the {size.lower()} size ({weight:.1f}% against {band[0]:.0f}-{band[1]:.0f}%)"
        elif sector_pct.get(sector, 0) >= cfg["max_sector_pct"]:
            action, reason = "Hold", f"{sector} is already {sector_pct[sector]:.0f}% of the equity book (limit {cfg['max_sector_pct']:.0f}%)"
        elif better:
            reason += f"; {alt['symbol']} is the better opportunity in the sector for new money"
    add_value = None
    if action in ("Add gradually", "Add on confirmation") and band and equity_book:
        add_value = round(max(0.0, (band[0] + band[1]) / 2 - weight) / 100 * equity_book, 0)
    return {
        "framework": {**v, "classification": row.classification, "action": row.action, "size": decision.get("size"),
                      "matrix": decision.get("matrix")},
        "sector": sector, "sector_pct_of_equity": sector_pct.get(sector),
        "size_after_checks": size, "target_band_pct": band, "add_value_to_band_mid": add_value, "notes": notes,
        "correlation_with_rest": corr_rest and round(corr_rest, 2),
        "most_correlated_holding": closest and {"stock_id": closest[0], "correlation": round(closest[1], 2)},
        "median_daily_traded_value": turnover and round(turnover, 0),
        "comparison": comparison, "final_action": action, "final_reason": reason,
    }


def candidates(db: Session, holdings: list[PortfolioHolding], cfg: dict, sector_pct: dict, limit: int = 12) -> list[dict]:
    """Stocks not owned that pass the core gate and are ready to buy, outside
    sectors already at the limit — each set against the weakest holding in
    its sector, if any (section 12: is it better than what I already own?)."""
    owned = {h.stock_id for h in holdings if h.stock_id}
    held_rows = {sid: store.latest(db, sid) for sid in owned}
    rows = (db.query(FrameworkScore, Stock).join(Stock, Stock.id == FrameworkScore.stock_id)
            .filter(FrameworkScore.classification.in_(("Core Quality", "Investable")),
                    FrameworkScore.action.in_(("Add gradually", "Add on confirmation")), Stock.is_active.is_(True)).all())
    latest: dict[str, tuple] = {}
    for r, s in rows:
        if s.id in owned:
            continue
        if s.id not in latest or r.as_of > latest[s.id][0].as_of or (r.as_of == latest[s.id][0].as_of and r.basis == store.FULL):
            latest[s.id] = (r, s)
    out, per_sector = [], {}
    for r, s in sorted(latest.values(), key=lambda x: (_READY[x[0].action], -(float(x[0].quality or 0)))):
        if sector_pct.get(s.sector or "", 0) >= cfg["max_sector_pct"] or per_sector.get(s.sector, 0) >= 3:
            continue  # sector already at its limit, or three candidates from it already listed
        per_sector[s.sector] = per_sector.get(s.sector, 0) + 1
        v = values(r)
        same = [(sid, hr) for sid, hr in held_rows.items() if hr is not None and (db.get(Stock, sid).sector == s.sector)]
        vs = None
        if same:
            weakest_id, weakest = min(same, key=lambda x: float(x[1].quality or 0))
            ok, why = clearly_better(values(weakest), weakest.classification, {**v, "classification": r.classification})
            vs = {"holding": db.get(Stock, weakest_id).symbol, "clearly_better": ok, "why": why}
        out.append({"symbol": s.symbol, "company_name": s.company_name, "sector": s.sector, "classification": r.classification,
                    "action": r.action, "size": ((r.detail or {}).get("decision") or {}).get("size"), **v,
                    "sector_pct_of_equity": sector_pct.get(s.sector or ""), "vs_weakest_holding_in_sector": vs})
        if len(out) >= limit:
            break
    return out
