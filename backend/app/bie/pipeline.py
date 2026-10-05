"""Phase 1 build for one company: fetch its filings from NSE, archive them,
extract facts, derive the calculated ones, verify everything against the
archived copies, and check that each cited link still resolves.

    python -m app.bie.pipeline ITC            # build facts
    python -m app.bie.pipeline ITC --report   # build facts, then the PDF

Each source is independent: one that fails is recorded in the summary and
the rest of the build carries on.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from datetime import date, datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from app.bie import annual_report_extract, brsr_extract, macro, xbrl
from app.bie.derive import derive_company
from app.bie.documents import archive, content_of, record_link_check
from app.bie.evidence import clear_document_facts, record_fact, verify_fact
from app.bie.nse_filings import NseFilings, ResultsFiling, _parse_datetime
from app.bie.results_extract import extract_results
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import BieFact, Document, Stock
from app.logger import logger

_EVENT_BUCKETS = (
    ("ACQUISITION", re.compile(r"acquisition", re.I)),
    ("RESTRUCTURING", re.compile(r"scheme of arrangement|amalgamation|merger|demerger|restructuring", re.I)),
    ("CREDIT_RATING", re.compile(r"credit rating", re.I)),
    ("LITIGATION", re.compile(r"litigation|dispute", re.I)),
    ("REGULATORY_ORDER", re.compile(r"orders passed|action\(s\)", re.I)),
)
_DEAL_UPDATE = re.compile(r"\bacquisition of (?!shares and takeovers)(?!.*substantial acquisition)", re.I)
_EVENT_WINDOW = timedelta(days=3 * 365)
_EVENTS_PER_BUCKET = 25


def _json_raw(raw: str, key: str) -> str | None:
    """The literal text of `"key": value` in a JSON document, for quoting."""
    match = re.search(rf'"{re.escape(key)}"\s*:\s*("(?:[^"\\]|\\.)*"|[^,}}\]]+)', raw)
    return match.group(0) if match else None


def _select_filings(filings: list[ResultsFiling], fy_end: date | None, fiscal_years: int, recent_quarters: int) -> list[ResultsFiling]:
    """The latest `recent_quarters` period ends plus the last `fiscal_years`
    year-end filings, both bases."""
    period_ends = sorted({f.period_end for f in filings}, reverse=True)
    wanted = set(period_ends[:recent_quarters])
    if fy_end is not None:
        year_ends = [d for d in period_ends if d.month == fy_end.month]
        wanted |= set(year_ends[:fiscal_years])
    return [f for f in filings if f.period_end in wanted]


class Build:
    def __init__(self, db: Session, nse: NseFilings | None = None):
        self.db = db
        self.nse = nse or NseFilings()
        self.touched: dict[str, Document] = {}
        self.summary: dict = {"errors": {}}

    # ── steps ────────────────────────────────────────────────────────────

    on_step = None  # called with each step's name as it starts, for progress reporting

    def _step(self, name: str, fn, *args, **kwargs):
        if self.on_step is not None:
            self.on_step(name)
        try:
            result = fn(*args, **kwargs)
            self.db.commit()
            return result
        except Exception as e:  # noqa: BLE001 — one source failing must not stop the others
            self.db.rollback()
            logger.warning("bie: step failed", step=name, error=str(e))
            self.summary["errors"][name] = f"{type(e).__name__}: {e}"
            return None

    def _touch(self, document: Document | None) -> Document | None:
        if document is not None:
            self.touched[document.id] = document
        return document

    def _snapshot(self, **kwargs) -> Document | None:
        """Archive a feed response that changes on every call, dropping the
        company's earlier snapshots of the same feed and their facts."""
        document = archive(self.db, **kwargs)
        if document is None:
            return None
        stale = self.db.query(Document).filter(
            Document.company_id == kwargs["company_id"], Document.document_type == kwargs["document_type"],
            Document.id != document.id).all()
        for old in stale:
            clear_document_facts(self.db, old)
            self.db.delete(old)
        return self._touch(document)

    def identity(self, stock: Stock) -> dict:
        symbol = stock.symbol
        meta_url = self.nse.symbol_meta_url(symbol)
        meta_raw = self.nse.fetch(meta_url, timeout=45)
        meta = json.loads(meta_raw)
        series = "EQ" if "EQ" in (meta.get("activeSeries") or ["EQ"]) else (meta.get("activeSeries") or ["EQ"])[0]
        data_url = self.nse.symbol_data_url(symbol, series)
        data_raw = self.nse.fetch(data_url, timeout=45)
        entry = (json.loads(data_raw).get("equityResponse") or [None])[0] or {}
        today = date.today()
        now = datetime.now(timezone.utc)
        written = 0

        def facts(document: Document, raw: str, pairs: list[tuple[str, str, str | None, object]]) -> None:
            nonlocal written
            clear_document_facts(self.db, document)
            for key, json_key, unit, value in pairs:
                quote = _json_raw(raw, json_key)
                if value in (None, "", "-") or quote is None:
                    continue
                numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
                record_fact(
                    self.db, scope="COMPANY", company_id=stock.id, fact_type="identity", key=key,
                    period_type="INSTANT", period_end=today, value_num=float(value) if numeric else None,
                    value_text=None if numeric else str(value).strip(), unit=unit, nature="REPORTED",
                    document=document, locator_type="JSON", locator=json_key, quote=quote,
                    extraction_method="API_JSON", source_tier=1, confidence="HIGH", replace=False,
                )
                written += 1

        meta_doc = self._snapshot(
            company_id=stock.id, source="NSE", document_type="NSE_SYMBOL_META", url=meta_url,
            content=meta_raw, content_type="application/json", title=f"NSE security metadata — {symbol}",
            period_end=today, published_at=now)
        if meta_doc is not None:
            facts(meta_doc, meta_raw.decode("utf-8", "replace"), [
                ("company_name", "companyName", None, meta.get("companyName")),
                ("isin", "isin", None, meta.get("isin")),
            ])
        data_doc = self._snapshot(
            company_id=stock.id, source="NSE", document_type="NSE_SYMBOL_DATA", url=data_url,
            content=data_raw, content_type="application/json", title=f"NSE quote and security information — {symbol}",
            period_end=today, published_at=now)
        if data_doc is not None and entry:
            sec, trade = entry.get("secInfo") or {}, entry.get("tradeInfo") or {}
            facts(data_doc, data_raw.decode("utf-8", "replace"), [
                ("basic_industry", "basicIndustry", None, sec.get("basicIndustry")),
                ("listing_date", "listingDate", None, (sec.get("listingDate") or "")[:11]),
                ("index_membership", "index", None, sec.get("index")),
                ("shares_outstanding", "issuedSize", "shares", trade.get("issuedSize")),
                ("face_value", "faceValue", "INR", trade.get("faceValue")),
                ("last_price", "lastPrice", "INR", trade.get("lastPrice")),
                ("market_cap", "totalMarketCap", "INR", trade.get("totalMarketCap")),
                ("free_float_market_cap", "ffmc", "INR", trade.get("ffmc")),
            ])
        return {"facts": written, "company_name": meta.get("companyName") or stock.company_name}

    def results(self, stock: Stock, fiscal_years: int, recent_quarters: int) -> dict:
        filings = self.nse.results(stock.symbol)
        if not filings:
            return {"filings_listed": 0, "files": 0, "facts": 0}
        fetched = {filings[0].xbrl_url: self.nse.fetch(filings[0].xbrl_url)}
        newest = xbrl.parse(fetched[filings[0].xbrl_url])
        try:
            fy_end = date.fromisoformat((newest.lookup("DateOfEndOfFinancialYear", "OneD") or "")[:10])
        except ValueError:
            fy_end = date(filings[0].period_end.year, 3, 31)
        files = facts = 0
        missing: list[str] = []
        for filing in _select_filings(filings, fy_end, fiscal_years, recent_quarters):
            try:
                content = fetched.get(filing.xbrl_url) or self.nse.fetch(filing.xbrl_url)
            except Exception as e:  # noqa: BLE001 — one data file the exchange no longer serves must not lose the others
                missing.append(f"{filing.period_end:%b %Y} {filing.basis.title()}: {type(e).__name__}")
                continue
            basis_label = filing.basis.title()
            document = self._touch(archive(
                self.db, company_id=stock.id, source="NSE", document_type="RESULTS_XBRL", url=filing.xbrl_url,
                content=content, content_type="application/xml", period_end=filing.period_end,
                title=f"Financial results for the period ended {filing.period_end:%d %b %Y} ({basis_label}) — exchange data file",
                published_at=filing.published_at, human_url=filing.readable_url or filing.pdf_url))
            if document is None:
                continue
            facts += extract_results(self.db, company_id=stock.id, document=document, content=content,
                                     period_end=filing.period_end, basis=filing.basis, audited=filing.audited)
            files += 1
            self.db.commit()
        return {"filings_listed": len(filings), "files": files, "facts": facts, "fy_end": fy_end.isoformat(), "files_unavailable": missing}

    def brsr(self, stock: Stock) -> dict:
        rows = self.nse.brsr(stock.symbol)
        if not rows or not rows[0].get("xbrlFile"):
            return {"filed": False, "facts": 0}
        row = rows[0]
        content = self.nse.fetch(row["xbrlFile"])
        fy_end = brsr_extract.fiscal_year_end(content)
        document = self._touch(archive(
            self.db, company_id=stock.id, source="NSE", document_type="BRSR_XBRL", url=row["xbrlFile"], content=content,
            content_type="application/xml", period_end=fy_end,
            title=f"Business Responsibility and Sustainability Report, FY{row.get('fyFrom')}-{str(row.get('fyTo'))[-2:]} — exchange data file",
            published_at=_parse_datetime(row.get("submissionDate")), human_url=row.get("attachmentFile") or None))
        if document is None:
            return {"filed": True, "facts": 0}
        return {"filed": True, "facts": brsr_extract.extract_brsr(self.db, company_id=stock.id, document=document, content=content)}

    def annual_report(self, stock: Stock) -> dict:
        rows = self.nse.annual_reports(stock.symbol)
        if not rows:
            return {"listed": 0}
        # The exchange sometimes serves a large report cut short. A cut file cannot be opened, so each is fetched
        # up to twice, and if the newest report is still incomplete the one before it is used and the fact is recorded.
        row = content = None
        skipped: list[str] = []
        seen: set[str] = set()
        for candidate in rows:
            url = candidate.get("fileName") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            if len(seen) > 3:
                break
            best = b""
            for _ in range(2):
                got = self.nse.fetch(url, timeout=300)
                if got[:2] == b"PK":
                    archive_file = zipfile.ZipFile(io.BytesIO(got))
                    pdfs = sorted((n for n in archive_file.namelist() if n.lower().endswith(".pdf")),
                                  key=lambda n: archive_file.getinfo(n).file_size, reverse=True)
                    got = archive_file.read(pdfs[0]) if pdfs else b""
                best = got if len(got) > len(best) else best
                if best[:4] == b"%PDF" and b"%%EOF" in best[-4096:]:
                    break
            if best[:4] == b"%PDF" and b"%%EOF" in best[-4096:]:
                row, content = candidate, best
                break
            skipped.append(f"{candidate.get('fromYr')}-{str(candidate.get('toYr'))[-2:]}: file served incomplete ({len(best):,} bytes)")
        if row is None:
            return {"listed": len(rows), "error": "no complete annual report could be downloaded", "incomplete": skipped}
        try:
            fy_end = date(int(row.get("toYr")), 3, 31)
        except (TypeError, ValueError):
            fy_end = None
        document = self._touch(archive(
            self.db, company_id=stock.id, source="NSE", document_type="ANNUAL_REPORT", url=row["fileName"],
            content=content, content_type="application/pdf", period_end=fy_end,
            title=f"Annual Report {row.get('fromYr')}-{str(row.get('toYr'))[-2:]}",
            published_at=_parse_datetime(row.get("broadcast_dttm") or row.get("disseminationDateTime"))))
        if document is None:
            return {"listed": len(rows), "error": "could not archive"}
        return {"listed": len(rows), "incomplete": skipped, "report_year": f"{row.get('fromYr')}-{str(row.get('toYr'))[-2:]}",
                **annual_report_extract.extract_annual_report(
                    self.db, company_id=stock.id, document=document, content=content, fy_end=fy_end)}

    def corporate_events(self, stock: Stock, company_name: str) -> dict:
        today = date.today()
        now = datetime.now(timezone.utc)
        written = 0

        url = self.nse.announcements_url(stock.symbol)
        raw_bytes = self.nse.fetch(url, timeout=90)
        rows = json.loads(raw_bytes)
        document = self._snapshot(
            company_id=stock.id, source="NSE", document_type="NSE_ANNOUNCEMENTS", url=url, content=raw_bytes,
            content_type="application/json", title=f"NSE corporate announcements — {stock.symbol}",
            period_end=today, published_at=now)
        if document is not None:
            clear_document_facts(self.db, document)
            counts: dict[str, int] = {}
            for row in rows if isinstance(rows, list) else []:
                when = _parse_datetime(row.get("an_dt") or row.get("sort_date"))
                attachment = row.get("attchmntFile") or ""
                bucket = next((b for b, pattern in _EVENT_BUCKETS if pattern.search(row.get("desc") or "")), None)
                # A deal's completion is often filed as a general update: the text, not the category, says what it is.
                if bucket is None and re.search(r"update", row.get("desc") or "", re.I) and _DEAL_UPDATE.search(row.get("attchmntText") or ""):
                    bucket = "ACQUISITION"
                if bucket is None or when is None or today - when.date() > _EVENT_WINDOW or not attachment.startswith("http"):
                    continue
                counts[bucket] = counts.get(bucket, 0) + 1
                if counts[bucket] > _EVENTS_PER_BUCKET:
                    continue
                filename = attachment.rsplit("/", 1)[-1]
                record_fact(
                    self.db, scope="COMPANY", company_id=stock.id, fact_type="corporate_event", key=bucket,
                    dimension=f"{when:%Y-%m-%d %H:%M:%S} {filename}"[:300], period_type="INSTANT", period_end=when.date(),
                    value_text=re.sub(r"\s+", " ", row.get("attchmntText") or row.get("desc") or "").strip()[:1200],
                    attributes={"category": row.get("desc"), "filing_url": attachment},
                    nature="REPORTED", document=document, locator_type="JSON", locator=f"attchmntFile = …/{filename}",
                    quote=filename, extraction_method="API_JSON", source_tier=1, confidence="HIGH", replace=False,
                )
                written += 1

        url = self.nse.schemes_url(company_name)
        raw_bytes = self.nse.fetch(url, timeout=90)
        rows = json.loads(raw_bytes)
        document = self._snapshot(
            company_id=stock.id, source="NSE", document_type="NSE_SCHEMES", url=url, content=raw_bytes,
            content_type="application/json", title=f"NSE schemes of arrangement — {company_name}",
            period_end=today, published_at=now)
        if document is not None:
            clear_document_facts(self.db, document)
            for row in rows if isinstance(rows, list) else []:
                attachment = row.get("date_attachmnt") or ""
                when = _parse_datetime(row.get("date"))
                if not attachment.startswith("http") or when is None:
                    continue
                filename = attachment.rsplit("/", 1)[-1]
                record_fact(
                    self.db, scope="COMPANY", company_id=stock.id, fact_type="corporate_event", key="SCHEME_OF_ARRANGEMENT",
                    dimension=f"{when:%Y-%m-%d} {filename}"[:300], period_type="INSTANT", period_end=when.date(),
                    value_text=re.sub(r"\s+", " ", row.get("scheme_details") or "Scheme of arrangement filed").strip()[:1200],
                    attributes={"filing_url": attachment, "observation_letter_url": row.get("observation_attachmnt") or None},
                    nature="REPORTED", document=document, locator_type="JSON", locator=f"date_attachmnt = …/{filename}",
                    quote=filename, extraction_method="API_JSON", source_tier=1, confidence="HIGH", replace=False,
                )
                written += 1
        return {"facts": written}

    # ── verification ─────────────────────────────────────────────────────

    def verify(self) -> dict:
        """Re-read each archived document touched in this build and check
        every fact drawn from it; then check the calculated facts."""
        tally = {"VERIFIED": 0, "FAILED": 0, "UNVERIFIED": 0}
        company_ids: set[str] = set()
        for document in self.touched.values():
            facts = self.db.query(BieFact).filter(BieFact.document_id == document.id).all()
            if not facts:
                continue
            content = content_of(document)
            kwargs: dict = {}
            if content is not None:
                locator_types = {f.locator_type for f in facts}
                if "XBRL" in locator_types:
                    kwargs["xbrl_lookup"] = xbrl.parse(content).lookup
                if "PAGE" in locator_types:
                    texts = annual_report_extract.page_texts(content)
                    kwargs["page_text"] = lambda page, texts=texts: texts[page - 1] if 0 < page <= len(texts) else ""
                if locator_types & {"JSON", "TABLE"}:
                    kwargs["raw_text"] = content.decode("utf-8", "replace")
            for fact in facts:
                tally[verify_fact(self.db, fact, **kwargs)] += 1
                if fact.company_id:
                    company_ids.add(fact.company_id)
            self.db.commit()
        calculated = self.db.query(BieFact).filter(BieFact.nature == "CALCULATED", BieFact.company_id.in_(company_ids)).all() if company_ids else []
        for fact in calculated:
            tally[verify_fact(self.db, fact)] += 1
        self.db.commit()
        return tally

    def check_links(self) -> dict:
        ok = broken = 0
        for document in self.touched.values():
            if "nseindia.com" in (document.url or ""):
                status = self.nse.link_status(document.url)
            else:
                try:
                    headers = macro._PLAIN if "imf.org" in document.url else macro._BROWSER
                    response = requests.get(document.url, headers=headers, timeout=30, stream=True)
                    status = response.status_code
                    response.close()
                except Exception:  # noqa: BLE001
                    status = None
            record_link_check(document, status)
            ok += status == 200
            broken += status != 200
        self.db.commit()
        return {"resolving": ok, "not_resolving": broken}


