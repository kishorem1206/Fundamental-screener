"""Assembles the report's content from `bie_facts`. Nothing is computed here
beyond presentation (unit conversion, year-on-year change of two cited
figures); every figure carries the number of the source it came from.
"""
from __future__ import annotations

import re
from datetime import date

from sqlalchemy.orm import Session

from app.bie.facts import (
    EXCEPTIONAL_KEYS, PBT_KEYS, PROFIT_KEYS, REVENUE_KEYS, LINE_PREMIUM, LINE_RESULTS, SEGMENT_ASSETS, SEGMENT_LIABILITIES, SEGMENT_RESULT,
    SEGMENT_REVENUE, FactBook,
)
from app.infrastructure.database.models import BieFact, Document, Stock
from app.bie.peers import segment_peer_plan, select_peers
from app.bie.sector import DEFAULT_DRIVER, DRIVERS, benchmark_industry, benchmarks_for

CRORE = 1e7
_EVENT_LABELS = {
    "ACQUISITION": "Acquisition", "RESTRUCTURING": "Restructuring", "SCHEME_OF_ARRANGEMENT": "Scheme of arrangement",
    "CREDIT_RATING": "Rating disclosure", "LITIGATION": "Litigation", "REGULATORY_ORDER": "Regulatory order",
}


class Sources:
    """Numbers each document in order of first citation."""

    def __init__(self, db: Session):
        self._db = db
        self._order: list[str] = []
        self._docs: dict[str, Document] = {}
        self._use: dict[str, dict] = {}

    def cite(self, *facts: BieFact | None) -> list[int]:
        numbers: list[int] = []
        for fact in facts:
            if fact is None:
                continue
            if fact.nature in ("CALCULATED", "ANALYST_ASSUMPTION"):
                inputs = self._db.query(BieFact).filter(BieFact.id.in_(fact.inputs or [])).all()
                numbers += self.cite(*inputs)
                continue
            if not fact.document_id:
                continue
            if fact.document_id not in self._docs:
                doc = self._db.get(Document, fact.document_id)
                if doc is None:
                    continue
                self._docs[doc.id] = doc
                self._order.append(doc.id)
                self._use[doc.id] = {"facts": 0, "pages": set()}
            use = self._use[fact.document_id]
            use["facts"] += 1
            if fact.page:
                use["pages"].add(fact.page)
            numbers.append(self._order.index(fact.document_id) + 1)
        return sorted(set(numbers))

    def register(self) -> list[dict]:
        out = []
        for n, doc_id in enumerate(self._order, 1):
            doc, use = self._docs[doc_id], self._use[doc_id]
            out.append({
                "n": n, "title": doc.title or doc.document_type, "publisher": doc.source,
                "company": doc.company_id.split(":")[-1] if doc.company_id and doc.document_type in ("RESULTS_XBRL", "BRSR_XBRL", "ANNUAL_REPORT") else None,
                "date": (doc.published_at.date() if doc.published_at else doc.period_end),
                "url": doc.url, "readable_url": doc.human_url, "sha": doc.sha256[:12],
                "link_status": doc.link_status, "checked": doc.link_checked_at.date() if doc.link_checked_at else None,
                "pages": sorted(use["pages"]), "is_data_file": (doc.content_type or "").endswith("xml"),
            })
        return out


def _cr(fact: BieFact | None) -> float | None:
    return None if fact is None or fact.value_num is None else float(fact.value_num) / CRORE


def _num(fact: BieFact | None) -> float | None:
    return None if fact is None or fact.value_num is None else float(fact.value_num)


def _growth(now: float | None, before: float | None) -> float | None:
    return None if now is None or not before or before <= 0 else now / before - 1


def _fy(end: date) -> str:
    return f"FY{str(end.year)[-2:]}"


def _primary_basis(book: FactBook) -> str | None:
    bases = book.bases()
    return bases[0] if bases else None


