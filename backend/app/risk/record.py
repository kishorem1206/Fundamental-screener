"""A stock's regulatory record, as the framework uses it, and its credit ratings, as the report shows them.

Regulatory record (SEBI orders over the last three years)
  Each order matched to the company is graded:
    SERIOUS  a whole-time member / quasi-judicial order (FINAL, INTERIM,
             ORDER) in the company's own matter with restraint directions
             (on the company or on those running it: an order titled for the
             company, debarring its promoters, is a governance event either
             way), or disgorgement or a penalty of ₹1 crore or more on the
             company itself                                         15 points
    PENALTY  a smaller penalty on the company, or directions to comply
             (no restraint)                                            6
    MATTER   directions or penalties on others (promoters, directors,
             traders) in the company's matter, not on the company      4
             (8 at most in all: many orders against individuals in one
             insider-trading case are one case)
    SETTLED  a settlement order in the company's matter                3
             (6 at most in all)
    NOTE     shown only: trading in the company's shares (SCRIP),
             exemption / revocation orders, orders disposed of without
             directions, orders not yet read                           0
  The points (at most 20) are taken off the Business Quality score. A
  SERIOUS order within 24 months is a governance red flag: it caps Quality at
  49 (the same rule as a promoter pledge) and fails the core gate.

Credit ratings (rating letters filed with NSE) are reported, never scored:
`credit_for_stock` feeds the full analysis report only. By the user's decision
of 2026-10-30 they touch no score, gate, flag or classification.

The regulatory record is point in time: `as_of` sees only orders dated by then.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.database.models import CreditRating, SebiOrder, SebiOrderMatch

WINDOW_DAYS = 3 * 365
FLAG_DAYS = 2 * 365
POINTS = {"SERIOUS": 15, "PENALTY": 6, "MATTER": 4, "SETTLED": 3, "NOTE": 0}
MAX_DEDUCTION = 20
SERIOUS_PENALTY_RS = 1e7
_SERIOUS_KINDS = ("FINAL", "INTERIM", "ORDER")
GRADE_CAPS = {"MATTER": 8, "SETTLED": 6}


def grade(kind: str, outcome: str | None, role: str, company_in_operative: bool | None, penalty_rs: float | None = None) -> str:
    if role == "SCRIP" or kind in ("EXEMPTION", "REVOCATION", "CORRIGENDUM", "RTI_APPEAL", "RECOVERY", "COURT", "OTHER"):
        return "NOTE"
    if kind == "SETTLEMENT":
        return "SETTLED"
    if outcome not in ("DIRECTIONS", "DISGORGEMENT", "PENALTY", "COMPLIANCE"):
        return "NOTE"
    if role == "MATTER":
        return "MATTER"
    if outcome == "DIRECTIONS" and kind in _SERIOUS_KINDS and (role == "NAMED" or company_in_operative):
        return "SERIOUS"
    if not company_in_operative:
        return "MATTER"
    if kind in _SERIOUS_KINDS and (outcome == "DISGORGEMENT" or (outcome == "PENALTY" and (penalty_rs or 0) >= SERIOUS_PENALTY_RS)):
        return "SERIOUS"
    return "PENALTY"


def _earliest_order(db: Session) -> date | None:
    return db.query(func.min(SebiOrder.order_date)).scalar()


def regulatory_record(rows: list[tuple[SebiOrder, SebiOrderMatch]], as_of: date, earliest: date | None) -> dict:
    """`rows`: this stock's (order, match) pairs; `earliest`: the oldest order stored at all."""
    start = as_of - timedelta(days=WINDOW_DAYS)
    if earliest is None or earliest > start + timedelta(days=31):
        return {"measured": False, "reason": "SEBI orders not read back three years (python -m app.risk.runner --sebi)",
                "orders": [], "deduction": 0, "red_flag": None}
    orders, deduction, flag = [], 0, None
    by_grade: dict[str, int] = {}
    for o, m in sorted(rows, key=lambda r: r[0].order_date, reverse=True):
        if not (start <= o.order_date <= as_of):
            continue
        penalty = float(o.penalty_rs) if o.penalty_rs is not None else None
        g = grade(o.kind, o.outcome, m.role, m.company_in_operative, penalty)
        points = min(POINTS[g], GRADE_CAPS.get(g, 10**6) - by_grade.get(g, 0))
        by_grade[g] = by_grade.get(g, 0) + points
        deduction += points
        orders.append({"date": o.order_date.isoformat(), "title": o.title, "kind": o.kind, "outcome": o.outcome, "penalty_rs": penalty,
                       "role": m.role, "company_named": m.company_in_operative, "grade": g, "points": points,
                       "url": o.url, "pdf_url": o.pdf_url})
        if g == "SERIOUS" and flag is None and o.order_date >= as_of - timedelta(days=FLAG_DAYS):
            what = {"DIRECTIONS": "restraint directions", "DISGORGEMENT": "disgorgement"}.get(o.outcome) or f"penalty ₹{(penalty or 0) / 1e7:,.2f} crore"
            flag = f"SEBI order {o.order_date.isoformat()} ({what}): {o.title[:120]}"
    return {"measured": True, "window": f"{start.isoformat()} to {as_of.isoformat()}", "orders": orders,
            "deduction": min(MAX_DEDUCTION, deduction), "red_flag": flag, "source": "SEBI enforcement orders (sebi.gov.in)"}


