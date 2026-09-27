"""Locates the pages worth reading in a 600+ page annual report — pure Python
text search, zero LLM cost. Confirmed against HDFC Bank's real FY2025-26
report (678 pages, no PDF bookmarks/outline) that these terms cluster tightly
in the notes-to-accounts region rather than being scattered evenly, so a
handful of matched pages per area is enough to bound the later LLM extraction
calls to a few thousand tokens instead of the whole document.

See annual_report_ingestion.py's module docstring for the full Annual
Report Extraction Engine architecture and AREA REGISTRY that this file's
_AREA_TERMS/_AREA_WINDOW_SIZE/_AREA_PEAK_ONLY implement.
"""
from __future__ import annotations

import io

import pdfplumber

# Term -> disclosure area. A page is assigned to an area if ANY of its terms
# appear on that page (case-insensitive substring match).
_AREA_TERMS = {
    "asset_quality": [
        "provision coverage ratio", "movement in", "restructured",
        "gross npa", "net npa", "non-performing",
    ],
    # "current account" / "savings account" alone are too generic — they match
    # retail-product marketing copy ("CASA Accounts", "Savings Account offers")
    # elsewhere in the report, not the actual deposit-mix disclosure. Confirmed
    # on HDFC's report: plain "casa" hits both a business-segment list (noise)
    # and the real "CASA Deposits accounted for 34.1 per cent of Total
    # Deposits" line in the Board's Report — the compound phrase anchors on
    # the latter.
    "funding": [
        "casa", "deposits accounted for", "casa ratio", "average casa",
    ],
    "capital": [
        "capital adequacy", "cet1", "tier 1", "tier 2", "risk weighted assets",
        "common equity tier",
    ],
    "priority_sector": ["priority sector"],
    "segment": ["segment information", "segment reporting"],
    # Universal (any sector) areas, added when annual_report_ingestion.py
    # was generalized past banking-only. Note phrasing varies by company —
    # TCS's PPE note heading is "Property, plant and equipment consist of
    # the following", Coforge's is just "3  Property, plant and equipment"
    # (a note number, no qualifier) — so the heading text alone isn't a
    # reliable universal anchor. "accumulated depreciation" is: PPE
    # schedules always have it, and it's specifically NOT used for
    # goodwill/intangible-asset schedules (which say "accumulated
    # amortization" instead, by accounting convention) — confirmed this
    # distinction holds on both TCS and Coforge's real reports.
    "ppe": ["accumulated depreciation", "property, plant and equipment consist of"],
    # Note phrasing genuinely varies by company — confirmed on two real
    # reports: TCS titles this note "Other liabilities – Current" /
    # "...consist of the following", Coforge just "15 Other liabilities"
    # with no qualifier. "deferred revenue"/"accrued expenses"/"contract
    # liabilities" alone are too generic on their own (confirmed on TCS:
    # scattered across many pages of unrelated related-party disclosure
    # tables, which won the densest-window contest over the real note) —
    # but bare "other liabilities" alone is specific enough and correctly
    # wins the window on both real reports tested.
    "other_liabilities": ["other liabilities"],
    # Chemicals-sector areas (2026-09-20) — all four confirmed against
    # Pidilite Industries' real FY2025-26 standalone notes before writing
    # any extraction prompt (same discipline as ppe/other_liabilities
    # above): "Cost of Materials Consumed" is always its own numbered note
    # with a clean Opening+Purchases-Closing=TOTAL structure (Note 32,
    # p.208). "Power and Fuel" is NOT its own note — it's one line inside
    # the much longer "Other Expenses" note (Note 37, p.210) — the anchor
    # term still isolates the right page since "power and fuel"/"power,
    # fuel and water" don't otherwise appear scattered through the report.
    "raw_material": ["cost of materials consumed", "cost of raw materials consumed",
                      "cost of raw material consumed"],
    # "power cost"/"power & fuel" added after cross-checking a second real
    # report (Aarti Industries): its Manufacturing Expenses note labels the
    # line bare "Power" (fuel is folded into Cost of Materials Consumed
    # instead, confirmed on the same report) — deliberately NOT adding bare
    # "power" itself as a keyword, too generic/risky (would match "Power
    # Sector" commentary, "purchasing power", etc. elsewhere in the
    # report); accepting that this specific bare-label variant is a real,
    # acceptable miss rather than widening the net that far.
    "energy_cost": ["power and fuel", "power, fuel and water", "power cost", "power & fuel"],
    # "Revenue based on geography" / "Revenue by geography" (Pidilite,
    # Note 42, p.213) and "Geographical Gross Revenue" (Aarti Industries,
    # Note 27.1, p.209, using "Local Sales"/"Export Sales" as its row
    # labels instead of "India"/"Outside India") — both confirmed verbatim
    # against real reports; genuinely different phrasing per company for
    # the same Ind AS 108 disclosure. Also carries the "no single external
    # customer... 10% or more" sentence on the same page in both reports
    # checked, so one area covers both concepts.
    "revenue_geography": ["revenue based on geography", "revenue by geography",
                           "revenue from external customers", "geographical gross revenue",
                           "geographical revenue"],
    # "Expenditure incurred on Research and Development" is the Companies
    # Act (Accounts) Rules 2014 standard heading, inside the Board's Report
    # "Conservation of Energy, Technology Absorption" annexure (confirmed
    # verbatim on Pidilite, p.117) — always a small Capital/Recurring/TOTAL
    # table when present at all, absent entirely for companies with no R&D.
    "rd_expenditure": ["expenditure incurred on research and development",
                        "expenditure on research and development"],
    # Cement-sector area (2026-09-20) — lives in the Management Discussion &
    # Analysis section, not notes-to-accounts (a first for this file), so
    # the anchor terms are MD&A KPI-table headings rather than a note title.
    # Confirmed live on UltraTech Cement's real FY2025-26 report: a single
    # clean "Particulars / FY26 / FY25 / % change" table (p.123 0-indexed)
    # with Installed capacity (MTPA), Production (MMT), Capacity Utilisation,
    # immediately followed by a "Cost Highlights" narrative block reporting
    # Energy Cost, Input Material Costs, and Freight and Forwarding Expenses
    # all in INR/tonne for both years. Cross-checked on Ambuja Cements' real
    # report too: NOT present in this clean tabular form there — Ambuja's
    # equivalent figures are laid out as a scattered infographic/dashboard
    # (numbers and labels not reliably co-locatable from plain-text
    # extraction alone) — accepted as a real, company-dependent miss rather
    # than risking a label/value mismatch; the extraction prompt is written
    # to return null rather than guess when the layout isn't unambiguous.
    # Deliberately NARROW: "mtpa"/"installed capacity" were tried first and
    # rejected — both are common enough elsewhere in a cement annual report
    # (plant-by-plant capacity listings repeat "MTPA" dozens of times on a
    # single page) that they won the density contest over the real table,
    # pointing the locator at noise instead (confirmed live on UltraTech:
    # a plant-capacity listing page scored 21 combined hits vs the real
    # table's page scoring 10 with the wider term set — removing "mtpa" and
    # "installed capacity" collapsed UltraTech's result to page 123 alone,
    # the correct page, with zero competing candidates).
    "cement_operating_metrics": ["capacity utilisation", "capacity utilization", "cost highlights"],
    # Forest Materials (Paper)-sector area (2026-09-20). Paper companies'
    # MD&A disclosure is far less standardized than cement's — confirmed
    # live on two real reports: TNPL states current-year Paper production/
    # sales volume cleanly in a "Performance Highlights" narrative bullet
    # list (page 64, "lakh MT" units), JK Paper's report has no comparable
    # production/capacity disclosure in extractable text at all (every
    # candidate term scored at most 1 hit, scattered, no real concentration
    # — an accepted per-company miss, same class as Ambuja Cements').
    # Broader term set than cement's (no single anchor phrase proved
    # reliable across both reports) — precision comes from the prompt's
    # own conservative "return null if ambiguous" instruction, not from a
    # tight locator net here.
    "paper_operating_metrics": [
        "installed capacity", "production capacity", "capacity utilisation",
        "capacity utilization", "lakh mt", "tonnes per annum", "paper production", "paper sales",
    ],
    # Metals & Mining-sector area (2026-09-20). Confirmed live on 3 real
    # reports with a similar spread to Cement/Paper: JSW Steel's MD&A
    # "6.1.1 Production and sales" gives a clean current+prior-year
    # Consolidated AND Standalone crude steel production/sales table, PLUS
    # a directly-stated EBITDA/tonne narrative figure (rare bonus — most
    # sectors require deriving this). Tata Steel's report also has usable
    # narrative data ("combined saleable steel production... stood at
    # 22.04 MT... higher than FY2024-25 (20.34 MT) by 8%"), just not
    # tabular — "saleable steel production"/"saleable steel" were added
    # specifically after this term set's first pass picked a generic
    # industry-commentary page (p.214, tied score with the real data page
    # p.222) over the real data. Hindalco's report has NO comparably
    # extractable text — its production/capacity figures are embedded in
    # rotated chart labels that pdfplumber extracts as reversed, scrambled
    # digit strings (e.g. "840,39" instead of a real number) — an accepted
    # miss, the conservative prompt should return null rather than try to
    # parse corrupted chart text.
    "metals_operating_metrics": [
        "ebitda per tonne", "production and sales", "capacity utilisation",
        "capacity utilization", "crude steel production", "saleable steel production", "saleable steel",
    ],
    # Automobile (OEM)-sector area (2026-09-20). Confirmed live on two real
    # reports with genuinely different disclosure styles: Maruti Suzuki's
    # early "Company Overview" section has a clean "Total Sales Volume (in
    # units)" 5-year callout with the actual numbers as plain text (not a
    # bar chart image) — 2,422,713 / 2,234,266 / ... — giving both current
    # and prior year in one place; separately, its MD&A narrative states
    # "dealer inventory also remained low at around 12 days of stock" (a
    # metric normally near-impossible to get). Bajaj Auto's MD&A instead
    # has a genuine "Table 1: Domestic Sale of Motorcycles" 5-year table
    # with company sales, growth %, AND market share % all in one table —
    # a real, unexpected win: `market_share` (normally thought to require
    # third-party SIAM/VAHAN data) is sometimes disclosed directly by the
    # company itself, sourced from SIAM in the annual report's own table.
    "automobile_operating_metrics": ["total sales volume", "domestic sale of", "dealer inventory"],
    # ── Quarterly Sector KPI Extraction Engine (2026-09-20) ──────────────────
    # These four areas run against a DIFFERENT document type — NSE quarterly
    # Investor Presentation decks (app/ingestion/nse_investor_presentation_
    # client.py), not annual reports — but reuse this same generic
    # keyword-density page locator (nothing here is actually annual-report-
    # specific; the module name predates this second document type).
    # Confirmed live on 3 real decks: Maruti Suzuki's (Automobile) and
    # Ambuja Cements' (Cement) are directly attached to their NSE filing;
    # JSW Steel's (Metals) required following an external link out of a
    # cover-letter PDF (see nse_investor_presentation_client.py). No Paper
    # company found filing this category at all in a 120-day window — a
    # real, structural gap (smaller-cap paper companies don't run investor
    # decks), not a locator failure.
    #
    # Wider windows than the annual areas above, not peak_only, for
    # automobile specifically — confirmed live on Maruti's deck that the
    # YoY highlights table (p.5) and the domestic/export/segment breakdown
    # (p.12) are 7 pages apart, both wanted in one extraction call; the
    # whole deck is only 14 pages (~4,600 chars total) so a wide window
    # costs nothing here, unlike a 600-page annual report.
    "automobile_quarterly_metrics": ["sales volume", "highlights of q", "w.r.t."],
    # Cement: NOT the bar-chart "Sales Volume (MnT) / Cement Cost / EBITDA
    # (Rs PMT)" highlights page (tried first, rejected) — its text extracts
    # as a genuinely scrambled sequence of 9 numbers with no recoverable
    # column mapping (confirmed live: a primary-model LLM call on that
    # exact page returned sales_volume=1069, which is actually the OTHER
    # metric's Q1FY26 value — an order of magnitude wrong, not a near
    # miss). Retargeted at the "Quarter Ended / Particulars UoM / Volume
    # MnT ... EBITDA (PMT)" proper table instead (Ambuja Cements p.22
    # Consolidated / p.25 Standalone) — every row's own stated YoY/QoQ %
    # change independently verifies against the row's own numbers
    # (17.1 -> 18.4 = -7%, matches the table's own "(7%)"), confirming
    # this format is genuinely reliable where the bar-chart one wasn't.
    "cement_quarterly_metrics": ["particulars uom", "ebitda (pmt)", "ebitda margin"],
    # "ebitda/t" was tried first and dropped — tied on term-hit count with
    # a *different*, wrong page (JSW Steel's long-term FY14-FY26 average
    # EBITDA/t strategy slide, p.28) against the real quarterly table
    # (p.56), and _peak_pages' earliest-page tie-break picked the wrong
    # one. Not needed anyway — quarterly EBITDA/tonne is derived from
    # qtr_operating_profit/production here, same fallback pattern as the
    # annual metals_operating_metrics area, not extracted directly.
    "metals_quarterly_metrics": ["production & sales", "crude steel production"],
    "paper_quarterly_metrics": ["paper production", "paper sales", "sales volume"],
    # Chemicals-sector area — a genuinely weaker signal than the other 4
    # sectors, worth documenting honestly: ChemicalsSector's annual metrics
    # are all cost/revenue RATIOS (raw_material_cost_pct, energy_cost_pct,
    # export_revenue_pct, rd_to_revenue_pct), not physical volumes, so
    # there's no single clean "units/tonnes produced" figure to look for
    # the way Cement/Metals/Paper/Automobile have. Confirmed live on 2 real
    # companies: Aarti Industries' MD&A has a "Business Volumes (Q1)"
    # section giving YoY/QoQ growth % per business segment (Energy /
    # Non-Energy) — real, extractable, but segment-level, not a single
    # company-wide number. SRF's deck has no comparable volume section at
    # all, only financial figures already covered by the Tier-1 quarterly
    # engine. "business volumes" alone is the anchor — "volume growth" was
    # tried too and dropped: it won the density contest on a 3-year
    # strategic-outlook narrative page ("Deliver consistent volume growth
    # over 3 yrs...") that has no real quarterly numbers at all, beating
    # the actual data page purely on repeated generic phrasing.
    "chemicals_quarterly_metrics": ["business volumes"],
    # Consumer Durables — like Chemicals, a narrative press-release-style
    # deck rather than a row/column table (confirmed live on Voltas' real
    # Q1 FY27 "Investor Presentation" filing, actually a 7-page MD&A-style
    # earnings note). Page 2 states both the primary segment's (Room Air
    # Conditioners, under the "Unitary Cooling Products" segment) YoY
    # volume growth ("RAC volumes grew 45% year on year") AND its market
    # share ("achieved a 17.3% secondary market share") in the same
    # paragraph — a stronger single-page signal than Chemicals had. "market
    # share" alone was NOT used as an anchor: it also appears on 2 later
    # pages discussing a different segment's (Voltbek home appliances)
    # market share, which would dilute the density contest without adding
    # precision — "rac volumes"/"secondary market share" are unique to the
    # one real page.
    "consumer_durables_quarterly_metrics": ["rac volumes", "secondary market share"],
    # Hotels & Restaurants — confirmed live on Chalet Hotels' real Q1 FY27
    # deck: a genuine ROW-based table ("Hospitality: Geography wise
    # performance" p.10 / "...Segment wise performance" p.11), each with
    # ADR/Occupancy/RevPAR rows and a "Combined Portfolio" total row
    # showing current quarter, same-quarter-prior-year, and the table's
    # own stated YoY% — as reliable as Cement's row-based table, NOT a
    # bar-chart infographic. Indian Hotels' (IHCL) own deck was checked
    # first and rejected as a locator target: its only occupancy/ADR/
    # RevPAR content is a multi-panel bar-chart infographic (p.9) with
    # several unlabeled figures interleaved in extraction order — the same
    # failure mode as the rejected Ambuja Cement bar-chart page — so no
    # IHCL-specific terms were added here.
    "hotels_quarterly_metrics": ["combined portfolio", "average daily rate"],
    # Retail — confirmed live on Trent's real Q1 FY27 deck: a clean
    # single-panel "TRENT AT A GLANCE" snapshot (p.4) giving the COMPANY-
    # WIDE total store count, retail area (sq ft) and quarterly revenue in
    # one place, no bar-chart ambiguity. "at a glance" is the disambiguating
    # anchor — "retail area"/"store count" alone also appear on later,
    # per-BRAND "at a glance" pages (Westside p.14, Zudio p.18, Star p.24)
    # using the identical template; "at a glance" is present on the
    # company-wide page only (a real, brand-specific false-positive risk
    # avoided this way, same discipline as every other area's anchor-term
    # tuning this session). Only validated against one company so far —
    # this phrasing is Trent's own template wording, not yet confirmed to
    # generalize to other retailers' decks (a documented, honest limit,
    # same as every other newly-added area here).
    "retail_quarterly_metrics": ["at a glance", "retail area"],
    # Real Estate — confirmed live on Godrej Properties' real Q1 FY27
    # deck: a genuine ROW-based "Sales highlights" table (Particulars /
    # Q1 FY27 / Q1 FY26 / Growth / Q4 FY26 / Growth / FY26 columns) giving
    # Area Sold, Booking Value and Customer Collections with the table's
    # own stated YoY% — as clean as Cement's table. "sales highlights" is
    # the disambiguating anchor; "booking value"/"collections" alone
    # recur across many narrative pages in this deck. Only validated
    # against Godrej's own phrasing so far — Prestige Estates' real deck
    # (checked as a second company) uses entirely different section
    # titles ("Operational Highlights"/no "Booking Value" label at all,
    # a card layout with each figure's own inline YoY% instead of a
    # table) and would NOT be found by these terms, a known, documented
    # cross-company generalization gap, same as Consumer Durables'
    # Voltas-tuned terms not finding Blue Star.
    "realty_quarterly_metrics": ["sales highlights", "booking value", "collections"],
    # Oil & Gas (refiners) — confirmed live on BPCL's real Q1 FY27
    # "Investor Handout" (the standardized Reg-30 format every PSU refiner
    # files): a clean 2-page ROW-based table with a "Gross Refining Margin
    # (GRM)" row giving 4 date-labelled columns (current quarter, YoY
    # prior, QoQ prior, full prior year). IOC's newest filing (May 2026) has no Unicode
    # mapping and OCR finds no GRM text either, but its older Oct-2025
    # Investor Presentation is readable and labels it "GRM (US$/bbl)" —
    # never "Gross Refining Margin" — hence the second anchor term.
    "oil_gas_quarterly_metrics": ["gross refining margin", "grm (us$", "mmscmd", "cng stations", "png connections", "domestic png",
                                  "gas transmission", "gas marketing", "tbtu", "regasification", "capacity utili"],
    # FMCG — company-wide headline "Underlying Volume Growth"/"Underlying
    # Sales Growth" (HUL's results release, p.1: "Revenue Growth 10%,
    # Underlying Volume Growth 5%") or "India Volume Growth" (Dabur).
    # Segment-level UVG lines (Home Care/Foods...) recur on later pages and
    # are deliberately not the target — the prompt asks for the company total.
    # Healthcare (hospitals + pharma) — see the "healthcare" prompt. Anchors are
    # the KPI names themselves; hospital ARPOB/occupancy sit in charts on most
    # decks, so this area is live-UNVALIDATED (see quarterly_operating_metrics_
    # ingestion.py docstring) and relies on the prompt's null-unless-explicit rule.
    "healthcare_quarterly_metrics": ["arpob", "bed occupancy", "us formulations", "us business sales",
                                      "us revenue", "occupancy"],
    "services_quarterly_metrics": ["load factor", "passengers", "cargo volume", "container", "teu", "shipments",
                                   "headcount", "attrition", "order book", "order backlog", "fleet utili",
                                   "time charter", "toll", "traffic"],
    "it_quarterly_metrics": ["attrition", "constant currency", "headcount", "utilization", "utilisation",
                             "total contract value", "tcv", "top 10 clients", "top 5 clients", "workforce strength"],
    "utilities_quarterly_metrics": ["order book", "order backlog", "order inflow", "tonnes per day", "tpd", "mld",
                                    "waste processed", "treatment capacity", "customers", "collection efficiency"],
    "power_quarterly_metrics": ["plant load factor", "plf", "installed capacity", "operational capacity", "generation",
                                "availability", "cuf", "transmission system availability", "at&c loss", "million units"],
    "telecom_quarterly_metrics": ["arpu", "average revenue per user", "churn", "customer base", "tower base",
                                  "co-location", "data usage per customer", "subscriber base", "order book"],
    # Banks/NBFCs — a "Key Ratios"/"Financial Highlights" slide (confirmed
    # live on ICICI, Axis, SBI, Kotak, Bajaj Finance, Chola decks: all 6
    # tested had extractable NIM, most also had Cost to Income stated
    # explicitly, e.g. SBI: "NIM (Whole Bank) (%) 2.89 2.81 2.86", "Cost to
    # Income Ratio (%) 47.71 55.09 46.71" side by side by quarter — HDFC
    # Bank's own NSE-attached deck was the one documented miss, a scanned/
    # graphic-only PDF with no text layer at all, same failure mode as
    # UltraTech's deck elsewhere in this registry).
    "banking_quarterly_metrics": ["net interest margin", "nim (whole bank)", "nim (domestic)",
                                  "cost to income", "cost-to-income", "key ratios"],
    "capgoods_quarterly_metrics": ["order backlog", "order book", "order inflow", "order intake",
                                   "order booking", "orders received", "order balance"],
    "fmcg_quarterly_metrics": ["underlying volume growth", "underlying sales growth", "india volume growth",
                               "announced its results", "results for the quarter ended"],
    # ^ the last two anchor the results-release paragraph. Without them the
    # densest page on HUL was a chart page whose unlabelled "10% 7% 10% 5%"
    # extracts scrambled, and the model returned underlying SALES growth as
    # 5 (real: USG 10%, UVG 5%) — caught live, not shipped.
}
# Deliberately narrow to the balance-sheet heading phrase only — "standalone
# financial statements"/"consolidated financial statements" were dropped
# (2026-09-20) after a second, worse false-positive class than the
# page-1-narrative-mention bug already fixed above: on UltraTech Cement's
# real report, "...forms part of the standalone financial statements"
# appears mid-paragraph in a CSR disclosure (p.130) and "...consolidated
# financial statements, taken together" appears mid-paragraph in a BRSR
# reporting-boundary disclosure (p.169) — both narrative, both hundreds of
# pages before the real sections, and both immune to the "require
# standalone-before-consolidated" ordering fix since each phrase's OWN
# narrative false-positive precedes its own genuine section. "standalone
# balance sheet"/"consolidated balance sheet" never appear in prose (only
# as an actual table heading), confirmed clean on UltraTech (standalone:
# first hit p.189, real section p.199; consolidated: first hit p.252, both
# with a large gap before the next section and no earlier false hits) and
# re-confirmed unchanged on Pidilite/Aarti (the reports this file's
# standalone-first-gating fix was originally validated against).
_STANDALONE_MARKERS = ["standalone balance sheet"]
_CONSOLIDATED_MARKERS = ["consolidated balance sheet"]

