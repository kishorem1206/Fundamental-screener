"""Valuation Score — "is the current price reasonable?" (framework section 8).
Higher means cheaper. Used after quality and fundamentals; a cheap price never
repairs a weak business (the decision engine applies that rule, phase 9).

How market value is measured: Screener's market cap on the day it was read,
moved to the as-of date with the stored split-adjusted close, so share-count
quirks (splits, bonuses) cannot distort a ratio. Earnings are the last four
quarters' net profit from Screener (consolidated first); book value is
Screener's latest net worth.

  P/E vs own history      today's P/E against the P/E at each quarter end of the
                          last three years (as far back as the price store goes)
  P/E vs sector           percentile among same-sector stocks with profits
  PEG                     P/E divided by three-year profit growth (Screener)
  EV/EBITDA               Yahoo's figure (Screener shows no enterprise value)
  free-cash-flow yield    Screener free cash flow of the latest year / market cap
  deep report value       the deep report's blended value per share against the
                          price, where that report has been built
For a lender, P/B against its own history and its sector lead, with P/E second.

"Sector" for the multiples is the stock's industry when it has at least eight
listed peers (banks against banks, not against NBFCs and brokers), otherwise
its sector. A quarter that dwarfs the other three (a one-off gain or loss) is
left out of trailing profit and the other three are annualised.

Earnings yield is not scored separately: it is the inverse of P/E.
"""
from __future__ import annotations

import statistics
from datetime import date, timedelta
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.calculations.scoring import VALUATION_SCORE_CONFIG, _score_metric
from app.framework.screener_series import cagr

_WEIGHTS = {"pe_vs_history": 0.25, "pe_vs_sector": 0.20, "peg": 0.15, "ev_ebitda": 0.10, "fcf_yield": 0.15, "deep_report": 0.15}
_WEIGHTS_LENDER = {"pb_vs_history": 0.25, "pb_vs_sector": 0.20, "pe_vs_history": 0.15, "pe_vs_sector": 0.15, "peg": 0.10,
                   "deep_report": 0.15}
_PEG = [(0.5, 95), (1.0, 80), (1.5, 60), (2.0, 45), (3.0, 25), (5.0, 5)]
_UPSIDE = [(-40, 5), (-20, 25), (0, 50), (20, 75), (40, 95), (60, 100)]
_MIN_POINTS = 6


def view(score: float | None) -> str | None:
    if score is None:
        return None
    return "CHEAP" if score >= 65 else "FAIR" if score >= 40 else "EXPENSIVE"


INTERPRETATION = {  # section 8, keyed by (quality is strong, valuation view)
    (True, "EXPENSIVE"): "good business, poor entry price",
    (True, "FAIR"): "investable if other conditions support",
    (True, "CHEAP"): "potential high-conviction candidate",
    (False, "CHEAP"): "possible value trap",
    (False, "EXPENSIVE"): "usually avoid",
    (False, "FAIR"): "fair price for a weaker business",
}


@lru_cache(maxsize=4)
def _universe(end: date) -> dict[str, dict]:
    """{stock_id: {"mcap": crore at `end`, "mcap_source", "ttm_profit", "pe", "quarters": {period: profit}}}"""
    from app.infrastructure.database.client import get_db

    db = get_db()
    try:
        profits: dict[str, dict[str, dict[str, float]]] = {}
        for sid, basis, period, value in db.execute(text(
                "select company_id, statement_type, period, value from fa_metric_data_points "
                "where metric_key = 'qtr_net_profit' and source = 'SCREENER' and value is not null "
                "order by retrieved_at desc")):
            if len(period) == 10:
                profits.setdefault(sid, {}).setdefault(basis, {}).setdefault(period, float(value))
        last_close = dict(db.execute(text(
            "select distinct on (stock_id) stock_id, close from price_bars_daily where bar_date <= :d and bar_date > :f "
            "order by stock_id, bar_date desc"), {"d": end, "f": end - timedelta(days=10)}).all())
        sr = db.execute(text(
            "select m.company_id, m.value, (select p.close from price_bars_daily p where p.stock_id = m.company_id "
            "  and p.bar_date <= m.period::date order by p.bar_date desc limit 1) "
            "from (select distinct on (company_id) company_id, value, period from fa_metric_data_points "
            "      where metric_key = 'sr_market_cap' and source = 'SCREENER' order by company_id, period desc, retrieved_at desc) m"))
        caps = {sid: (float(v), float(c) if c else None, "Screener market cap") for sid, v, c in sr}
        for sid, mcap, updated in db.execute(text(
                "select s.id, s.market_cap, s.updated_at::date from stocks s where s.is_active and s.market_cap is not null")):
            if sid not in caps:
                c = db.execute(text("select close from price_bars_daily where stock_id = :s and bar_date <= :d "
                                    "order by bar_date desc limit 1"), {"s": sid, "d": updated}).scalar()
                caps[sid] = (float(mcap) / 1e7, float(c) if c else None, "stocks table market cap")
        out = {}
        for sid, (cap, close_then, source) in caps.items():
            now = last_close.get(sid)
            if not now or not close_then:
                continue
            mcap = cap * float(now) / close_then
            by_basis = profits.get(sid, {})
            quarters = by_basis.get("CONSOLIDATED") if len(by_basis.get("CONSOLIDATED", {})) >= 4 else by_basis.get("STANDALONE", {})
            qs = sorted(quarters or {})
            ttm, note = core_ttm([quarters[p] for p in qs[-4:]]) if len(qs) >= 4 else (None, None)
            out[sid] = {"mcap": mcap, "mcap_source": source, "ttm_profit": ttm, "ttm_note": note, "quarters": quarters or {},
                        "pe": mcap / ttm if ttm and ttm > 0 else None}
        return out
    finally:
        db.close()


