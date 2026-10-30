"""AMFI's daily NAV file: value and classify mutual-fund holdings by ISIN.

Source: https://portal.amfiindia.com/spages/NAVAll.txt — every scheme of
every Indian mutual fund, published each business day, free and unthrottled
(about 1.5 MB). Layout: a category heading line ("Open Ended Schemes(Debt
Scheme - Liquid Fund)"), a fund-house line, then one line per scheme:

    code;ISIN payout/growth;ISIN reinvestment;name;[plan;option;]NAV;date

(the plan and option columns were added in 2026; both layouts are read).

Asset class from AMFI's own category heading, so a fund is classed by what
SEBI's scheme category says it is, not by words in its name:

    gold / silver ETFs and funds                         GOLD
    overseas fund of funds, ETFs investing overseas      INTERNATIONAL
    debt / income / gilt / liquid / money market /
      overnight schemes, debt index funds and ETFs,
      arbitrage funds, conservative hybrid funds         DEBT
    equity schemes, equity ETFs and index funds, other
      hybrid funds (aggressive, balanced advantage,
      equity savings, multi asset), solution oriented    EQUITY_FUND
    headings that do not say (other ETFs, index funds,
      domestic fund of funds)                            from the scheme name
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import AmfiNav

URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
_ISIN = re.compile(r"^IN[A-Z0-9]{10}$")


def classify(category: str, name: str) -> tuple[str, str]:
    """(asset class, how it was decided)."""
    from app.portfolio.importers import classify_fund

    inner = category[category.find("(") + 1:].rstrip(")") if "(" in category else category
    c = inner.lower()
    basis = f"AMFI category: {inner}"
    if "gold" in c or "silver" in c:
        return "GOLD", basis
    if "overseas" in c:
        return "INTERNATIONAL", basis
    if any(w in c for w in ("debt", "income", "gilt", "liquid", "money market", "overnight", "arbitrage", "conservative hybrid",
                            "floating", "credit risk", "corporate bond", "banking and psu", "duration", "short term", "long term")):
        return "DEBT", basis
    if "equity" in c or "hybrid" in c or "solution oriented" in c or "retirement" in c or "children" in c or "life cycle" in c \
            or any(w in c for w in ("large cap", "mid cap", "small cap", "flexi", "multi cap", "elss", "value", "thematic", "sectoral",
                                    "focused", "dividend yield", "contra")):
        return "EQUITY_FUND", basis
    return classify_fund(name), f"{basis}; class read from the scheme name"


def parse(text: str) -> list[dict]:
    rows, category, house = [], None, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("Scheme Code"):
            continue
        if ";" not in line:
            if re.search(r"schemes?\s*\(|schemes?$", line, re.I) and ("(" in line or "scheme" in line.lower()):
                category, house = line, None
            else:
                house = line
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) == 8:
            code, isin1, isin2, name, plan, option, nav, day = parts
            name = " - ".join(x for x in (name, plan, option) if x and x != "-")
        elif len(parts) == 6:
            code, isin1, isin2, name, nav, day = parts
        else:
            continue
        try:
            nav_v = float(nav)
        except ValueError:
            nav_v = None
        try:
            day_v = datetime.strptime(day, "%d-%b-%Y").date()
        except ValueError:
            day_v = None
        cls, basis = classify(category or "", name)
        for isin in {isin1, isin2}:
            if _ISIN.match(isin or ""):
                rows.append({"isin": isin, "scheme_code": code, "scheme_name": name[:300], "fund_house": house,
                             "category": category or "unknown", "asset_class": cls, "class_basis": basis[:300],
                             "nav": nav_v, "nav_date": day_v})
    return rows


def refresh(db: Session) -> dict:
    """Download and store today's file. Raises on a network failure (the caller reports it)."""
    r = httpx.get(URL, timeout=60, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    rows = {x["isin"]: x for x in parse(r.text)}
    now = datetime.now(timezone.utc)
    items = [{**x, "retrieved_at": now} for x in rows.values()]
    for i in range(0, len(items), 2000):
        stmt = insert(AmfiNav).values(items[i:i + 2000])
        db.execute(stmt.on_conflict_do_update(index_elements=["isin"], set_={
            c: stmt.excluded[c] for c in ("scheme_code", "scheme_name", "fund_house", "category", "asset_class", "class_basis",
                                          "nav", "nav_date", "retrieved_at")}))
    db.commit()
    latest = max((x["nav_date"] for x in items if x["nav_date"]), default=None)
    return {"isins": len(items), "nav_date": latest.isoformat() if latest else None}


def ensure_fresh(db: Session, max_age_hours: float = 20) -> dict | None:
    """Refresh when the stored file is older than `max_age_hours`; None when it is fresh."""
    seen = db.query(func.max(AmfiNav.retrieved_at)).scalar()
    if seen and datetime.now(timezone.utc) - seen < timedelta(hours=max_age_hours):
        return None
    return refresh(db)


def lookup(db: Session, isin: str | None) -> AmfiNav | None:
    if not isin:
        return None
    return db.get(AmfiNav, isin.strip().upper())


def stale(nav_date: date | None, today: date | None = None) -> bool:
    """A NAV more than five days old (a closed or matured scheme)."""
    return nav_date is None or ((today or date.today()) - nav_date).days > 5