# Per-area override of the default window_size (see locate_sections) — the
# banking areas were tuned at 20 against HDFC's real report and stay there
# untouched. "ppe"/"other_liabilities" need a much narrower window: their
# terms ("other liabilities", "gross carrying amount", "accumulated
# depreciation") are common enough that a wide window lets an isolated
# concentrated note (the real schedule, usually 1-2 pages) lose the density
# contest to a WIDER but thinner spread of unrelated mentions elsewhere
# (confirmed live: TCS's related-party disclosure section mentions
# "deferred revenue"/"other liabilities" 1-2x each across ~15 pages, which
# outscored the real note's single concentrated page under window=20).
# window=5 confirmed correct on both TCS (page 207) and Coforge (page 116)
# — two real reports with genuinely different note phrasing.
_AREA_WINDOW_SIZE = {
    "ppe": 5, "other_liabilities": 5,
    # Same narrow-window reasoning as ppe/other_liabilities — each of these
    # is a 1-2 page concentrated note on real reports (confirmed on
    # Pidilite), so a wide window risks losing the density contest to a
    # thin scatter of unrelated mentions elsewhere.
    "raw_material": 5, "energy_cost": 5, "revenue_geography": 5, "rd_expenditure": 5,
    "cement_operating_metrics": 5, "paper_operating_metrics": 5, "metals_operating_metrics": 5,
    "automobile_operating_metrics": 5,
    "cement_quarterly_metrics": 5, "metals_quarterly_metrics": 5, "paper_quarterly_metrics": 5,
    "chemicals_quarterly_metrics": 5, "consumer_durables_quarterly_metrics": 5,
    "hotels_quarterly_metrics": 5, "retail_quarterly_metrics": 5,
    "realty_quarterly_metrics": 5, "oil_gas_quarterly_metrics": 5, "fmcg_quarterly_metrics": 5, "healthcare_quarterly_metrics": 5, "capgoods_quarterly_metrics": 5, "it_quarterly_metrics": 5, "telecom_quarterly_metrics": 5, "power_quarterly_metrics": 5, "utilities_quarterly_metrics": 5, "services_quarterly_metrics": 5, "banking_quarterly_metrics": 5,
    # Deliberately wide (and NOT peak_only, below) — confirmed live on
    # Maruti's real Q1 FY27 deck that the two pages wanted (YoY highlights,
    # domestic/export/segment breakdown) are 7 pages apart, and the whole
    # deck is short enough (~4,600 chars) that a wide window costs nothing.
    "automobile_quarterly_metrics": 10,
}
_DEFAULT_WINDOW_SIZE = 20

