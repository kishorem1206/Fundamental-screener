"""Checks run over everything on file: that every fact still verifies against its archived source, that the same
figure is not held at two different values, and that headline figures agree with an independent source.

    python -m app.bie.audit            # verify + conflicts
    python -m app.bie.audit --screener # also compare revenue and profit with Screener (network)
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.bie import xbrl
from app.bie.annual_report_extract import page_texts
from app.bie.documents import content_of
from app.bie.evidence import verify_fact
from app.bie.facts import PROFIT_KEYS, REVENUE_KEYS, FactBook
from app.infrastructure.database.models import BieFact, Document, Stock


def verify_pending(db: Session) -> dict:
    """Re-check every fact not yet marked verified against its archived document (and calculated facts against their inputs)."""
    tally: Counter = Counter()
    pending = db.query(BieFact).filter(BieFact.verification_status.in_(("UNVERIFIED", "FAILED"))).all()
    by_document: dict[str | None, list[BieFact]] = defaultdict(list)
    for f in pending:
        by_document[f.document_id].append(f)
    for document_id, facts in by_document.items():
        if document_id is None:
            continue
        content = content_of(db.get(Document, document_id))
        if content is None:
            tally["source unavailable"] += len(facts)
            continue
        kinds = {f.locator_type for f in facts}
        instance = xbrl.parse(content) if "XBRL" in kinds else None
        pages = page_texts(content) if "PAGE" in kinds else []
        raw = content.decode("utf-8", "ignore") if kinds & {"JSON", "TABLE"} else None
        for f in facts:
            tally[verify_fact(db, f, xbrl_lookup=instance.lookup if instance else None,
                              page_text=(lambda n: pages[n - 1] if 0 < n <= len(pages) else "") if pages else None, raw_text=raw)] += 1
    db.flush()
    for f in by_document.get(None, []):  # calculated facts and assumptions: after their inputs
        tally[verify_fact(db, f)] += 1
    db.commit()
    return dict(tally)


def check_links(db: Session, only_unchecked: bool = True) -> dict:
    """Request every cited document's address (by default only those not yet checked) and record whether it resolves."""
    from app.bie.pipeline import Build
    cited = db.query(BieFact.document_id).filter(BieFact.document_id.isnot(None)).distinct()
    query = db.query(Document).filter(Document.id.in_(cited))
    if only_unchecked:
        query = query.filter(Document.link_status.is_(None))
    build = Build(db, None)
    for document in query.all():
        build._touch(document)
    return build.check_links() if build.touched else {"resolving": 0, "not_resolving": 0}


def conflicts(db: Session, company_ids: list[str] | None = None) -> list[dict]:
    """Reported figures held at more than one value for the same company, element, period and basis, with which one
    the reports use (the latest publication) — a revision is expected to appear here; a mislabelled period is not."""
    out = []
    query = db.query(BieFact).filter(BieFact.fact_type == "financial", BieFact.nature == "REPORTED", BieFact.value_num.isnot(None))
    if company_ids:
        query = query.filter(BieFact.company_id.in_(company_ids))
    groups: dict[tuple, list[BieFact]] = defaultdict(list)
    for f in query.all():
        groups[(f.company_id, f.key, f.period_type, f.period_end, f.statement_type)].append(f)
    for (company_id, key, period_type, period_end, basis), facts in groups.items():
        values = sorted({round(float(f.value_num), 2) for f in facts})
        if len(values) > 1:
            out.append({"company": company_id, "key": key, "period_type": period_type, "period_end": period_end, "basis": basis, "values": values})
    return out


def compare_with_store(db: Session, tolerance: float = 0.015) -> dict:
    """Every quarter's revenue and profit after tax on file, for every company (peers included), against the Screener
    quarterly figures the app already stores for both consolidated and standalone accounts. No network. Returns
    {'companies', 'compared', 'agree', 'differences': [...]}; a difference is a prompt to look, since the two sources
    can define a line differently (excise, other operating income, minority interests)."""
    from app.infrastructure.database.models import MetricDataPoint

    stored: dict[tuple, float] = {}
    for row in db.query(MetricDataPoint).filter(MetricDataPoint.source == "SCREENER",
                                                MetricDataPoint.metric_key.in_(("qtr_sales", "qtr_net_profit"))).all():
        stored.setdefault((row.company_id, row.metric_key, row.period, row.statement_type), float(row.value))
    companies = {key[0] for key in stored}
    out = {"companies": 0, "compared": 0, "agree": 0, "differences": []}
    for (company_id,) in db.query(BieFact.company_id).filter(BieFact.company_id.in_(companies), BieFact.fact_type == "financial").distinct():
        book = FactBook(db, company_id)
        touched = False
        for basis in book.bases():
            for end in book.period_ends("Q", basis):
                excise = book.get("revenue_net_of_excise", "Q", end, basis)
                for item, ours, alternatives, key in (("revenue", book.first(REVENUE_KEYS, "Q", end, basis), [excise], "qtr_sales"),
                                                      ("profit after tax", book.first(PROFIT_KEYS, "Q", end, basis), [], "qtr_net_profit")):
                    theirs = stored.get((company_id, key, end.isoformat(), basis))
                    if ours is None or ours.value_num is None or theirs is None:
                        continue
                    candidates = [float(ours.value_num) / 1e7] + [float(a.value_num) / 1e7 for a in alternatives if a is not None and a.value_num is not None]
                    best = min(candidates, key=lambda x: abs(x - theirs))
                    touched = True
                    out["compared"] += 1
                    if abs(best - theirs) <= max(abs(theirs) * tolerance, 1.0):
                        out["agree"] += 1
                    else:
                        out["differences"].append({"company": company_id.split(":")[-1], "basis": basis, "quarter": end, "item": item,
                                                   "ours": round(best, 2), "screener": theirs, "gap": (best / theirs - 1) if theirs else None})
        out["companies"] += touched
    return out


