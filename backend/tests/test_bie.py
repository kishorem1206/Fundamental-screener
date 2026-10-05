"""Business Intelligence Engine, phase 1: the evidence gate, the data-file
reader's period handling, and the annual-report locators."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.bie import annual_report_extract as ar
from app.bie import xbrl
from app.bie.derive import derive_company
from app.bie.evidence import EvidenceError, record_fact, verify_fact
from app.bie.facts import FactBook
from app.bie.results_extract import extract_results, is_business_segment
from app.infrastructure.database.models import Document, Stock

NOW = datetime.now(timezone.utc)


def _company(db, symbol: str) -> str:
    db.add(Stock(id=f"TEST:{symbol}", symbol=symbol, exchange="TEST", company_name=f"{symbol} Ltd",
                 is_active=True, created_at=NOW, updated_at=NOW))
    db.flush()
    return f"TEST:{symbol}"


def _document(db, company_id: str, url: str = "https://example.test/filing.xml") -> Document:
    doc = Document(id=str(uuid.uuid4()), company_id=company_id, source="NSE", document_type="RESULTS_XBRL", url=url,
                   sha256="a" * 64, storage_key=f"test/{uuid.uuid4()}", retrieved_at=NOW, title="Test filing", published_at=NOW)
    db.add(doc)
    db.flush()
    return doc


def _reported(db, company_id, doc, **kw):
    base = dict(scope="COMPANY", company_id=company_id, fact_type="financial", key="RevenueFromOperations", value_num=100.0,
                unit="INR", nature="REPORTED", document=doc, locator_type="XBRL", locator="RevenueFromOperations@FourD",
                quote="100", extraction_method="XBRL_PARSE", source_tier=1, confidence="HIGH")
    return record_fact(db, **{**base, **kw})


# ── evidence gate ────────────────────────────────────────────────────────────

def test_document_fact_needs_an_archived_document_with_a_direct_url(db):
    cid = _company(db, "BIEG1")
    with pytest.raises(EvidenceError, match="archived document"):
        _reported(db, cid, None)
    with pytest.raises(EvidenceError, match="direct http"):
        _reported(db, cid, _document(db, cid, url="screener page"))


def test_page_locator_needs_page_and_quote_and_data_locator_needs_an_element(db):
    cid = _company(db, "BIEG2")
    doc = _document(db, cid)
    with pytest.raises(EvidenceError, match="page number"):
        _reported(db, cid, doc, locator_type="PAGE", page=None)
    with pytest.raises(EvidenceError, match="quoted source text"):
        _reported(db, cid, doc, locator_type="PAGE", page=3, quote=None)
    with pytest.raises(EvidenceError, match="element or path"):
        _reported(db, cid, doc, locator=None)
    with pytest.raises(EvidenceError, match="needs a locator"):
        _reported(db, cid, doc, locator_type="NONE")


def test_calculated_fact_must_name_existing_inputs_and_a_formula(db):
    cid = _company(db, "BIEG3")
    source = _reported(db, cid, _document(db, cid))
    calc = dict(scope="COMPANY", company_id=cid, fact_type="financial", key="x", value_num=1.0, nature="CALCULATED",
                extraction_method="CALCULATION", source_tier=1, confidence="HIGH")
    with pytest.raises(EvidenceError, match="input facts"):
        record_fact(db, **calc, formula="a ÷ b")
    with pytest.raises(EvidenceError, match="formula"):
        record_fact(db, **calc, inputs=[source.id])
    with pytest.raises(EvidenceError, match="do not exist"):
        record_fact(db, **calc, inputs=["no-such-fact"], formula="a ÷ b")
    assert record_fact(db, **calc, inputs=[source.id], formula="a ÷ b").source_url is None


def test_rerun_replaces_the_same_fact_and_verification_compares_with_the_source(db):
    cid = _company(db, "BIEG4")
    doc = _document(db, cid)
    _reported(db, cid, doc)
    fact = _reported(db, cid, doc, value_num=120.0, quote="120")
    assert len(FactBook(db, cid).facts) == 1
    assert verify_fact(db, fact, xbrl_lookup=lambda element, ctx: "120") == "VERIFIED"
    assert verify_fact(db, fact, xbrl_lookup=lambda element, ctx: "999") == "FAILED"
    page = _reported(db, cid, doc, key="claim", value_num=None, value_text="x", locator_type="PAGE", page=2, quote="market  share of 40%")
    assert verify_fact(db, page, page_text=lambda p: "Our Market\nshare of 40% grew") == "VERIFIED"


# ── results data file ────────────────────────────────────────────────────────

_FILE = b"""<?xml version="1.0"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:f="http://x/in-bse-fin">
 <xbrli:context id="FourSeg1D"><xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-03-31</xbrli:endDate></xbrli:period>
  <xbrli:scenario><xbrldi:explicitMember dimension="f:ReportableSegmentsAxis">f:Seg1Member</xbrldi:explicitMember></xbrli:scenario></xbrli:context>
 <xbrli:context id="FourSeg2D"><xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-03-31</xbrli:endDate></xbrli:period>
  <xbrli:scenario><xbrldi:explicitMember dimension="f:ReportableSegmentsAxis">f:Seg2Member</xbrldi:explicitMember></xbrli:scenario></xbrli:context>
 <xbrli:context id="FourRes1D"><xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-03-31</xbrli:endDate></xbrli:period>
  <xbrli:scenario><xbrldi:explicitMember dimension="f:ReportableSegmentsFinanceCostsAxis">f:Seg1Member</xbrldi:explicitMember></xbrli:scenario></xbrli:context>
 <xbrli:context id="FourExp1D"><xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-03-31</xbrli:endDate></xbrli:period>
  <xbrli:scenario><xbrldi:explicitMember dimension="f:DetailsOfOtherExpensesAxis">f:Exp1Member</xbrldi:explicitMember></xbrli:scenario></xbrli:context>
 <f:DateOfStartOfFinancialYear contextRef="OneD">2023-04-01</f:DateOfStartOfFinancialYear>
 <f:DateOfEndOfFinancialYear contextRef="OneD">2024-03-31</f:DateOfEndOfFinancialYear>
 <f:DateOfStartOfReportingPeriod contextRef="OneD">2024-01-01</f:DateOfStartOfReportingPeriod>
 <f:DateOfEndOfReportingPeriod contextRef="OneD">2024-03-31</f:DateOfEndOfReportingPeriod>
 <f:DateOfStartOfReportingPeriod contextRef="FourD">2023-04-01</f:DateOfStartOfReportingPeriod>
 <f:DateOfEndOfReportingPeriod contextRef="FourD">2024-03-31</f:DateOfEndOfReportingPeriod>
 <f:NatureOfReportStandaloneConsolidated contextRef="OneD">Standalone</f:NatureOfReportStandaloneConsolidated>
 <f:RevenueFromOperations contextRef="OneD" unitRef="INR" decimals="-5">250</f:RevenueFromOperations>
 <f:RevenueFromOperations contextRef="FourD" unitRef="INR" decimals="-5">1000</f:RevenueFromOperations>
 <f:Cash contextRef="OneI" unitRef="INR" decimals="-5">7</f:Cash>
 <f:Cash contextRef="OneI" unitRef="INR" decimals="-5">9</f:Cash>
 <f:DescriptionOfReportableSegment contextRef="FourSeg1D">Cigarettes</f:DescriptionOfReportableSegment>
 <f:SegmentRevenue contextRef="FourSeg1D" unitRef="INR" decimals="-5">600</f:SegmentRevenue>
 <f:DescriptionOfReportableSegment contextRef="FourSeg2D">Less: Inter-segment revenue</f:DescriptionOfReportableSegment>
 <f:SegmentRevenue contextRef="FourSeg2D" unitRef="INR" decimals="-5">50</f:SegmentRevenue>
 <f:DescriptionOfReportableSegment contextRef="FourRes1D">Cigarettes</f:DescriptionOfReportableSegment>
 <f:SegmentProfitLossBeforeTaxAndFinanceCosts contextRef="FourRes1D" unitRef="INR" decimals="-5">300</f:SegmentProfitLossBeforeTaxAndFinanceCosts>
 <f:DescriptionOfOtherExpenses contextRef="FourExp1D">Excise Duty</f:DescriptionOfOtherExpenses>
 <f:OtherExpenses contextRef="FourExp1D" unitRef="INR" decimals="-5">120</f:OtherExpenses>