def _headline(book: FactBook, basis: str, period_type: str, end: date, src: Sources) -> dict:
    revenue = book.first(REVENUE_KEYS, period_type, end, basis)
    profit = book.first(PROFIT_KEYS, period_type, end, basis)
    net = book.get("revenue_net_of_excise", period_type, end, basis)
    excise = next((f for f in book.facts if f.fact_type == "line_detail" and f.key == "OtherExpenses"
                   and "excise" in f.dimension.lower() and f.period_type == period_type and f.period_end == end
                   and f.statement_type == basis), None)
    row = {
        "end": end, "label": _fy(end) if period_type == "FY" else f"{end:%b %Y}",
        "revenue": _cr(revenue), "excise": _cr(excise), "net_revenue": _cr(net),
        "other_income": _cr(book.get("OtherIncome", period_type, end, basis)),
        "pbt_before_exceptional": _cr(book.get("ProfitBeforeExceptionalItemsAndTax", period_type, end, basis)),
        "exceptional": _cr(book.first(EXCEPTIONAL_KEYS, period_type, end, basis)),
        "pbt": _cr(book.first(PBT_KEYS, period_type, end, basis)),
        "tax": _cr(book.get("TaxExpense", period_type, end, basis)),
        "profit_continuing": _cr(book.get("ProfitLossForPeriodFromContinuingOperations", period_type, end, basis)),
        "profit_discontinued": _cr(book.get("ProfitLossFromDiscontinuedOperationsAfterTax", period_type, end, basis)),
        "profit": _cr(profit),
        "eps": _num(book.first(("BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations",
                                "BasicEarningsPerShareAfterExtraordinaryItems"), period_type, end, basis)),
        "audited": (book.get("WhetherResultsAreAuditedOrUnaudited", period_type, end, basis, fact_type="filing_statement") or
                    BieFact(value_text="")).value_text,
        "cites": src.cite(revenue, profit, excise),
    }
    row["revenue_label"] = revenue.key if revenue is not None else None
    return row


def _segment_table(book: FactBook, basis: str, end: date, prior: date | None, src: Sources) -> dict | None:
    current = book.segments("FY", end, basis)
    if len(current) < 2:
        return None
    before = book.segments("FY", prior, basis) if prior else {}
    rows, cited = [], []
    for label, facts in current.items():
        first = next(iter(facts.values()))
        if not (first.attributes or {}).get("is_business_segment", True):
            continue
        rev, res = facts.get(SEGMENT_REVENUE), facts.get(SEGMENT_RESULT)
        if rev is None and res is None:  # an insurer's lines of business: shown in their own table
            continue
        seg = lambda key: book.get(key, "FY", end, basis, fact_type="segment", dimension=label)  # noqa: E731
        employed = book.get("segment_capital_employed", "INSTANT", end, basis, fact_type="segment", dimension=label)
        cited += [rev, res, facts.get(SEGMENT_ASSETS), facts.get(SEGMENT_LIABILITIES)]
        rows.append({
            "name": label, "revenue": _cr(rev), "result": _cr(res),
            "revenue_growth": _growth(_cr(rev), _cr(before.get(label, {}).get(SEGMENT_REVENUE))),
            "result_growth": _growth(_cr(res), _cr(before.get(label, {}).get(SEGMENT_RESULT))),
            "margin": _num(seg("segment_margin")), "revenue_share": _num(seg("segment_revenue_share")),
            "result_share": _num(seg("segment_result_share")), "assets": _cr(facts.get(SEGMENT_ASSETS)),
            "capital_employed": _cr(employed), "return_on_capital": _num(seg("segment_return_on_capital")),
        })
    if len(rows) < 2:
        return None
    rows.sort(key=lambda r: r["revenue"] or 0, reverse=True)
    history = []
    for label in [r["name"] for r in rows]:
        series = []
        for e in book.period_ends("FY", basis):
            margin = book.get("segment_margin", "FY", e, basis, fact_type="segment", dimension=label)
            share = book.get("segment_result_share", "FY", e, basis, fact_type="segment", dimension=label)
            series.append({"label": _fy(e), "margin": _num(margin), "result_share": _num(share)})
            cited.append(margin)
        history.append({"name": label, "series": list(reversed(series))})
    top = max(rows, key=lambda r: r["result_share"] or 0)
    return {"basis": basis, "label": _fy(end), "rows": rows, "history": history, "top": top,
            "years": [_fy(e) for e in reversed(book.period_ends("FY", basis))], "cites": src.cite(*cited)}


def _latest_identity(book: FactBook, key: str) -> BieFact | None:
    facts = [f for f in book.of_type("identity") if f.key == key]
    return max(facts, key=lambda f: f.created_at) if facts else None