def _row(r: CreditRating, excerpt: bool = True) -> dict:
    return {"date": r.announced_on.isoformat(), "agency": r.agency, "instrument": r.instrument, "rating": r.rating,
            "short_term": r.short_term, "outlook": r.outlook, "action": r.action, "previous_rating": r.previous_rating,
            "previous_outlook": r.previous_outlook, "parsed": r.parsed, "filing_url": r.filing_url,
            "rationale_url": r.rationale_url, **({"excerpt": r.excerpt} if excerpt else {})}


def credit_status(rows: list[CreditRating], as_of: date) -> dict:
    """What the agencies say, for the report. Facts only: nothing here is judged."""
    start = as_of - timedelta(days=WINDOW_DAYS)
    rows = sorted((r for r in rows if start <= r.announced_on <= as_of), key=lambda r: r.announced_on)
    readable = [r for r in rows if r.parsed]
    latest: dict[str, CreditRating] = {}
    for r in readable:
        if r.agency:
            latest[r.agency] = r
    return {"letters": len(rows), "read": len(readable), "current": _row(readable[-1]) if readable else None,
            "by_agency": {a: _row(r, excerpt=False) for a, r in latest.items()},
            "history": [_row(r, excerpt=False) for r in reversed(rows[-12:])],
            "source": "credit rating letters filed with NSE"}


def credit_for_stock(db: Session, stock_id: str, as_of: date | None = None) -> dict:
    ratings = db.query(CreditRating).filter(CreditRating.stock_id == stock_id).all()
    return credit_status(ratings, as_of or date.today())


def for_stock(db: Session, stock_id: str, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    pairs = (db.query(SebiOrder, SebiOrderMatch).join(SebiOrderMatch, SebiOrderMatch.order_url == SebiOrder.url)
             .filter(SebiOrderMatch.stock_id == stock_id).all())
    return {"regulatory": regulatory_record(pairs, as_of, _earliest_order(db))}


def for_all(db: Session, stock_ids: set[str], as_of: date | None = None) -> dict[str, dict]:
    """Same as for_stock for many stocks, in two queries."""
    as_of = as_of or date.today()
    earliest = _earliest_order(db)
    pairs: dict[str, list] = {}
    for o, m in db.query(SebiOrder, SebiOrderMatch).join(SebiOrderMatch, SebiOrderMatch.order_url == SebiOrder.url):
        pairs.setdefault(m.stock_id, []).append((o, m))
    return {sid: {"regulatory": regulatory_record(pairs.get(sid, []), as_of, earliest)} for sid in stock_ids}