def compare_with_screener(db: Session, stock: Stock, tolerance: float = 0.01) -> list[dict]:
    """Revenue and profit after tax for each year on file against Screener's annual table: an independent transcription of
    the same accounts. A difference above `tolerance` is reported with both figures; it is a prompt to look, not a verdict,
    because the two can legitimately differ in definition (excise, other operating income, minority interests)."""
    from openscreener import Stock as Screener

    book = FactBook(db, stock.id)
    basis = next(iter(book.bases()), None)
    if basis is None:
        return []
    table = Screener(stock.symbol, consolidated=basis == "CONSOLIDATED").profit_loss()
    theirs = {}
    for row in table or []:
        label = str(row.get("year") or row.get("period") or row.get("date") or "")
        year = next((int(x) for x in label.split() if x.isdigit() and len(x) == 4), None)
        if year and "TTM" not in label.upper():
            theirs[year] = row
    rows = []
    for end in book.period_ends("FY", basis):
        other = theirs.get(end.year)
        if other is None:
            continue
        revenue, profit = book.first(REVENUE_KEYS, "FY", end, basis), book.first(PROFIT_KEYS, "FY", end, basis)
        net = book.get("revenue_net_of_excise", "FY", end, basis)
        for name, ours, alternatives, their_keys in (
                ("revenue", revenue, [net], ("sales", "revenue")), ("profit after tax", profit, [], ("net_profit",))):
            their = next((other[k] for k in their_keys if other.get(k) is not None), None)
            if ours is None or their is None or not float(their):
                continue
            candidates = [float(ours.value_num) / 1e7] + [float(a.value_num) / 1e7 for a in alternatives if a is not None]
            best = min(candidates, key=lambda x: abs(x - float(their)))
            gap = best / float(their) - 1
            rows.append({"symbol": stock.symbol, "year": end.year, "item": name, "ours": round(best, 2), "screener": float(their), "gap": gap,
                         "agrees": abs(gap) <= tolerance})
    return rows


if __name__ == "__main__":
    from app.infrastructure.database.client import get_db
    session = get_db()
    print("verification:", verify_pending(session))
    print("links newly checked:", check_links(session))
    unresolved = session.query(Document).filter(Document.id.in_(session.query(BieFact.document_id).filter(BieFact.document_id.isnot(None)).distinct()),
                                                (Document.link_status != 200) | Document.link_status.is_(None)).count()
    print("cited documents whose link does not resolve:", unresolved)
    found = conflicts(session)
    print("figures held at more than one value:", len(found))
    stored = compare_with_store(session)
    print(f"against the Screener quarterly figures already stored: {stored['agree']} of {stored['compared']} quarter figures agree "
          f"across {stored['companies']} companies (peers included)")
    for row in sorted(stored["differences"], key=lambda x: -abs(x["gap"] or 0))[:40]:
        print(f"   {row['company']:12} {row['basis'][:4]} {row['quarter']} {row['item']:17} ours {row['ours']:>12,.2f}  Screener {row['screener']:>12,.2f}")
    if "--screener" in sys.argv:
        from app.bie.jobs import OWN_BUILD
        for company in session.query(Stock).join(BieFact, BieFact.company_id == Stock.id).filter(BieFact.fact_type.in_(OWN_BUILD)).distinct():
            import time
            result = None
            for wait in (8, 75, 150):  # Screener throttles: pace the requests and wait out a refusal
                time.sleep(wait)
                try:
                    result = compare_with_screener(session, company)
                    break
                except Exception as error:  # noqa: BLE001
                    last = error
            if result is None:
                print(company.symbol, "could not be compared:", type(last).__name__, str(last)[:80])
                continue
            off = [r for r in result if not r["agrees"]]
            print(f"{company.symbol:12} {len(result) - len(off)}/{len(result)} agree", [(r["year"], r["item"], r["ours"], r["screener"], f"{r['gap']:+.1%}") for r in off][:6])