def core_ttm(last_four: list[float]) -> tuple[float, str | None]:
    """Four quarters' profit, unless one quarter dwarfs the other three (a
    one-off gain or loss): then the other three, annualised, with a note."""
    if len(last_four) != 4:
        raise ValueError("need four quarters")
    total = sum(last_four)
    for i, q in enumerate(last_four):
        rest = last_four[:i] + last_four[i + 1:]
        if abs(q) > 2 * sum(abs(r) for r in rest) and abs(q) > 0.5 * abs(total):
            return sum(rest) * 4 / 3, f"one quarter ({q:,.0f} cr) left out as a one-off; the other three annualised"
    return total, None


def universe(end: date) -> dict[str, dict]:
    return _universe(end)


def _percentile(value: float, population: list[float]) -> float:
    return 100 * (sum(1 for p in population if p < value) + 0.5 * sum(1 for p in population if p == value)) / len(population)


def _history(db: Session, stock_id: str, me: dict, end: date, series: dict, field: str) -> list[tuple[str, float]]:
    """P/E (field="pe") or P/B (field="pb") at each quarter end of the stored price history."""
    closes = dict(db.execute(text("select bar_date, close from price_bars_daily where stock_id = :s and bar_date <= :d"),
                             {"s": stock_id, "d": end}).all())
    if not closes:
        return []
    days = sorted(closes)
    now_close = float(closes[days[-1]])
    qs = sorted(me["quarters"])
    out = []
    for i, q in enumerate(qs):
        qd = date.fromisoformat(q)
        if qd < days[0] or qd > end:
            continue
        on = [d for d in days if d <= qd]
        if not on:
            continue
        mcap = me["mcap"] * float(closes[on[-1]]) / now_close
        if field == "pe":
            if i < 3:
                continue
            ttm, _ = core_ttm([me["quarters"][p] for p in qs[i - 3:i + 1]])
            if ttm > 0:
                out.append((q, mcap / ttm))
        else:
            years = [y for y in series.get("years") or [] if y <= q and (series["rows"][y].get("net_worth") or 0) > 0]
            if years:
                out.append((q, mcap / series["rows"][years[-1]]["net_worth"]))
    return out


def _vs_history(name: str, current: float | None, hist: list[tuple[str, float]]) -> dict:
    if current is None:
        return {"score": None, "reason": f"no current {name} (loss-making or no data)"}
    points = [v for _, v in hist]
    if len(points) < _MIN_POINTS:
        return {"score": None, "reason": f"fewer than {_MIN_POINTS} quarter-end {name} readings"}
    pct = _percentile(current, points)
    return {"score": round(100 - pct, 1), f"current_{name.lower()}": round(current, 1),
            f"median_{name.lower()}": round(statistics.median(points), 1), "percentile_in_own_history": round(pct, 1),
            "from": hist[0][0], "to": hist[-1][0], "readings": len(points)}


def _vs_sector(name: str, current: float | None, peers: list[float], sector: str | None) -> dict:
    if current is None:
        return {"score": None, "reason": f"no current {name} (loss-making or no data)"}
    if len(peers) < 5:
        return {"score": None, "reason": f"fewer than 5 same-sector stocks with a {name}"}
    pct = _percentile(current, peers)
    return {"score": round(100 - pct, 1), f"current_{name.lower()}": round(current, 1),
            f"sector_median_{name.lower()}": round(statistics.median(peers), 1), "percentile_in_sector": round(pct, 1),
            "sector": sector, "peers": len(peers)}


def _deep_report(db: Session, stock_id: str, price: float | None) -> dict:
    row = db.execute(text(
        "select value_num, created_at::date from bie_facts where company_id = :s and fact_type = 'valuation' "
        "and key = 'average_value_per_share' and dimension = 'Base' order by created_at desc limit 1"), {"s": stock_id}).first()
    if not row or not price:
        return {"score": None, "reason": "deep report valuation not built for this company"}
    value = float(row[0])
    upside = (value / price - 1) * 100
    return {"score": round(_score_metric(upside, _UPSIDE), 1), "value_per_share": round(value, 2), "price": round(price, 2),
            "upside_pct": round(upside, 1), "valued_on": row[1].isoformat(), "source": "deep report (DCF, sum of the parts, peer multiple)"}


