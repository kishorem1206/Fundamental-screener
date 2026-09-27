"""NSE shareholding-pattern ingestion — Architecture v2 Stage 3, the
governance/integrity layer's data source.

Two NSE calls per quarter, both confirmed reachable live (2026-09-11):
  1. `/api/corporate-share-holdings-master?index=equities&symbol=X` — a
     summary list, one row per submitted quarter, giving `pr_and_prgrp`
     (promoter + promoter group %) and `public_val` (public %) directly as
     JSON — no parsing needed.
  2. Each row links an `xbrl` URL — the actual SEBI shareholding-pattern
     XBRL filing for that quarter. Promoter/public % could be read from
     here too, but pledge % (`EncumberedShareUnderPledgedAsPercentageOf-
     TotalNumberOfShares`, `in-bse-shp` taxonomy) is NOT in the summary
     JSON at all — it only exists inside this XBRL document, at the
     `ShareholdingOfPromoterAndPromoterGroup_ContextI` context (the
     promoter-group aggregate, not the many per-shareholder-type rows the
     same tag also appears under). A plain regex extraction is enough here
     — no XBRL-aware library needed, since this is the one tag+context
     pair this module cares about, not a general XBRL parser.

Sector-agnostic by design (shareholding pattern is filed by every listed
company, not just banks) — reuses nse_client's session bootstrap since it's
the same NSE cookie requirement, not a different site.
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.ingestion import nse_client
from app.infrastructure.database.models import GovernanceEvent, Shareholding
from app.logger import logger

API_URL = "https://www.nseindia.com/api/corporate-share-holdings-master"

_PLEDGE_CONTEXT = "ShareholdingOfPromoterAndPromoterGroup_ContextI"
_PLEDGE_TAG_RE = re.compile(
    r'<in-bse-shp:EncumberedShareUnderPledgedAsPercentageOfTotalNumberOfShares'
    r'[^>]*contextRef="' + _PLEDGE_CONTEXT + r'"[^>]*>([^<]*)</in-bse-shp:EncumberedShareUnderPledgedAsPercentageOfTotalNumberOfShares>'
)

# A promoter-holding drop of at least this many percentage points in one
# quarter triggers PROMOTER_HOLDING_DECLINE.
_DECLINE_THRESHOLD = 1.0


def _parse_period(date_str: str) -> str:
    """"30-JUN-2026" -> "2026-06-30"."""
    return datetime.strptime(date_str.strip(), "%d-%b-%Y").date().isoformat()


def _to_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def fetch_shareholding_history(symbol: str, session=None, quarters: int = 8) -> list[dict]:
    """Latest `quarters` shareholding-pattern rows for `symbol`, newest first."""
    s = session or nse_client._session()
    r = s.get(API_URL, params={"index": "equities", "symbol": symbol}, timeout=20)
    r.raise_for_status()
    rows = r.json() or []
    rows.sort(key=lambda row: row.get("date", ""), reverse=True)
    return rows[:quarters]


def _fetch_pledge_pct(xbrl_url: str, session) -> float | None:
    try:
        r = session.get(xbrl_url, timeout=20, headers={"Referer": nse_client.BOOTSTRAP_URL})
        r.raise_for_status()
        text = r.content.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning("shareholding_client: xbrl fetch failed", url=xbrl_url, error=str(e))
        return None
    m = _PLEDGE_TAG_RE.search(text)
    if not m or not m.group(1).strip():
        return None
    try:
        return round(float(m.group(1)) * 100, 3)
    except ValueError:
        return None


def _detect_events(company_id: str, rows_asc: list[Shareholding]) -> list[dict]:
    """Deterministic, evidence-backed flags — never an inferred conclusion.
    `rows_asc` must be chronologically ascending (oldest first)."""
    events = []
    for prev, curr in zip(rows_asc, rows_asc[1:]):
        if prev.promoter_pct is not None and curr.promoter_pct is not None:
            delta = float(curr.promoter_pct) - float(prev.promoter_pct)
            if delta <= -_DECLINE_THRESHOLD:
                severity = "HIGH" if delta <= -3 else "MEDIUM"
                events.append({
                    "event_type": "PROMOTER_HOLDING_DECLINE", "severity": severity,
                    "event_date": curr.period_end,
                    "description": (
                        f"Promoter holding fell from {prev.promoter_pct}% ({prev.period_end}) "
                        f"to {curr.promoter_pct}% ({curr.period_end}), a {abs(delta):.2f} "
                        f"percentage-point drop in one quarter."
                    ),
                    "evidence": {
                        "prior_period": prev.period_end, "prior_promoter_pct": float(prev.promoter_pct),
                        "current_period": curr.period_end, "current_promoter_pct": float(curr.promoter_pct),
                        "change_pct_points": round(delta, 3),
                    },
                })
        if curr.pledge_pct is not None and float(curr.pledge_pct) > 0:
            pledge = float(curr.pledge_pct)
            severity = "HIGH" if pledge > 50 else "MEDIUM" if pledge > 10 else "LOW"
            events.append({
                "event_type": "PLEDGE_PRESENT", "severity": severity,
                "event_date": curr.period_end,
                "description": f"{pledge}% of promoter shareholding is pledged/encumbered as of {curr.period_end}.",
                "evidence": {"period": curr.period_end, "pledge_pct": pledge},
            })
            if prev.pledge_pct is not None and pledge > float(prev.pledge_pct):
                events.append({
                    "event_type": "PLEDGE_INCREASE", "severity": severity,
                    "event_date": curr.period_end,
                    "description": (
                        f"Promoter pledge increased from {prev.pledge_pct}% ({prev.period_end}) "
                        f"to {pledge}% ({curr.period_end})."
                    ),
                    "evidence": {
                        "prior_period": prev.period_end, "prior_pledge_pct": float(prev.pledge_pct),
                        "current_period": curr.period_end, "current_pledge_pct": pledge,
                    },
                })
    return events


def ingest_shareholding(db: Session, company_id: str, symbol: str, quarters: int = 8) -> dict:
    """Fetch, store, and detect governance events from `symbol`'s recent
    shareholding-pattern history. Never raises — logs and returns empty
    results on failure, matching every other ingestion path's contract."""
    try:
        session = nse_client._session()
        rows = fetch_shareholding_history(symbol, session=session, quarters=quarters)
    except Exception as e:
        logger.warning("shareholding_client: fetch failed", symbol=symbol, error=str(e))
        return {"shareholding_rows": 0, "events": 0}

    now = datetime.now(timezone.utc)
    stored: list[Shareholding] = []
    for row in rows:
        try:
            period_end = _parse_period(row["date"])
        except (KeyError, ValueError):
            continue
        promoter_pct = _to_float(row.get("pr_and_prgrp"))
        public_pct = _to_float(row.get("public_val"))
        pledge_pct = _fetch_pledge_pct(row["xbrl"], session) if row.get("xbrl") else None

        existing = db.query(Shareholding).filter_by(company_id=company_id, period_end=period_end).first()
        if existing:
            existing.promoter_pct = promoter_pct
            existing.public_pct = public_pct
            existing.pledge_pct = pledge_pct
            existing.source_url = row.get("xbrl")
            existing.retrieved_at = now
            stored.append(existing)
        else:
            new_row = Shareholding(
                id=str(uuid.uuid4()), company_id=company_id, period_end=period_end,
                promoter_pct=promoter_pct, public_pct=public_pct, pledge_pct=pledge_pct,
                source_url=row.get("xbrl"), retrieved_at=now,
            )
            db.add(new_row)
            stored.append(new_row)
    db.flush()

    rows_asc = sorted(stored, key=lambda r: r.period_end)
    events = _detect_events(company_id, rows_asc)
    inserted_events = 0
    for ev in events:
        exists = db.query(GovernanceEvent).filter_by(
            company_id=company_id, event_type=ev["event_type"], event_date=ev["event_date"]
        ).first()
        if exists:
            continue
        db.add(GovernanceEvent(
            id=str(uuid.uuid4()), company_id=company_id, created_at=now, **ev,
        ))
        inserted_events += 1

    logger.info("shareholding_client: ingested", symbol=symbol,
                shareholding_rows=len(stored), events=inserted_events)
    return {"shareholding_rows": len(stored), "events": inserted_events}