def build_company(db: Session, symbol: str, *, fiscal_years: int = 5, recent_quarters: int = 5,
                  peers: int = 8, peer_fiscal_years: int = 2, nse: NseFilings | None = None, on_step=None) -> dict:
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper(), Stock.is_active.is_(True)).first()
    if stock is None:
        raise ValueError(f"{symbol} is not an active stock in the screener universe")
    build = Build(db, nse)
    build.on_step = on_step
    summary = build.summary
    summary["symbol"], summary["company_id"] = stock.symbol, stock.id

    identity = build._step("identity", build.identity, stock) or {}
    summary["identity"] = identity
    summary["results"] = build._step("results", build.results, stock, fiscal_years, recent_quarters)
    summary["brsr"] = build._step("brsr", build.brsr, stock)
    summary["annual_report"] = build._step("annual_report", build.annual_report, stock)
    summary["corporate_events"] = build._step(
        "corporate_events", build.corporate_events, stock, identity.get("company_name") or stock.company_name)
    # Phase 2: management commentary, and entity names where the table reader found none.
    def guidance():
        from app.bie.commentary import import_guidance
        out = import_guidance(db, stock.id)
        for document in out.pop("documents"):
            build._touch(document)
        return out

    def entities():
        from app.bie.entities_llm import read_entities
        out = read_entities(db, stock.id)
        build._touch(out.pop("document", None))
        return out

    summary["guidance"] = build._step("guidance", guidance)
    summary["entities_read"] = build._step("entities_read", entities)
    summary["calculated"] = build._step("derive", derive_company, db, stock.id)

    def acquisitions():
        from app.bie.acquisitions import ingest_acquisitions
        from app.bie.facts import FactBook
        book = FactBook(db, stock.id)
        basis = next(iter(book.bases()), None)
        ends = book.period_ends("FY", basis) if basis else []
        return ingest_acquisitions(db, build.nse, stock, ends[0], touch=build._touch) if ends else {"skipped": "no full-year results"}

    summary["acquisitions"] = build._step("acquisitions", acquisitions)

    def sector_measures():
        from app.bie.kpis import ingest_sector_measures
        return ingest_sector_measures(db, build.nse, stock, touch=build._touch)

    summary["sector_measures"] = build._step("sector_measures", sector_measures)

    # A stake in a listed associate or joint venture is valued at the market's price: fetch it from the exchange.
    from app.bie.valuation import listed_stakes
    summary["listed_stakes"] = {}
    for held, _fact in listed_stakes(db, stock.id)[:6]:
        summary["listed_stakes"][held.symbol] = build._step(f"stake:{held.symbol}:identity", build.identity, held)

    def segment_industries():
        from app.bie.llm_assist import classify_segments
        return classify_segments(db, stock)

    summary["segment_industries"] = build._step("segment_industries", segment_industries)

    summary["peers"] = {}
    if peers:
        from app.bie.peers import select_peers
        for peer, _segment in select_peers(db, stock)[:peers]:
            peer_summary = {
                "identity": build._step(f"peer:{peer.symbol}:identity", build.identity, peer),
                "results": build._step(f"peer:{peer.symbol}:results", build.results, peer, peer_fiscal_years, 1),
            }
            build._step(f"peer:{peer.symbol}:derive", derive_company, db, peer.id)
            summary["peers"][peer.symbol] = peer_summary

    summary["macro"] = macro.ingest_macro(db)

    def benchmarks():
        from app.bie.sector import ingest_benchmarks
        return ingest_benchmarks(db)

    summary["industry_benchmarks"] = build._step("industry_benchmarks", benchmarks)

    def official():
        from app.bie.official_data import ingest_official_data
        return ingest_official_data(db)

    summary["official_production_data"] = build._step("official_production_data", official)

    def volumes():
        from app.bie.volumes import ingest_volumes
        return ingest_volumes(db)

    summary["unit_volumes"] = build._step("unit_volumes", volumes)
    for document_type in ("CCIL_GSEC_YIELDS", "IMF_NGDP_RPCH", "IMF_PCPIPCH"):
        latest = (db.query(Document).filter(Document.document_type == document_type, Document.company_id.is_(None))
                  .order_by(Document.retrieved_at.desc()).first())
        build._touch(latest)

    summary["verification"] = build._step("verify", build.verify)
    summary["links"] = build._step("links", build.check_links)
    summary["documents"] = len(build.touched)
    summary["nse_requests"] = build.nse.requests
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbol")
    parser.add_argument("--fiscal-years", type=int, default=5)
    parser.add_argument("--quarters", type=int, default=5)
    parser.add_argument("--peers", type=int, default=8)
    parser.add_argument("--report", action="store_true", help="also render the PDF report")
    args = parser.parse_args()
    db = get_db()
    try:
        summary = build_company(db, args.symbol, fiscal_years=args.fiscal_years, recent_quarters=args.quarters, peers=args.peers)
        print(json.dumps(summary, indent=2, default=str))
        if args.report:
            from app.bie.report.render import render_report
            print("report:", render_report(db, summary["company_id"]))
    finally:
        db.close()


if __name__ == "__main__":
    main()