# ppe/other_liabilities notes are confirmed 1-2 pages long on both real
# reports tested (TCS, Coforge) — for these, skip the window entirely and
# take only the single highest-hit page plus a tight ±1 margin. This isn't
# just a budget optimization: confirmed live that sending the full 5-page
# windowed selection (6 concatenated pages, several of them irrelevant)
# measurably WORSENED Groq's extraction accuracy on TCS's real PPE table —
# it went from 4/5 fields correct with just the one real page to mostly
# null with the wider selection, and separately blew Groq's account-level
# 8000-tokens-per-minute rate limit once the wider text needed a larger
# char budget to avoid truncating the real table out. Precision beats
# recall here — the model does better with less, more targeted text.
_AREA_PEAK_ONLY = {"ppe", "other_liabilities",
                   "raw_material", "energy_cost", "revenue_geography", "rd_expenditure",
                   "cement_operating_metrics", "paper_operating_metrics", "metals_operating_metrics",
                   "automobile_operating_metrics",
                   "cement_quarterly_metrics", "metals_quarterly_metrics", "paper_quarterly_metrics",
                   "chemicals_quarterly_metrics", "consumer_durables_quarterly_metrics",
                   "hotels_quarterly_metrics", "retail_quarterly_metrics",
                   "realty_quarterly_metrics", "oil_gas_quarterly_metrics",
                   "fmcg_quarterly_metrics", "healthcare_quarterly_metrics", "capgoods_quarterly_metrics", "it_quarterly_metrics", "services_quarterly_metrics", "telecom_quarterly_metrics", "power_quarterly_metrics", "utilities_quarterly_metrics"}
                   # automobile_quarterly_metrics deliberately excluded — see its
                   # _AREA_WINDOW_SIZE comment above.