def compute_valuation(db: Session, stock_id: str, series: dict, metrics: dict, lender: bool, end: date | None,
                      sector: str | None, sector_ids: list[str]) -> dict:
    if end is None:
        return {"score": None, "reason": "no stored prices", "components": {}}
    table = universe(end)
    me = table.get(stock_id)
    if not me:
        return {"score": None, "reason": "no market cap or price on record", "components": {}}
    price = db.execute(text("select close from price_bars_daily where stock_id = :s and bar_date <= :d order by bar_date desc limit 1"),
                       {"s": stock_id, "d": end}).scalar()
    pe = me["pe"]
    peer_pe = [table[s]["pe"] for s in sector_ids if s in table and table[s]["pe"]]
    profit_growth = cagr(series, "net_profit", 3) if series.get("years") else None
    parts = {
        "pe_vs_history": _vs_history("PE", pe, _history(db, stock_id, me, end, series, "pe")),
        "pe_vs_sector": _vs_sector("PE", pe, peer_pe, sector),
        "peg": ({"score": round(_score_metric(pe / profit_growth, _PEG), 1), "peg": round(pe / profit_growth, 2),
                 "profit_growth_3y_pct": round(profit_growth, 1)} if pe and profit_growth and profit_growth > 0
                else {"score": None, "reason": "no profit growth over three years, or no P/E"}),
        "deep_report": _deep_report(db, stock_id, float(price) if price else None),
    }
    if lender:
        nw_years = [y for y in series.get("years") or [] if (series["rows"][y].get("net_worth") or 0) > 0]
        pb = me["mcap"] / series["rows"][nw_years[-1]]["net_worth"] if nw_years else None
        parts["pb_vs_history"] = _vs_history("PB", pb, _history(db, stock_id, me, end, series, "pb"))
        parts["pb_vs_sector"] = _pb_vs_sector(db, pb, sector_ids, table, sector)
    else:
        ev = metrics.get("ev_to_ebitda")
        parts["ev_ebitda"] = ({"score": round(_score_metric(ev, VALUATION_SCORE_CONFIG["ev_ebitda_inv"]), 1), "ev_to_ebitda": round(ev, 1),
                               "source": "Yahoo (Screener shows no enterprise value)"} if ev and ev > 0
                              else {"score": None, "reason": "no positive EV/EBITDA"})
        parts["fcf_yield"] = _fcf_yield(series, me, metrics)
    weights = _WEIGHTS_LENDER if lender else _WEIGHTS
    for name, part in parts.items():
        part["weight"] = weights[name]
    scored = {n: p for n, p in parts.items() if p.get("score") is not None}
    covered = sum(p["weight"] for p in scored.values())
    score = round(sum(p["score"] * p["weight"] for p in scored.values()) / covered, 1) if covered >= 0.4 else None
    reason = None if score is not None else "too few valuation measures apply (often a loss-maker: no P/E, PEG or EV/EBITDA)"
    return {"score": score, "view": view(score), "coverage": round(covered, 3), "components": parts,
            **({"reason": reason} if reason else {}),
            "market_cap_cr": round(me["mcap"], 1), "market_cap_source": me["mcap_source"],
            "ttm_profit_cr": me["ttm_profit"] and round(me["ttm_profit"], 1), "ttm_note": me.get("ttm_note"),
            "pe": pe and round(pe, 1), "as_of": end.isoformat()}


def _pb_vs_sector(db: Session, pb: float | None, sector_ids: list[str], table: dict, sector: str | None) -> dict:
    if pb is None:
        return {"score": None, "reason": "no positive net worth on record"}
    rows = db.execute(text(
        "select distinct on (company_id) company_id, value from fa_metric_data_points where metric_key = 'reserves' "
        "and source = 'SCREENER' and company_id = any(:ids) order by company_id, period desc, retrieved_at desc"),
        {"ids": sector_ids}).all()
    capital = dict(db.execute(text(
        "select distinct on (company_id) company_id, value from fa_metric_data_points where metric_key = 'equity_capital' "
        "and source = 'SCREENER' and company_id = any(:ids) order by company_id, period desc, retrieved_at desc"),
        {"ids": sector_ids}).all())
    peers = []
    for sid, reserves in rows:
        nw = float(reserves) + float(capital.get(sid) or 0)
        if sid in table and nw > 0:
            peers.append(table[sid]["mcap"] / nw)
    return _vs_sector("PB", pb, peers, sector)


def _fcf_yield(series: dict, me: dict, metrics: dict) -> dict:
    years = [y for y in series.get("years") or [] if series["rows"][y].get("fcf") is not None]
    if years and me["mcap"]:
        y = series["rows"][years[-1]]["fcf"] / me["mcap"] * 100
        return {"score": round(_score_metric(y, VALUATION_SCORE_CONFIG["fcf_yield"]), 1), "fcf_yield_pct": round(y, 2),
                "year": years[-1][:4], "source": "Screener free cash flow of the latest year / market cap"}
    y = metrics.get("fcf_yield")
    if y is None:
        return {"score": None, "reason": "no free cash flow on record"}
    return {"score": round(_score_metric(y, VALUATION_SCORE_CONFIG["fcf_yield"]), 1), "fcf_yield_pct": round(y, 2), "source": "Yahoo"}