def _peer_from_store(db: Session, stock: Stock, for_segment: str | None) -> dict | None:
    """A peer with no exchange filings on file, from the Screener quarterly figures the app already keeps for every
    company (consolidated where held, else standalone): the four quarters to the latest March, or failing that the
    latest four. Marked as such in the table; it does not feed the valuation, which uses filed figures only."""
    from app.infrastructure.database.models import MetricDataPoint

    rows = db.query(MetricDataPoint).filter(MetricDataPoint.company_id == stock.id, MetricDataPoint.source == "SCREENER",
                                            MetricDataPoint.metric_key.in_(("qtr_sales", "qtr_net_profit"))).all()
    for basis in ("CONSOLIDATED", "STANDALONE"):
        series: dict[str, dict[str, float]] = {}
        for row in rows:
            if row.statement_type == basis and re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.period or ""):
                series.setdefault(row.period, {})[row.metric_key] = float(row.value)
        periods = sorted(p for p, v in series.items() if len(v) == 2)
        if len(periods) < 4:
            continue
        marches = [i for i, p in enumerate(periods) if p[5:7] == "03" and i >= 3]
        last = marches[-1] if marches else len(periods) - 1
        year = periods[last - 3:last + 1]
        revenue, profit = sum(series[p]["qtr_sales"] for p in year), sum(series[p]["qtr_net_profit"] for p in year)
        before = sum(series[p]["qtr_sales"] for p in periods[last - 7:last - 3]) if last >= 7 else None
        end = date.fromisoformat(year[-1])
        return {
            "name": stock.company_name, "symbol": stock.symbol, "for_segment": for_segment, "basic_industry": stock.basic_industry, "is_subject": False,
            "year": _fy(end) if marches else f"12m to {end:%b %y}", "basis": basis.title(),
            "market_cap": float(stock.market_cap) / CRORE if stock.market_cap else None, "revenue": revenue, "profit": profit,
            "growth": _growth(revenue, before), "margin": (profit / revenue) if revenue else None, "segments": None, "cites": [],
            "from_screener": True, "screener_url": f"https://www.screener.in/company/{stock.symbol}/" + ("consolidated/" if basis == "CONSOLIDATED" else ""),
        }
    return None


def _peer_row(db: Session, stock: Stock, src: Sources, is_subject: bool, for_segment: str | None = None) -> dict | None:
    book = FactBook(db, stock.id)
    basis = _primary_basis(book)
    ends = book.period_ends("FY", basis) if basis else []
    if not ends:
        return None if is_subject else _peer_from_store(db, stock, for_segment)
    end, prior = ends[0], ends[1] if len(ends) > 1 else None
    revenue, profit = book.first(REVENUE_KEYS, "FY", end, basis), book.first(PROFIT_KEYS, "FY", end, basis)
    before = book.first(REVENUE_KEYS, "FY", prior, basis) if prior else None
    market_cap = _latest_identity(book, "market_cap")
    rev, pat = _cr(revenue), _cr(profit)
    return {
        "name": stock.company_name, "symbol": stock.symbol, "for_segment": for_segment, "basic_industry": stock.basic_industry, "is_subject": is_subject,
        "year": _fy(end), "basis": basis.title(), "market_cap": _cr(market_cap), "revenue": rev, "profit": pat,
        "growth": _growth(rev, _cr(before)), "margin": (pat / rev) if rev and pat is not None else None,
        "segments": len([1 for facts in book.segments("FY", end, basis).values()
                         if (next(iter(facts.values())).attributes or {}).get("is_business_segment", True)]),
        "cites": src.cite(revenue, profit, before, market_cap),
    }