def locate_sections(
    pdf_bytes: bytes, max_pages_per_area: int = 8, window_size: int | None = None, x_tolerance: float = 3,
) -> tuple[dict[str, list[int]], dict[str, str]]:
    """Scan every page once, return ({area: [0-indexed page numbers]},
    {area: "STANDALONE"|"CONSOLIDATED"|"UNKNOWN"}), pages capped per area.
    Prefers pages before the first "consolidated" marker (i.e. within the
    standalone financials) when both standalone and consolidated sections
    exist, for consistency with the BSE pipeline's standalone-only figures —
    falls back to whatever's found if that boundary isn't detected.

    The second dict is what makes that preference an explicit, checkable
    fact rather than an unstated assumption (real bug fixed 2026-09-20:
    every `metric_store.insert_metric_value()` call in
    `annual_report_ingestion.py` previously relied on `statement_type`'s
    bare default, "STANDALONE", regardless of which pages were actually
    selected — correct on every real report tested so far purely because
    Indian annual reports consistently put the standalone section first,
    but silently wrong for a company where the standalone-side candidates
    don't exist for a given area, e.g. because a company's PPE note happens
    to only be found on the consolidated side even though its Other
    Liabilities note is on the standalone side — each area's real
    provenance now travels with it instead of being assumed uniform).
    Per-area, not one global value, because each area's own candidate pages
    are independently filtered to the standalone side (or not) below —
    two areas from the same report can genuinely resolve differently.

    Selecting the raw first N hits in page order is wrong in practice: these
    terms also appear scattered as narrative one-liners in the early
    Management Discussion & Analysis section ("our capital adequacy ratio
    was X%"), well before the actual audited notes-to-accounts schedules
    that carry the real breakdowns — confirmed on HDFC's real annual report,
    where naive first-N picked MD&A pages instead of the notes section 300+
    pages later. Instead this finds the `window_size`-page window with the
    highest total hit count per area (a proxy for "the dense tabular notes
    section," not "the first passing mention") and selects pages from there.

    `window_size` left `None` (the default) uses `_AREA_WINDOW_SIZE`'s
    per-area override where one exists, else `_DEFAULT_WINDOW_SIZE` — pass
    an explicit value to force the same window for every area regardless
    (mainly useful for testing).
    """
    hits: dict[str, list[tuple[int, int]]] = {area: [] for area in _AREA_TERMS}  # (page_idx, hit_count)
    standalone_start: int | None = None
    consolidated_start: int | None = None

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = (page.extract_text(x_tolerance=x_tolerance) or "").lower()
            if not text:
                continue
            # Real bug caught live 2026-09-20 on UltraTech Cement: its Table
            # of Contents (p.31) lists both "Standalone Financial
            # Statements" and "Consolidated Financial Statements" as
            # adjacent page-number entries — a page matching BOTH markers
            # simultaneously is a strong signal of a TOC/index page, not a
            # genuine section transition (the real sections are hundreds of
            # pages apart and never mention each other's heading on the
            # same page). Skip such a page entirely rather than letting it
            # resolve both markers to the same too-early page — confirmed
            # this was silently mislabelling every area "CONSOLIDATED" for
            # this report.
            if (any(m in text for m in _STANDALONE_MARKERS)
                    and any(m in text for m in _CONSOLIDATED_MARKERS)):
                continue
            if standalone_start is None and any(m in text for m in _STANDALONE_MARKERS):
                standalone_start = i
            # Real bug caught live 2026-09-20 on Pidilite Industries: a bare
            # "consolidated financial statements" match fired on PAGE 1 —
            # a Notice/Board's-Report narrative mention ("...the audited
            # consolidated financial statements of the company for the
            # financial year ended..."), nowhere near the real section
            # transition 200+ pages later. `consolidated_start` used to
            # only gate PAGE SELECTION (a too-early value just meant the
            # "prefer standalone" filter silently never matched anything,
            # and per-area page selection still happened to land correctly
            # by coincidence — peak-density naturally favours the earlier,
            # canonical standalone note over a single later consolidated
            # duplicate). It went from harmless-by-luck to actively wrong
            # the moment it started also LABELLING those same pages
            # "CONSOLIDATED" for provenance (this file's own
            # statement_types return value) — confirmed live: real
            # standalone pages (Note 37 "Power and Fuel", p.210) got
            # tagged CONSOLIDATED in the ledger. Fix: only trust a
            # "consolidated" marker as the real transition once we've
            # already seen a genuine "standalone financial statements"
            # marker first — the narrative Notice/Board's-Report mention
            # always precedes the actual standalone section, so gating on
            # that order rules it out without needing to guess at heading
            # formatting pdfplumber's plain-text extraction discards anyway.
            if (standalone_start is not None and consolidated_start is None
                    and any(m in text for m in _CONSOLIDATED_MARKERS)):
                consolidated_start = i
            for area, terms in _AREA_TERMS.items():
                count = sum(text.count(term) for term in terms)
                if count:
                    hits[area].append((i, count))

    result: dict[str, list[int]] = {}
    statement_types: dict[str, str] = {}
    for area, page_counts in hits.items():
        used_standalone_filter = False
        if consolidated_start is not None:
            standalone = [(p, c) for p, c in page_counts if p < consolidated_start]
            if standalone:
                page_counts = standalone
                used_standalone_filter = True

        if area in _AREA_PEAK_ONLY:
            result[area] = _peak_pages(page_counts, max_pages_per_area)
        else:
            effective_window = window_size if window_size is not None else _AREA_WINDOW_SIZE.get(area, _DEFAULT_WINDOW_SIZE)
            result[area] = _densest_window_pages(page_counts, effective_window, max_pages_per_area)

        if not result[area]:
            statement_types[area] = "UNKNOWN"
        elif consolidated_start is None:
            # No "consolidated" marker found anywhere in the document — most
            # likely a company with only one set of financial statements,
            # not a genuine standalone/consolidated split to get wrong.
            statement_types[area] = "STANDALONE"
        elif used_standalone_filter:
            statement_types[area] = "STANDALONE"
        else:
            # Real candidates only ever existed on the consolidated side for
            # THIS area, even though other areas in the same report may have
            # resolved to STANDALONE above.
            statement_types[area] = "CONSOLIDATED"

    return result, statement_types