</xbrli:xbrl>"""


def test_year_to_date_period_comes_from_the_facts_not_the_mislabelled_context_dates(db):
    cid = _company(db, "BIEX1")
    doc = _document(db, cid)
    extract_results(db, company_id=cid, document=doc, content=_FILE, period_end=date(2024, 3, 31), basis="STANDALONE", audited=True)
    book = FactBook(db, cid)
    year = book.get("RevenueFromOperations", "FY", date(2024, 3, 31), "STANDALONE")
    assert (float(year.value_num), year.period_start) == (1000.0, date(2023, 4, 1))
    assert float(book.get("RevenueFromOperations", "Q", date(2024, 3, 31), "STANDALONE").value_num) == 250.0
    # undefined main contexts are still read; an element repeated with two values in one context is dropped
    assert book.get("Cash", "INSTANT", date(2024, 3, 31), "STANDALONE") is None
    assert verify_fact(db, year, xbrl_lookup=xbrl.parse(_FILE).lookup) == "VERIFIED"


def test_segment_and_excise_facts_feed_calculated_facts_that_name_their_inputs(db):
    cid = _company(db, "BIEX2")
    extract_results(db, company_id=cid, document=_document(db, cid), content=_FILE, period_end=date(2024, 3, 31),
                    basis="STANDALONE", audited=True)
    derive_company(db, cid)
    book = FactBook(db, cid)
    end = date(2024, 3, 31)
    margin = book.get("segment_margin", "FY", end, "STANDALONE", fact_type="segment", dimension="Cigarettes")
    assert float(margin.value_num) == 0.5 and len(margin.inputs) == 2
    net = book.get("revenue_net_of_excise", "FY", end, "STANDALONE")
    assert float(net.value_num) == 880.0 and net.nature == "CALCULATED"
    # the reconciliation row is stored but not treated as a business segment
    share = book.get("segment_revenue_share", "FY", end, "STANDALONE", fact_type="segment", dimension="Cigarettes")
    assert float(share.value_num) == 1.0
    assert not is_business_segment("Less: Inter-segment revenue") and is_business_segment("FMCG - Others")


# ── annual report locators ───────────────────────────────────────────────────

def test_subsidiary_statement_is_located_with_roman_numeral_and_continuation_pages():
    statement = "Form AOC-I Statement. Share capital Reserves Total assets Turnover Profit before tax % of shareholding"
    texts = ["Directors' report mentions Form AOC-1 is annexed.", statement, "Share capital Reserves Total assets continued", "Notes"]
    assert ar.locate_subsidiary_statement(texts) == [1, 2]


def test_no_subsidiary_statement_and_market_share_claims_are_quoted_with_their_page():
    texts = ["Intro.", "(e) The Company does not have any subsidiary, associate or joint venture. Accordingly nothing applies.",
             "In FY 2025-26, the Company's retail market share was about 40%. Vision: grow market share and revenue."]
    page, quote = ar.find_no_subsidiary_statement(texts)
    assert page == 1 and "does not have any subsidiary" in quote
    claims = ar.find_market_share_claims(texts)
    assert [(p, pct) for p, _, pct in claims] == [(2, [40.0])]


# ── analyst overrides ────────────────────────────────────────────────────────

def test_override_needs_a_reason_and_is_never_edited_in_place(db):
    from app.bie.overrides import OverrideError, history, reset_override, set_override
    cid = _company(db, "BIEO1")
    with pytest.raises(OverrideError, match="reason"):
        set_override(db, cid, metric="tax_rate", value=0.3, reason="no")
    with pytest.raises(OverrideError, match="company-level"):
        set_override(db, cid, metric="tax_rate", value=0.3, reason="A company-level input cannot take a year.", fiscal_year=2027)
    first = set_override(db, cid, metric="revenue_growth", unit="Cigarettes", fiscal_year=2027, value=-0.08, reason="Tax increase is expected to cut volumes.")
    second = set_override(db, cid, metric="revenue_growth", unit="Cigarettes", fiscal_year=2027, value=-0.06, reason="Second-quarter commentary was better than feared.")
    rows = {r["id"]: r for r in history(db, cid)}
    assert not rows[first.id]["active"] and rows[second.id]["active"] and rows[first.id]["value"] == -0.08
    assert reset_override(db, second.id) and not reset_override(db, second.id)
    assert len(history(db, cid)) == 2  # both kept after the reset


def test_classification_maps_to_the_right_production_series():
    from app.bie.official_data import core_series, iip_group
    assert iip_group("Cigarettes & Tobacco Products") == "Manufacture of Tobacco Products"
    assert iip_group("Cement & Cement Products") == "Manufacture of Other Non-metallic Mineral Products"
    assert core_series("Cement & Cement Products") == ["Cement"]
    assert iip_group("Private Sector Bank", "Banks") is None and core_series("Private Sector Bank") == []


def test_volume_release_is_chosen_by_classification(db):
    from app.bie.volumes import SOURCES
    import re
    pick = lambda name: next((s for s, (_, _, pattern) in SOURCES.items() if re.search(pattern, name, re.I)), None)  # noqa: E731
    assert pick("Passenger Cars & Utility Vehicles") == "Vehicles" and pick("Tyres & Rubber Products") == "Vehicles"
    assert pick("Telecom - Cellular & Fixed line services") == "Telecom" and pick("Airline") == "Aviation"
    assert pick("Asset Management Company") == "Mutual funds" and pick("Pharmaceuticals") is None
    assert pick("Life Insurance") == "Life insurance" and pick("General Insurance") == "General insurance"


def test_an_insurer_is_matched_to_its_own_row_in_the_industry_release():
    from app.bie.volumes import HEADLINES, SOURCES, _own_name
    assert _own_name("HDFC Life Insurance Company Limited", "HDFC Life Insurance Company Ltd.")
    assert _own_name("ICICI Lombard General Insurance Co Ltd", "ICICI Lombard General Insurance Company Ltd.")
    assert not _own_name("ICICI Prudential Life Insurance Company Limited", "ICICI Lombard General Insurance Company Ltd.")
    assert not _own_name("Industry total", None)
    assert set(HEADLINES) == set(SOURCES)  # every source has a trend to show


def test_insurer_ratios_are_calculated_from_the_filed_lines_and_filed_ratios_put_on_one_scale(db):
    cid = _company(db, "INSURER")
    doc = _document(db, cid)
    end = date(2026, 3, 31)
    filed = {"GrossPremiumsWritten": 30618.0, "NetPremiumWritten": 23374.0, "PremiumEarned": 22264.0, "IncurredClaims": 15828.0,
             "NetCommission": 4484.0, "OperatingExpensesRelatedToInsuranceBusiness": 3059.0, "ProfitLossAfterTax": 2772.0, "SolvencyRatio": 0.0267}
    for key, value in filed.items():
        record_fact(db, scope="COMPANY", company_id=cid, fact_type="financial", key=key, period_type="FY", period_end=end, statement_type="STANDALONE",
                    value_num=value, unit="ratio" if key == "SolvencyRatio" else "INR", nature="REPORTED", document=doc, locator_type="XBRL",
                    locator=f"{key}@FourD", quote=str(value), extraction_method="XBRL_PARSE", source_tier=1, confidence="HIGH")
    derive_company(db, cid)
    book = FactBook(db, cid)
    get = lambda key: float(book.get(key, "FY", end, "STANDALONE").value_num)  # noqa: E731
    assert book.period_ends("FY", "STANDALONE") == [end]  # gross premium written counts as the headline line
    assert get("claims_ratio") == pytest.approx(15828 / 22264) and get("expense_ratio") == pytest.approx((4484 + 3059) / 23374)
    assert get("combined_ratio") == pytest.approx(get("claims_ratio") + get("expense_ratio"))
    assert get("solvency_multiple") == pytest.approx(2.67)
    assert len(book.get("combined_ratio", "FY", end, "STANDALONE").inputs) == 5


def test_a_break_in_the_new_years_quarters_rebases_the_forecast_and_a_noisy_quarter_does_not(db):
    from app.bie.valuation import value_company

    def company(symbol: str, quarter_revenue: float, quarter_profit: float) -> dict:
        cid = _company(db, symbol)
        doc = _document(db, cid, url=f"https://example.test/{symbol}.xml")
        put = lambda key, value, period_type, end, **kw: _reported(  # noqa: E731
            db, cid, doc, key=key, value_num=value, period_type=period_type, period_end=end, statement_type="STANDALONE",
            locator=f"{key}@{period_type}{end}", quote=str(value), **kw)
        for end, revenue in ((date(2024, 3, 31), 800.0), (date(2025, 3, 31), 900.0), (date(2026, 3, 31), 1000.0)):
            put("RevenueFromOperations", revenue, "FY", end)
            put("ProfitBeforeTax", revenue * 0.2, "FY", end)
        put("TaxExpense", 50.0, "FY", date(2026, 3, 31))
        for end, revenue, profit in ((date(2025, 6, 30), 250.0, 50.0), (date(2026, 6, 30), quarter_revenue, quarter_profit)):
            put("RevenueFromOperations", revenue, "Q", end)
            put("ProfitBeforeTax", profit, "Q", end)
        put("shares_outstanding", 100.0, "NA", None, fact_type="identity", unit="shares")
        put("last_price", 10.0, "INSTANT", date(2026, 10, 1), fact_type="identity", unit="INR/share")
        return value_company(db, cid)

    broken = company("BREAK", 450.0, 36.0)   # revenue +80%, margin 20% -> 8%
    assert [b["name"] for b in broken["breaks"]] == ["Company"]
    unit = broken["units"][0]
    assert unit["start"] == pytest.approx(0.8) and unit["margin"] == pytest.approx(0.08) and unit["path"][1] == unit["end"]
    first = broken["scenarios"]["Base"]["rows"][0]
    assert first["revenue"] == pytest.approx(1800.0) and first["pbt"] == pytest.approx(144.0)

    noisy = company("NOISY", 280.0, 40.0)    # revenue +12%, margin 20% -> 14%: profit moved, revenue did not
    assert noisy["breaks"] == [] and noisy["units"][0]["margin"] == pytest.approx(0.2)


def test_only_listed_associates_and_joint_ventures_count_as_stakes_to_value_at_market(db):
    from app.bie.valuation import _entity_key, listed_stakes
    assert _entity_key("ITC Hotels Limited") == _entity_key("ITC Hotels Ltd.") != _entity_key("ITC Infotech India Limited")
    parent, held, sub = _company(db, "PARENT"), _company(db, "HELDCO"), _company(db, "SUBCO")
    doc = _document(db, parent, url="https://example.test/annual-report.pdf")
    for name, relationship in (("HELDCO Limited", "Associate"), ("SUBCO Limited", "Subsidiary"), ("Unlisted Ventures Private Limited", "Joint Venture")):
        record_fact(db, scope="COMPANY", company_id=parent, fact_type="group_entity", key="relationship", dimension=name, value_text=relationship,
                    attributes={"shares_held_ratio": 0.4}, nature="REPORTED", document=doc, locator_type="PAGE", page=5, quote=name,
                    extraction_method="PDF_TABLE", source_tier=1, confidence="MEDIUM")
    assert [(s.id, f.dimension) for s, f in listed_stakes(db, parent)] == [(held, "HELDCO Limited")]


def test_acquisition_disclosure_rows_give_cost_consideration_and_whether_the_deal_has_closed():
    from app.bie.acquisitions import read_filing, target_key
    table = ("Sl.\nNo.\nParticulars Disclosures\n6. Indicative time period for \ncompletion of the acquisition\n{timing}\n"
             "7. Consideration - whether cash \nconsideration or share swap or any \nother form and details of the same\nCash.\n"
             "8. Cost of acquisition and / or the price \nat which the shares are acquired\n~ ₹ 645 crores.\n9. Percentage of shareholding\n100%\n")
    closed = read_filing(["Dear Sirs,\nThe Company today has further acquired 13,445 Equity Shares.", table.format(timing="The Company has today completed acquisition of the shares.")])
    assert (closed["status"], closed["consideration"], closed["cost"], closed["page"]) == ("completed", "cash", 645e7, 1)
    agreed = read_filing(["Dear Sirs,\nWe have entered into an agreement.", table.format(timing="Within 3 to 8 months, subject to receipt of applicable approvals.")])
    assert agreed["status"] == "pending" and agreed["cost"] == 645e7
    notice = read_filing(["Dear Sirs,\nThe Company has today completed the acquisition of the pulp and paper business."])
    assert notice["status"] == "completed" and notice["cost"] is None and notice["priced_elsewhere"]
    assert target_key("X Limited has informed the Exchange about Acquisition of Pulp Undertaking of Y Limited - Update") == target_key(
        "X Limited has informed the Exchange about Acquisition of Pulp Undertaking of Y Limited.")


def test_sector_measures_are_read_only_where_wording_and_a_plausible_number_sit_together():
    from app.bie.kpis import GROUPS, read_measures, read_outlook
    measures = {name: m for name, _, m in GROUPS}
    orders = {h["key"]: h for h in read_measures(["Cover", "The order book as on June 30, 2026, was at ₹ 778,954 crore.\nOrder Inflows at ₹ 1.08 lakh crore."], measures["Order book"])}
    assert orders["order_book"]["value"] == 778954 and orders["order_book"]["page"] == 1 and orders["order_inflow"]["value"] == pytest.approx(108000)
    air = {h["key"]: h["value"] for h in read_measures(["ASK (billion) 43.5\nLoad factor (%) 83.3%\nRASK* (INR) 5.66\nfleet of 432 aircraft"], measures["Airlines"])}
    assert air == {"load_factor": 83.3, "capacity_ask": 43.5, "rask": 5.66, "fleet": 432}
    assert read_measures(["Occupancy 7%", "we have no beds data"], measures["Hospitals"]) == []  # implausible or absent: nothing is taken
    talk = ["Analyst: Can you give guidance of 15% growth for FY27? Management: We expect to add about 7 gigawatts of capacity during FY27 through our own projects."]
    found = read_outlook(talk)
    assert len(found) == 1 and "We expect to add about 7 gigawatts" in found[0]["text"] and "Can you" not in found[0]["text"]


def test_measures_for_lenders_it_power_and_pharma_take_the_level_not_a_nearby_figure():
    from app.bie.kpis import GROUPS, read_measures
    measures = {name: m for name, _, m in GROUPS}
    read = lambda group, text: {h["key"]: h["value"] for h in read_measures([text], measures[group])}  # noqa: E731
    lender = read("Non-bank lenders", "AUM grew by 24% to\n₹ 546,944 crore. Delivered AUM addition of ₹ 36,969 crore.\nGNPA and NNPA improving to 0.96% and 0.39%")
    assert lender == {"assets_under_management": 546944, "gross_bad_loans": 0.96, "net_bad_loans": 0.39}
    assert read("IT services", "Total Contract Value (TCV): US$ 9.5 billion\nWorkforce strength: 593,798\nAttrition (IT Services): 13.6%") == \
        {"deal_wins": 9.5, "headcount": 593798, "attrition": 13.6}
    assert read("Power", "Operational capacity of over 90 GW\n35.7 GW under construction\ninstalled capacity, with another 32 GW") == {"capacity": 90, "under_construction": 35.7}
    assert read("Pharma", "677 ANDAs & 70 NDAs filed\n119 ANDAs & 13 NDAs pending approval\nR&D investment: 6.1% of Sales") == \
        {"rd_share": 6.1, "andas_filed": 677, "andas_pending": 119}


def test_a_measure_is_labelled_with_the_period_it_covers_and_levels_are_not_flows():
    from app.bie.kpis import period_of
    page = "Q1FY27 highlights\nNew sales bookings for the quarter stood at Rs 657 crore. Net Debt Rs 18,136 crore as on 30th June, 2026."
    at = page.index("Rs 657")
    assert period_of(page, at, at + 12, "sales_bookings")[0] == "quarter"
    at = page.index("Net Debt")
    assert period_of(page, at, at + 26, "net_debt") == ("level", "as at 30th June, 2026")
    year = "For the financial year FY26, New Sales bookings of Rs 20,143 crore were recorded."
    assert period_of(year, year.index("Rs 20,143"), year.index("crore"), "sales_bookings")[0] == "year"
    assert period_of("Total 5,38,443", 0, 14, "units_sold", "Sales for the month of September 2026")[0] == "month"
    assert period_of("Total 5,38,443", 0, 14, "units_sold")[0] == "not stated"


def test_the_language_model_only_transcribes_and_a_stand_in_model_is_never_trusted(monkeypatch):
    from app.bie import llm_assist
    page = "Operational highlights\nRefinery throughput stood at 20.4 MMT for the quarter. Retail stores: 19,340 across the country. " * 3
    answers = {"measures": [
        {"label": "Refinery throughput", "value": 20.4, "unit": "MMT", "period": "the quarter", "quote": "Refinery throughput stood at 20.4 MMT"},
        {"label": "Stores", "value": 25000, "unit": "count", "period": None, "quote": "Retail stores: 19,340 across the country"},   # figure not in the quote
        {"label": "Customers", "value": 500, "unit": "million", "period": None, "quote": "customer base of 500 million"}]}           # words not on the page
    monkeypatch.setattr(llm_assist, "_ask", lambda *a, **k: answers)
    kept = llm_assist.read_measures([page], "X Ltd")
    assert [(m["label"], m["value"]) for m in kept] == [("Refinery throughput", 20.4)]

    class StandIn:
        last_used_fallback = True
        def chat(self, *a, **k):
            return '{"segments": {"A": "Whatever"}}'
    import app.llm.client as client_module
    monkeypatch.undo()
    monkeypatch.setattr(client_module, "LLMClient", StandIn)
    assert llm_assist._ask("s", "u") is None


def test_a_half_yearly_file_is_not_read_as_a_quarter():
    from app.bie.results_extract import _Periods

    def periods(start: str, end: str) -> _Periods:
        doc = f"""<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:in-bse-fin="http://x">
          <xbrli:context id="OneD"><xbrli:entity><xbrli:identifier scheme="s">X</xbrli:identifier></xbrli:entity>
            <xbrli:period><xbrli:startDate>{start}</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate></xbrli:period></xbrli:context>
          <in-bse-fin:DateOfStartOfReportingPeriod contextRef="OneD">{start}</in-bse-fin:DateOfStartOfReportingPeriod>
          <in-bse-fin:DateOfEndOfReportingPeriod contextRef="OneD">{end}</in-bse-fin:DateOfEndOfReportingPeriod>
        </xbrli:xbrl>"""
        inst = xbrl.parse(doc.encode())
        return _Periods(inst, date.fromisoformat(end)), inst.contexts["OneD"]

    quarter, ctx = periods("2025-07-01", "2025-09-30")
    assert quarter.of(ctx)[0] == "Q"
    half, ctx = periods("2025-04-01", "2025-09-30")
    assert half.of(ctx)[0] == "YTD"
    year, ctx = periods("2025-04-01", "2026-03-31")
    assert year.of(ctx)[0] == "FY"


def test_profit_after_tax_is_read_from_the_unambiguous_element_of_each_layout(db):
    from app.bie.facts import PROFIT_KEYS
    cid = _company(db, "LAYOUTS")
    doc = _document(db, cid)
    end = date(2025, 3, 31)
    for key, value in (("ProfitLossForPeriodBeforeMinorityInterest", 17687.0), ("ProfitLossForThePeriod", 15037.0)):
        _reported(db, cid, doc, key=key, value_num=value, period_type="FY", period_end=end, statement_type="CONSOLIDATED", locator=f"{key}@FourD", quote=str(value))
    # the conglomerate layout: "for the period" is after minority interests, so the before-minority element is the profit after tax
    assert float(FactBook(db, cid).first(PROFIT_KEYS, "FY", end, "CONSOLIDATED").value_num) == 17687.0


def test_mistyped_period_dates_are_settled_by_the_files_own_numbers():
    from app.bie.results_extract import _Periods
    doc = """<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:f="http://x">
      <xbrli:context id="OneD"><xbrli:entity><xbrli:identifier scheme="s">X</xbrli:identifier></xbrli:entity>
        <xbrli:period><xbrli:startDate>2025-01-10</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>
      <f:DateOfStartOfReportingPeriod contextRef="OneD">2025-01-10</f:DateOfStartOfReportingPeriod>
      <f:DateOfEndOfReportingPeriod contextRef="OneD">2025-12-31</f:DateOfEndOfReportingPeriod>
      <xbrli:context id="FourD"><xbrli:entity><xbrli:identifier scheme="s">X</xbrli:identifier></xbrli:entity>
        <xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>
      <f:DateOfStartOfReportingPeriod contextRef="FourD">2025-04-01</f:DateOfStartOfReportingPeriod>
      <f:DateOfEndOfReportingPeriod contextRef="FourD">2025-12-31</f:DateOfEndOfReportingPeriod>
      <f:RevenueFromOperations contextRef="OneD" unitRef="INR">__ONE__</f:RevenueFromOperations>
      <f:RevenueFromOperations contextRef="FourD" unitRef="INR">900</f:RevenueFromOperations>
    </xbrli:xbrl>"""
    doc = doc.replace("</xbrli:xbrl>", '<f:DateOfEndOfFinancialYear contextRef="OneD">2026-03-31</f:DateOfEndOfFinancialYear></xbrli:xbrl>')
    inst = xbrl.parse(doc.replace("__ONE__", "310").encode())  # a year that does not end at the year end, a third of nine months: a mistyped quarter
    kind, start, end = _Periods(inst, date(2025, 12, 31)).of(inst.contexts["OneD"])
    assert (kind, start, end) == ("Q", date(2025, 10, 1), date(2025, 12, 31))
    inst = xbrl.parse(doc.replace("__ONE__", "900").encode())  # all of the year to date: not a quarter, and not a full year either
    assert _Periods(inst, date(2025, 12, 31)).of(inst.contexts["OneD"])[0] == "YTD"
    six = doc.replace("2025-01-10", "2025-07-01").replace("__ONE__", "310")  # six months as typed are six months, whatever the share
    inst = xbrl.parse(six.encode())
    assert _Periods(inst, date(2025, 12, 31)).of(inst.contexts["OneD"])[0] == "YTD"


def test_a_measure_carries_what_it_is_a_measure_of_and_the_sentence_it_came_from():
    from app.bie.kpis import GENERAL, read_measures, scope_of
    page = ("Unitary Cooling Products\n\nRAC volumes grew 45% year on year, significantly outperforming the industry. "
            "The business achieved a YTD market share of 9.4% in Washing Machines and 6.2% in Refrigerators.")
    hits = {h["key"]: h for h in read_measures([page], GENERAL)}
    assert hits["volume_growth"]["scope"] == "RAC" and "RAC volumes grew 45% year on year" in hits["volume_growth"]["sentence"]
    assert hits["market_share"]["value"] == 9.4 and hits["market_share"]["scope"].startswith("Washing Machines")
    slide = "Jewellery division\n\n8.5% Market share\n"
    assert scope_of(slide, slide.index("8.5%"), slide.index("share") + 5)[0] is None  # not said in the sentence: never guessed from a heading