def build_report(db: Session, company_id: str) -> dict:
    stock = db.get(Stock, company_id)
    book = FactBook(db, company_id)
    src = Sources(db)
    basis = _primary_basis(book)
    fy_ends = book.period_ends("FY", basis) if basis else []
    q_ends = book.period_ends("Q", basis) if basis else []

    # ── Part I: sector ───────────────────────────────────────────────────
    basic_industry = _latest_identity(book, "basic_industry")
    index = _latest_identity(book, "index_membership")
    peers = [r for r in ([_peer_row(db, stock, src, True)] +
                         [_peer_row(db, p, src, False, seg) for p, seg in select_peers(db, stock)]) if r]
    by_segment = any(r["for_segment"] for r in peers)
    if not by_segment:
        peers.sort(key=lambda r: r["revenue"] or 0, reverse=True)

    # ── Phase 3: driver framework, industry benchmarks, lender measures ──
    equation, driver_list = DRIVERS.get(stock.basic_industry) or DRIVERS.get(stock.sector, DEFAULT_DRIVER)
    bench_rows = []
    targets = [("Whole company", stock.basic_industry, stock.industry, None)]
    for row in segment_peer_plan(db, stock, book):
        targets.append((row["segment"], row["basic_industry"], None, row["segment"]))
    seg_margins = {}
    if basis and fy_ends:
        seg_margins = {l: book.get("segment_margin", "FY", fy_ends[0], basis, fact_type="segment", dimension=l) for l, _ in
                       ((t[3], None) for t in targets if t[3])}
    for label, basic, industry, segment in targets:
        matched = benchmark_industry(basic, industry)
        facts = benchmarks_for(db, matched) if matched else {}
        if not facts:
            continue
        bench_rows.append({"label": label, "nse": basic, "matched": matched, "own_segment_margin": _num(seg_margins.get(segment)) if segment else None,
                           **{k: _num(facts.get(k)) for k in ("firms", "beta", "net_margin", "ebitda_margin", "cost_of_capital_inr", "trailing_pe", "ev_ebitda")},
                           "cites": src.cite(*facts.values())})
    as_of = db.query(BieFact.period_end).filter(BieFact.fact_type == "industry_benchmark").order_by(BieFact.period_end.desc()).first()
    benchmarks = {"rows": bench_rows, "as_of": as_of[0] if as_of else None, "cites": sorted({n for r in bench_rows for n in r["cites"]})}

    from app.bie.official_data import output_for
    output_rows = []
    for label, basic, industry, segment in targets:
        found = output_for(db, basic, industry)
        if found and not any(o["group"] == found["group"] and o["core"] == found["core"] for o in output_rows):
            output_rows.append({"label": label, "nse": basic, **{k: found[k] for k in ("group", "years", "core")}, "cites": src.cite(*found["facts"])})
    output = {"rows": output_rows, "labels": output_rows[0]["years"] and [y["label"] for y in output_rows[0]["years"]] if output_rows else [],
              "cites": sorted({n for row in output_rows for n in row["cites"]})}

    from app.bie.volumes import volumes_for
    volume_blocks, seen_volume = [], set()
    for label, basic, industry, segment in targets[:1]:  # the company's own classification only: a segment's matched industry is too loose a link
        found = volumes_for(db, basic, industry, company_name=stock.company_name)
        if found and found["sector"] not in seen_volume:
            seen_volume.add(found["sector"])
            volume_blocks.append({**{k: found[k] for k in ("sector", "period", "rows", "months", "trend")}, "cites": src.cite(*found["facts"])})

    lender_rows = []
    if stock.sector == "Financial Services":
        for s_, subject in [(stock, True)] + [(p, False) for p, _ in select_peers(db, stock)]:
            b_ = FactBook(db, s_.id)
            ends_ = b_.period_ends("FY", "STANDALONE")
            if not ends_ or b_.get("CET1Ratio", "FY", ends_[0], "STANDALONE") is None:
                continue
            e_ = ends_[0]
            picked = {"cet1": b_.get("CET1Ratio", "FY", e_, "STANDALONE"), "gnpa": b_.get("PercentageOfGrossNpa", "FY", e_, "STANDALONE"),
                      "nnpa": b_.get("PercentageOfNpa", "FY", e_, "STANDALONE"), "roa": b_.get("ReturnOnAssets", "FY", e_, "STANDALONE"),
                      "cd": b_.get("credit_deposit_ratio", "INSTANT", e_, "STANDALONE"), "cti": b_.get("cost_to_income", "FY", e_, "STANDALONE"),
                      "credit_cost": b_.get("credit_cost", "FY", e_, "STANDALONE"), "nii": b_.get("net_interest_income", "FY", e_, "STANDALONE"),
                      "advances": b_.get("Advances", "INSTANT", e_, "STANDALONE"), "deposits": b_.get("Deposits", "INSTANT", e_, "STANDALONE")}
            lender_rows.append({"name": s_.company_name, "is_subject": subject, "year": _fy(e_),
                                **{k: (_cr(v) if v is not None and v.unit == "INR" else _num(v)) for k, v in picked.items()},
                                "cites": src.cite(picked["cet1"], picked["advances"])})

    # Insurers: premium, what it costs to write, and the capital behind it, for the company and its peers.
    insurer_rows, insurer_lines = [], None
    if "insurance" in (stock.basic_industry or "").lower():
        for s_, subject in [(stock, True)] + [(p, False) for p, _ in select_peers(db, stock)]:
            b_ = book if subject else FactBook(db, s_.id)
            basis_ = _primary_basis(b_)
            ends_ = b_.period_ends("FY", basis_) if basis_ else []
            if not ends_:
                continue
            e_ = ends_[0]
            gross_ = b_.first(REVENUE_KEYS, "FY", e_, basis_)
            if gross_ is None or gross_.key not in ("GrossPremiumIncome", "GrossPremiumsWritten"):
                continue
            before_ = b_.first(REVENUE_KEYS, "FY", ends_[1], basis_) if len(ends_) > 1 else None
            profit_ = b_.first(PROFIT_KEYS, "FY", e_, basis_)
            ratios = {k: b_.get(k, "FY", e_, basis_) for k in ("return_on_equity", "expense_ratio", "claims_ratio", "combined_ratio", "retention_ratio",
                                                                "solvency_multiple", "persistency_13th_month", "persistency_61st_month")}
            insurer_rows.append({"name": s_.company_name, "is_subject": subject, "year": _fy(e_), "basis": basis_.title(),
                                 "premium": _cr(gross_), "growth": _growth(_cr(gross_), _cr(before_)), "profit": _cr(profit_),
                                 **{k: _num(v) for k, v in ratios.items()}, "cites": src.cite(gross_, profit_, *ratios.values())})
        insurer_rows.sort(key=lambda row: row["premium"] or 0, reverse=True)
        if basis and fy_ends:
            lines, cited = [], []
            earlier = book.segments("FY", fy_ends[1], basis) if len(fy_ends) > 1 else {}
            for label, facts in book.segments("FY", fy_ends[0], basis).items():
                premium = facts.get(LINE_PREMIUM)
                if premium is None or not premium.value_num:
                    continue
                result = next((facts[k] for k in LINE_RESULTS if k in facts), None)
                cited += [premium, result]
                lines.append({"name": re.sub(r"^Segment [A-Z] - ", "", label), "premium": _cr(premium), "result": _cr(result),
                              "growth": _growth(_cr(premium), _cr(earlier.get(label, {}).get(LINE_PREMIUM))),
                              "margin": _cr(result) / _cr(premium) if result is not None and _cr(premium) > 0 else None})
            total = sum(l["premium"] for l in lines if l["premium"] > 0)
            for l in lines:
                l["share"] = l["premium"] / total if total > 0 else None
            lines.sort(key=lambda l: l["premium"], reverse=True)
            if len(lines) >= 2:
                insurer_lines = {"rows": lines, "has_growth": any(l["growth"] is not None for l in lines), "year": _fy(fy_ends[0]), "basis": basis.title(), "cites": src.cite(*cited),
                                 "result_label": "Underwriting result" if any(LINE_RESULTS[0] in f for f in book.segments("FY", fy_ends[0], basis).values()) else "Surplus"}

    macro_facts = db.query(BieFact).filter(BieFact.scope == "MACRO").all()
    latest_yield_date = max((f.period_end for f in macro_facts if f.key == "gsec_yield_pct"), default=None)
    yields = sorted((f for f in macro_facts if f.key == "gsec_yield_pct" and f.period_end == latest_yield_date
                     and (f.attributes or {}).get("is_central_government")), key=lambda f: float(f.value_num))
    newest_by_year: dict[tuple[str, str], BieFact] = {}
    for f in macro_facts:
        if f.fact_type == "macro" and (newest_by_year.get((f.key, f.dimension)) is None
                                       or f.created_at > newest_by_year[(f.key, f.dimension)].created_at):
            newest_by_year[(f.key, f.dimension)] = f
    years = sorted({d for (_, d) in newest_by_year})
    macro = {
        "yield_date": latest_yield_date,
        "yields": [{"tenor": (f.attributes or {}).get("tenor_bucket"), "security": (f.attributes or {}).get("security"),
                    "value": float(f.value_num)} for f in yields],
        "yield_cites": src.cite(*yields),
        "years": years,
        "series": [{"label": label, "values": [
            {"year": y, "value": _num(newest_by_year.get((key, y))),
             "projection": bool((newest_by_year.get((key, y)).attributes or {}).get("is_projection")) if newest_by_year.get((key, y)) else False}
            for y in years]} for key, label in (("real_gdp_growth_pct", "Real GDP growth (%)"), ("cpi_inflation_pct", "Consumer price inflation (%)"))],
        "imf_cites": src.cite(*newest_by_year.values()),
    }
    ten_year = next((y for y in macro["yields"] if (y["tenor"] or "").startswith("9Y")), None)

    # ── Part II: company ─────────────────────────────────────────────────
    identity_keys = ("company_name", "isin", "listing_date", "shares_outstanding", "face_value", "last_price", "market_cap",
                     "free_float_market_cap")
    identity = {k: _latest_identity(book, k) for k in identity_keys}
    identity_view = {k: (f.value_text if f is not None and f.value_num is None else _num(f)) for k, f in identity.items()}
    identity_view["as_of"] = identity["market_cap"].period_end if identity["market_cap"] else None
    identity_cites = src.cite(*identity.values(), basic_industry, index)

    profile = {f.key: f for f in book.of_type("business_profile")}
    activities = sorted(book.of_type("business_activity"), key=lambda f: float(f.value_num), reverse=True)
    products = sorted(book.of_type("product"), key=lambda f: float(f.value_num), reverse=True)
    footprint = book.of_type("footprint")
    concentration = {f.key: f for f in book.of_type("concentration")}
    business = {
        "available": bool(profile or activities),
        "fy": _fy(activities[0].period_end) if activities and activities[0].period_end else None,
        "activities": [{"name": f.dimension, "group": (f.attributes or {}).get("main_activity"), "share": float(f.value_num)} for f in activities],
        "products": [{"name": f.dimension, "nic": (f.attributes or {}).get("nic_code"), "share": float(f.value_num)} for f in products],
        "states": _num(profile.get("NumberOfStatesWhereMarketServedByTheEntity")),
        "countries": _num(profile.get("NumberOfCountriesWhereMarketServedByTheEntity")),
        "export_share": _num(profile.get("PercentageOfContributionOfExportsInTheTotalTurnoverOfTheEntity")),
        "customers": (profile.get("ABriefOnTypesOfCustomersExplanatoryTextBlock") or BieFact(value_text=None)).value_text,
        "boundary": (profile.get("ReportingBoundary") or BieFact(value_text=None)).value_text,
        "footprint": sorted(({"label": f.dimension, "count": int(f.value_num)} for f in footprint), key=lambda r: r["label"]),
        "concentration": [
            {"label": label, "value": _num(concentration.get(key)), "is_ratio": concentration[key].unit == "ratio"}
            for key, label in (
                ("PercentageOfSalesToDealersOrDistributorsInTotalSales", "Sales made through dealers and distributors"),
                ("PercentageOfSalesToTopTenDealersOrDistributorsInTotalSalesToDealersOrDistributors", "Top ten dealers' share of those sales"),
                ("PercentageOfPurchasesFromTradingHousesInTotalPurchasesForConcentrationOfPurchases", "Purchases made through trading houses"),
                ("PercentageOfSalesToRelatedPartiesInTotalSalesForShareOfRelatedPartyTransactions", "Sales to related parties"),
                ("PercentageOfPurchasesFromRelatedPartiesInTotalPurchasesForShareOfRelatedPartyTransactions", "Purchases from related parties"),
            ) if key in concentration],
        "cites": src.cite(*profile.values(), *activities, *products, *footprint, *concentration.values()),
    }

    entities = book.of_type("group_entity")
    structure = {f.key: f for f in book.of_type("group_structure")}
    by_name: dict[str, BieFact] = {}
    for f in sorted(entities, key=lambda f: f.locator_type != "XBRL"):  # the data file's row wins over the PDF table's
        by_name.setdefault(f.dimension.lower(), f)
    group = {
        "entities": sorted(({"name": f.dimension, "relationship": f.value_text if f.locator_type == "XBRL" or f.extraction_method.startswith("LLM")
                             or re.match(r"(associate|joint venture)", f.value_text or "", re.I) else "Subsidiary statement",
                             "held": (f.attributes or {}).get("shares_held_ratio"), "page": f.page,
                             "from_table": f.locator_type == "PAGE"} for f in by_name.values()),
                           key=lambda r: (-(r["held"] or 0), r["name"])),
        "location": structure["entity_list_location"].value_text if "entity_list_location" in structure else None,
        "none_statement": structure["no_subsidiaries_statement"].value_text if "no_subsidiaries_statement" in structure else None,
        "none_page": structure["no_subsidiaries_statement"].page if "no_subsidiaries_statement" in structure else None,
        "cites": src.cite(*by_name.values(), *structure.values()),
    }

    segment_tables = []
    for b in book.bases():
        ends = book.period_ends("FY", b)
        if ends:
            table = _segment_table(book, b, ends[0], ends[1] if len(ends) > 1 else None, src)
            if table:
                segment_tables.append(table)
    single = next((f for f in book.of_type("filing_statement") if f.key == "DescriptionOfSingleSegment" and f.value_text), None)
    single_cites = src.cite(single)

    annual = [_headline(book, basis, "FY", e, src) for e in fy_ends] if basis else []
    quarters = [_headline(book, basis, "Q", e, src) for e in q_ends[:5]] if basis else []
    for rows in (annual, quarters):
        for i, row in enumerate(rows):
            comparable = rows[i + 1] if rows is annual and i + 1 < len(rows) else next(
                (r for r in rows if r["end"] == date(row["end"].year - 1, row["end"].month, row["end"].day)), None)
            row["revenue_growth"] = _growth(row["revenue"], comparable["revenue"]) if comparable else None
            row["profit_growth"] = _growth(row["profit"], comparable["profit"]) if comparable else None

    normalisation = []
    for row in annual:
        if row["exceptional"]:
            normalisation.append({"period": row["label"], "item": "Exceptional items, before tax", "value": row["exceptional"], "cites": row["cites"]})
        if row["profit_discontinued"]:
            normalisation.append({"period": row["label"], "item": "Profit from discontinued operations, after tax",
                                  "value": row["profit_discontinued"], "cites": row["cites"]})
    events = sorted(book.of_type("corporate_event"), key=lambda f: f.period_end, reverse=True)
    event_rows = [{"date": f.period_end, "kind": _EVENT_LABELS.get(f.key, f.key.title()), "text": f.value_text,
                   "url": (f.attributes or {}).get("filing_url")} for f in events if f.key != "CREDIT_RATING"][:14]
    rating_rows = [{"date": f.period_end, "text": f.value_text, "url": (f.attributes or {}).get("filing_url")}
                   for f in events if f.key == "CREDIT_RATING"][:5]
    event_cites = src.cite(*events)
    audit = next((f for f in sorted(book.of_type("filing_statement"), key=lambda f: f.period_end or date.min, reverse=True)
                  if f.key == "DeclarationOfUnmodifiedOpinionOrStatementOnImpactOfAuditQualification"
                  and f.value_text and "not applicable" not in f.value_text.lower()), None)

    # ── Phase 2: balance sheet, cash and where it went, management commentary ──
    is_lender = stock.sector == "Financial Services"
    cash_rows, cash_cited = [], []
    for e in ([] if is_lender or not basis else fy_ends):
        f = lambda key, t="FY": book.get(key, t, e, basis)  # noqa: E731
        picked = {
            "cfo": f("CashFlowsFromUsedInOperatingActivities"), "capex": f("capital_expenditure"), "fcf": f("free_cash_flow"),
            "acquisitions": f("CashFlowsUsedInObtainingControlOfSubsidiariesOrOtherBusinessesClassifiedAsInvestingActivities"),
            "dividends": f("DividendsPaidClassifiedAsFinancingActivities"), "cover": f("dividend_cover_by_free_cash_flow"),
            "conversion": f("cash_conversion"), "equity": f("Equity", "INSTANT"), "assets": f("Assets", "INSTANT"),
            "inventories": f("Inventories", "INSTANT"), "receivables": f("TradeReceivablesCurrent", "INSTANT"),
            "current_investments": f("CurrentInvestments", "INSTANT"), "net_liquid": f("net_liquid_assets", "INSTANT"),
            "debt_to_equity": f("debt_to_equity", "INSTANT"),
        }
        if picked["cfo"] is None and picked["equity"] is None:
            continue
        row = {k: (_num(v) if v is not None and v.unit == "ratio" else _cr(v)) for k, v in picked.items()}
        for k in ("capex", "dividends", "acquisitions"):
            row[k] = abs(row[k]) if row[k] is not None else None
        row["label"] = _fy(e)
        row["cites"] = src.cite(picked["cfo"], picked["equity"])
        cash_rows.append(row)
        cash_cited += list(picked.values())
    cash_rows.reverse()
    cash = {"rows": cash_rows, "cites": src.cite(*cash_cited), "latest": cash_rows[-1] if cash_rows else None, "is_lender": is_lender}

    guidance_facts = sorted(book.of_type("guidance"), key=lambda f: ((f.attributes or {}).get("call_date") or "", f.page or 0), reverse=True)
    guidance = [{"metric": f.key.replace("_", " "), "text": f.value_text, "for_period": (f.attributes or {}).get("for_period"),
                 "quarter": (f.attributes or {}).get("quarter"), "speaker": (f.attributes or {}).get("speaker_role"),
                 "status": (f.attributes or {}).get("status"), "page": f.page, "cites": src.cite(f)} for f in guidance_facts]

    seen_statements: set[str] = set()
    guidance = [g for g in guidance if not (g["text"][:120] in seen_statements or seen_statements.add(g["text"][:120]))]

    # Sector measures: the latest statement of each, and the one before it from an earlier filing.
    from app.bie.kpis import _NEEDS_SCOPE as NEEDS_SCOPE
    by_measure: dict[str, list[BieFact]] = {}
    from datetime import timedelta

    def stated_on(f: BieFact) -> date:
        # A call transcript is filed weeks after the results it discusses: it ranks behind that cycle's presentation and release.
        return f.period_end - (timedelta(days=45) if (f.attributes or {}).get("filing_kind") == "transcript" else timedelta(0))

    for f in sorted(book.of_type("sector_kpi"), key=stated_on, reverse=True):
        # The same measure of two different things (market share in air conditioners, in washing machines) is two rows.
        scope = ((f.attributes or {}).get("scope") or "").strip().lower() if f.key in NEEDS_SCOPE else ""
        by_measure.setdefault((f.key, scope), []).append(f)
    sector_measures = []
    for (key, _scope), facts in by_measure.items():
        latest = facts[0]
        # Compared only with an earlier figure for the same kind of period: a quarter against a quarter, a level against a level.
        kind = (latest.attributes or {}).get("period_kind")
        earlier = next((f for f in facts[1:] if f.period_end < latest.period_end and (f.attributes or {}).get("period_kind") == kind
                        and kind not in (None, "not stated", "as stated")), None)
        sector_measures.append({
            "label": latest.attributes["label"] + (f": {latest.attributes['scope']}" if latest.attributes.get("scope") else ""),
            "scope": latest.attributes.get("scope"), "needs_scope": latest.key in NEEDS_SCOPE and not latest.attributes.get("scope"),
            "value": float(latest.value_num), "unit": latest.unit,
            "quote": latest.attributes.get("sentence") or " ".join((latest.quote or "").split()),
            "date": latest.period_end, "kind": latest.attributes.get("filing_kind"), "document": latest.attributes.get("filing_title"), "page": latest.page,
            "earlier": float(earlier.value_num) if earlier is not None else None, "earlier_date": earlier.period_end if earlier is not None else None,
            "period": (latest.attributes or {}).get("period") or "", "period_kind": kind or "not stated",
            "earlier_period": (earlier.attributes or {}).get("period") if earlier is not None else None,
            "by_model": (latest.attributes or {}).get("read_by", "").startswith("language model"),
            "group": latest.attributes.get("group"), "cites": src.cite(latest, earlier)})

    claims = book.of_type("market_share")
    claim_rows = [{"text": f.value_text, "page": f.page} for f in sorted(claims, key=lambda f: f.page or 0)]
    claim_cites = src.cite(*claims)

    # ── Phase 4: forecast and valuation (recomputed from the facts on file at render time) ──
    from app.bie.valuation import value_company
    valuation = value_company(db, company_id)
    db.commit()
    if "skipped" not in valuation:
        stored = db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.fact_type.in_(("assumption", "valuation"))).all()
        valuation["assumptions"] = [{"key": f.key.replace("_", " "), "for": f.dimension, "value": float(f.value_num), "unit": f.unit, "why": f.formula}
                                    for f in stored if f.fact_type == "assumption"]
        valuation["assumptions"] = [a for a in valuation["assumptions"] if not a["key"].startswith("override:")]
        from app.bie.overrides import _dry, _headline as _lenses, ranking
        valuation["system_only"] = _lenses(_dry(db, company_id, use_overrides=False)) if valuation["overrides"] else None
        valuation["with_overrides"] = _lenses(valuation)
        valuation["ranking"] = ranking(db, company_id)[:8]
        deal_ids = [i for group in valuation["deals"].values() for d in group for i in d["fact_ids"]]
        valuation["deals_cites"] = src.cite(*db.query(BieFact).filter(BieFact.id.in_(deal_ids)).all()) if deal_ids else []
        bridge_ids = valuation["equity_bridge"]["fact_ids"]
        valuation["equity_bridge"]["cites"] = src.cite(*db.query(BieFact).filter(BieFact.id.in_(bridge_ids)).all()) if bridge_ids else []
        valuation["cites"] = src.cite(*[f for f in stored if f.key in ("cost_of_capital", "peer_price_to_earnings_median", "sotp_value_per_share", "terminal_growth")])
        for scenario in valuation["scenarios"].values():
            for row in scenario["rows"]:
                row["label"] = _fy(row["end"]) + "E"
    all_facts = FactBook(db, company_id).facts
    latest_fy = annual[0] if annual else None
    report = {
        "exhibits": [], "generated": date.today(), "stock": stock, "basis": basis.title() if basis else None,
        "cutoff": q_ends[0] if q_ends else None,
        "classification": list(dict.fromkeys(x for x in (stock.macro_sector, stock.sector, stock.industry, stock.basic_industry) if x)),
        "basic_industry": basic_industry.value_text if basic_industry else stock.basic_industry,
        "index": index.value_text if index else None,
        "peers": peers, "peers_by_segment": by_segment, "driver": {"equation": equation, "drivers": driver_list},
        "benchmarks": benchmarks, "output": output, "volumes": volume_blocks, "lenders": lender_rows, "insurers": insurer_rows, "insurer_lines": insurer_lines, "macro": macro, "ten_year": ten_year,
        "identity": identity_view, "identity_cites": identity_cites,
        "business": business, "group": group,
        "segments": segment_tables, "single_segment": single.value_text if single else None, "single_cites": single_cites,
        "annual": annual, "quarters": quarters, "latest_fy": latest_fy,
        "normalisation": normalisation, "events": event_rows, "ratings": rating_rows, "event_cites": event_cites,
        "audit": {"text": audit.value_text, "period": audit.period_end, "cites": src.cite(audit)} if audit else None,
        "sector_measures": sector_measures, "claims": claim_rows, "claim_cites": claim_cites, "valuation": valuation, "cash": cash, "guidance": guidance,
        "evidence": {
            "facts": len(all_facts),
            "reported": sum(1 for f in all_facts if f.nature == "REPORTED"),
            "claims": sum(1 for f in all_facts if f.nature in ("COMPANY_CLAIM", "MANAGEMENT_GUIDANCE")),
            "calculated": sum(1 for f in all_facts if f.nature == "CALCULATED"),
            "assumptions": sum(1 for f in all_facts if f.nature == "ANALYST_ASSUMPTION"),
            "verified": sum(1 for f in all_facts if f.verification_status in ("VERIFIED", "ASSUMPTION")),
            "failed": sum(1 for f in all_facts if f.verification_status == "FAILED"),
            "documents": len(book.documents),
        },
        "sources": src.register(),
    }
    from app.bie.editorial import build_assessment
    report["assessment"] = build_assessment(report)
    from app.bie.report.exhibits import build_exhibits, svg
    report["exhibits"] = [{**e, "svg": svg(e)} for e in build_exhibits(report)]
    return report