def _peak_pages(page_counts: list[tuple[int, int]], max_pages: int) -> list[int]:
    """Precision-focused alternative to `_densest_window_pages` — see
    `_AREA_PEAK_ONLY`'s comment for why. Takes the single page with the
    most term hits (ties broken by earliest page, matching scan order —
    correct in practice: a document's standalone note comes before its
    consolidated duplicate, which the caller's own standalone-preference
    filter already narrowed to anyway), plus a tight ±1 page margin for
    a table that spills onto an adjacent page."""
    if not page_counts:
        return []
    peak_page, _ = max(page_counts, key=lambda pc: pc[1])
    padded = set(range(max(0, peak_page - 1), peak_page + 2))
    return sorted(padded)[:max_pages]


def _densest_window_pages(page_counts: list[tuple[int, int]], window_size: int, max_pages: int) -> list[int]:
    if not page_counts:
        return []
    best_start, best_score = page_counts[0][0], -1
    for start, _ in page_counts:
        end = start + window_size
        score = sum(c for p, c in page_counts if start <= p < end)
        if score > best_score:
            best_start, best_score = start, score
    hit_pages = [p for p, _ in page_counts if best_start <= p < best_start + window_size]

    # A heading term often appears once, with the actual table continuing
    # onto pages that don't repeat it — pad a small margin around each hit
    # so continuation pages come along, rather than returning only the exact
    # pages that happened to contain the search text.
    padded = set()
    for p in hit_pages:
        padded.update(range(p, p + 3))
    return sorted(padded)[:max_pages]
