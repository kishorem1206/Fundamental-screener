"""Quarterly Sector KPI Extraction Engine (2026-09-20) — the quarterly
counterpart to `annual_report_ingestion.py`'s per-sector "operating
metrics" areas, sourced from a different document type entirely: NSE
quarterly Investor Presentation filings
(`app/ingestion/nse_investor_presentation_client.py`), not annual reports.

Why a separate module rather than adding areas to annual_report_ingestion.py:
that module's own docstring declares it "THE Annual Report Extraction
Engine" for a reason — its Area Registry, fallback-LLM guard, and
statement-type resolution are all annual-report-specific machinery. This
module reuses the same underlying primitives (pdfplumber text extraction,
`annual_report_locator.locate_sections()`'s keyword-density page finder —
genuinely document-type-agnostic despite the module name, see its own
docstring cross-reference) but keeps its own prompt/metric-field registry,
since the DOCUMENT is different and the caller already knows the
company's sector in advance (no need to "try every area and see what
matches" the way the annual engine must, serving every sector uniformly).

SOURCE CASCADE (2026-09-20): `ingest_quarterly_operating_metrics()` tries the
Investor Presentation first, then the NSE results press release
(`_ingest_from_filing("press")`, source NSE_PRESS_RELEASE), then the latest
earnings-call transcript (source NSE_CONCALL, capped at MEDIUM confidence) —
each layer only when the previous yielded nothing. A hand-read comparison of
all four NSE document types across 8 hospital operators (Q1 FY27) found:
press releases carry clean KPI tables with year-ago/prior-quarter columns
(Medanta, Rainbow, KIMS, Max); decks fill the rest (Fortis, KIMS occupancy,
Aster); transcripts corroborate; outcome-of-board-meeting filings contain
financial statements only, no operating KPIs. Motivation, measured on real filings: decks
put KPIs in charts (scrambled text, unit-inconsistent), but the same
managements state them in plain prose on the call — Max Healthcare "ARPOB
for the quarter stood at INR 77,900", Medanta "ARPOB ... INR 66,550",
Aster "blended occupancy ... 64%", Britannia's CFO "volume growth ... close
to 9%". Not yet wired (candidates, same pattern): NSE results press
releases and the outcome-of-board-meeting filings.

Sector coverage, confirmed live against real Q1 FY2026-27 decks before
writing any extraction prompt (same discipline as every annual-report
area this session):

- **Automobile** (Maruti Suzuki): the attached PDF IS the real 14-page
  deck. A clean "Highlights of Q1 FY'27 w.r.t. Q1 FY'26"/"...w.r.t. Q4
  FY'26" table gives current-quarter units sold + BOTH a YoY and a QoQ
  prior-quarter comparison, already computed — better than the annual
  area's single prior-year field.
- **Cement** (Ambuja Cements): also directly attached, 39 pages, but a
  real bug found and fixed live: the FIRST page tried (a "Consolidated
  Highlights" bar-chart strip showing Sales Volume/Cement Cost/EBITDA as
  3 side-by-side mini-charts) extracts as a scrambled 9-number sequence
  with no recoverable column mapping — confirmed with an actual primary-
  model LLM call returning sales_volume=1,069 (an order of magnitude
  wrong; that's really the OTHER metric's prior-year value). Retargeted
  at a proper ROW-based table instead ("Quarter Ended / Particulars UoM /
  Volume MnT ... EBITDA (PMT)", p.22 Consolidated / p.25 Standalone) —
  every row's own stated YoY/QoQ % change independently verifies against
  its own numbers, confirmed this format is genuinely reliable, and a
  second live LLM call on it returned an exact match. No cost-per-tonne
  row exists in this cleaner table, so `qtr_cost_per_tonne` is always
  derived (realisation - ebitda) for this sector, never directly reported.
- **Metals** (JSW Steel): the NSE-attached PDF is a cover letter pointing
  at the real deck on the company's own website — resolved automatically
  by `nse_investor_presentation_client.fetch_investor_presentation()`.
  The real 60-page deck has a genuine "Q1 FY27 Production & Sales" table
  with current + YoY-prior volumes.
- **Paper**: no real presentation found for any Paper-sector company in a
  120-day lookback (TNPL, JK Paper both file zero "Investor Presentation"
  filings) — a real, structural sector gap (smaller-cap paper companies
  generally don't run an investor-relations deck program), not a bug.
  The area is still built below (in case some paper company does file
  one, now or later), just unvalidated live.
- **Chemicals/Specialty Chemicals** (Aarti Industries): a genuinely weaker
  case than the other 4 — `ChemicalsSector`'s annual metrics are all
  cost/revenue RATIOS, not physical volumes, so there's no company-wide
  "units produced" figure to look for. Confirmed live: Aarti's deck has a
  "Business Volumes (Q1)" section giving YoY/QoQ growth % per business
  segment (Energy / Non-Energy), not a single aggregate — this area
  extracts the PRIMARY segment's growth only (confirmed exact live:
  "Energy" segment, +57% YoY, matching the deck verbatim), stored under
  the same final `qtr_volume_growth_yoy` key the other sectors use, for
  cross-sector dashboard consistency. SRF's deck has no comparable volume
  section at all — a documented miss, same as everywhere else.
- **Consumer Durables** (Voltas): the attached filing is a 7-page
  MD&A-style earnings note (not a slide deck), narrative like Chemicals'
  but a stronger single-page signal — the same paragraph states both the
  primary segment's (Room Air Conditioners) YoY volume growth ("RAC
  volumes grew 45% year on year") and its market share ("achieved a 17.3%
  secondary market share"), confirmed exact live. Stored under the shared
  `qtr_volume_growth_yoy` key plus a new `qtr_consumer_durables_market_share`
  key (mirroring Automobile's `qtr_automobile_market_share`) — directly
  fills the two `available_from_yfinance=False` fields in
  `app/sectors/consumer_durables.py` (`volume_growth_yoy`, `market_share`).
- **Hotels & Restaurants** (Chalet Hotels): a genuine ROW-based table
  ("Hospitality: Geography/Segment wise performance", a "Combined
  Portfolio" total row), like Cement's — confirmed exact live: ADR
  13,247/12,207 (Q1 FY27/FY26), Occupancy 64.8%/66.0%, RevPAR 8,582/8,059,
  all matching the deck's own stated YoY%. Indian Hotels' (IHCL) own deck
  was checked and rejected — its only occupancy/ADR/RevPAR content is a
  multi-panel bar-chart infographic, the same failure mode as the
  rejected Ambuja Cement page. Fills the three NA fields in
  `app/sectors/hotels.py` (`occupancy_rate`, `arr`, `revpar`); `sssg`
  is a QSR/restaurant metric under this same framework, not addressed
  here — no restaurant-chain deck was checked this round.
- **Retail** (Trent): a clean single-panel company-wide "AT A GLANCE"
  snapshot (store count, retail area, quarterly revenue), not a bar-chart —
  confirmed exact live with the PRIMARY model: store_count=1,312,
  retail_area_sqft=18,040,000 (correctly converted from "18.04 Mn sq ft"),
  revenue_cr=5,666, sssg_pct=null (correctly recognized as qualitative-
  only, see below). An earlier attempt this same session hit the Groq
  daily-quota fallback guard mid-run and was correctly blocked from
  storage — the smaller fallback model had confused "City Presence" (330)
  with store count (1,312), a real, observed wrong-label error the guard
  exists to catch, not a hypothetical one. SSSG is frequently disclosed
  only as vague qualitative text (confirmed live: Trent's own deck says
  "low single digits", no number) — a genuine, documented gap, not a bug.
  `store_count_growth_yoy` is derived from our OWN prior-year ledger value
  (no same-deck YoY pair exists here, unlike every other sector's prompt),
  so it stays null until a second year of quarterly ingestion accumulates.
- **Media & Entertainment**: checked live, NOT built — a genuine,
  structural sector gap, not an oversight. `MediaSector`'s NA fields
  (`subscription_revenue_pct`, `subscriber_count_growth`,
  `content_cost_to_revenue`, `arpu`) are all subscription/OTT-flavored,
  but none of the real subscription-relevant companies (Zee
  Entertainment, Sun TV, Nazara Technologies, Network18) file ANY NSE
  "Investor Presentation" filing in a 120-day lookback — a genuine gap in
  this document type for this sector, same class of finding as Paper's
  "no real candidate" (see above). The one company that does file one
  with content resembling these metrics, Saregama, only has a 9-quarter
  Revenue/EBITDA%/Net-Margin% bar-chart infographic with garbled
  column/period ordering in raw pdfplumber text extraction (the same
  failure mode as the rejected Ambuja Cement and IHCL bar-chart pages) —
  not targeted, consistent with this engine's "never fabricate" discipline
  under fabrication risk. PVR INOX's deck (the only other real filing
  found) has no content matching any of `MediaSector`'s current metrics
  at all. No locator area/prompt/`_SECTOR_CONFIG` entry was added for this
  sector.
- **Real Estate** (Godrej Properties): a genuine ROW-based "Sales
  highlights" table — confirmed exact live: Booking Value 8,651/7,082
  Cr, Customer Collections 4,348/3,670 Cr (Q1 FY27/FY26), matching the
  table's own stated YoY%. A third field (total launches area) was tried
  and DROPPED after a real, caught fabrication: the primary model
  invented a launches figure (3.63 million sq ft) that does not appear
  anywhere in the source text — confirmed by direct string search, not a
  misread of a real number. `launch_pipeline_msf` stays unaddressed as a
  result; only `pre_sales_value` and (derived) `collections_growth_yoy`
  are filled. Prestige Estates was checked as a second company (a
  different but structurally comparable card-style layout) — confirmed
  exact live with the primary model: booking value 6,126.6 Cr, collections
  4,391.4 Cr, both correctly converted from "₹ Mn" and correctly preferring
  the company's own "PG Share" figure over the gross group-wide "Sales"
  figure shown alongside it, exactly as instructed. yoy_prior fields
  correctly returned null for Prestige — its deck states only the YoY %
  inline, not the absolute prior-period value, and the model declined to
  back-calculate one rather than risk a derived figure presented as
  REPORTED. An earlier attempt against this same deck had hit the Groq
  quota fallback guard, which correctly blocked storage — the fallback
  model had failed the Mn->Cr conversion and picked the wrong row for the
  since-dropped launches field.
- **Oil & Gas** (BPCL): the standardized Reg-30 "Investor Handout" format
  every PSU refiner files — a clean, tiny (2-page) ROW-based table with a
  single "Gross Refining Margin (GRM)" row and 4 explicit date-labelled
  columns — confirmed exact live: 41.41 / 4.88 / 17.53 US$/bbl (Q1 FY27 /
  Q1 FY26 / Q4 FY26). The Q1 FY27 figure is unusually high vs BPCL's own
  recent history (4.88, 17.53, 11.74 FY26 full year) — extracted exactly
  as reported rather than second-guessed; whether it's a genuine spike or
  needs cross-checking is a scoring/interpretation concern, not an
  extraction one. IOC's most recent filing (Q4 FY26, May 2026) has no
  Unicode mapping (raw glyph IDs from pdfplumber) AND OCR (tesseract, via
  app/ingestion/pdf_ocr.py) recovers no GRM text either — the graphic
  handout doesn't carry it as recoverable text, so OCR was tried and is
  NOT a fix. IOC's older Q2 FY26 "Investor Presentation" (Oct 2025) IS
  text-readable and works: "GRM (US$/bbl) 10.66 2.15" — confirmed exact
  live (current=10.66, QoQ prior=2.15, YoY null since that deck only
  shows the prior quarter), which also exposed a real period-parse bug
  (IOC's "Q2 FY 25-26" span label was read as FY25, dating it a year
  early — fixed in _QUARTER_LABEL_RE). The locator also needed a second
  anchor ("grm (us$") since IOC never spells out "Gross Refining Margin".
  Neither
  "standalone" nor "consolidated" appears anywhere in BPCL's handout, so
  `_resolve_statement_type()`'s existing CONSOLIDATED default applies —
  a real ambiguity in the source document itself (PSU refiner handouts
  are commonly understood as standalone-primary by market convention, but
  that convention isn't stated in the document), left as-is rather than
  special-cased for one company against the shared, already-documented
  default every other sector also relies on.
- **FMCG** (Hindustan Unilever, Dabur): the company-wide headline growth
  figures, stated in the results-release paragraph — confirmed exact live
  on HUL ("Underlying Volume Growth 5%", "Underlying Sales Growth 10%") and
  Dabur ("5% India Volume Growth"). Price/mix is DERIVED as (1+USG)/(1+UVG)-1
  (CALCULATED, never REPORTED) and only when both are stated. A real
  error was caught and fixed: HUL's densest page was a chart whose
  unlabelled "10% 7% 10% 5%" extracts scrambled, and the model returned
  underlying SALES growth as 5 (real: 10, with UVG 5); the locator now
  anchors on the results-release paragraph and the prompt says to return
  null for chart-only figures. Nestle (annual volume chart only) and Colgate
  (MAT category growth, not company growth) correctly return nothing;
  Britannia/Emami state no numeric UVG in the DECK, and Marico/Godrej
  Consumer/ITC file no deck at all — but those gaps are closed through the
  OTHER document type: management states these figures on the earnings
  call. `earnings_call_client._EXTRACTION_JOBS["fmcg"]` extracts
  volume_growth_yoy / premiumization_pct / rural_revenue_pct from the
  transcript (strict prompt: management-stated, current-quarter,
  whole-company, no guidance/CAGR/analyst-question numbers). Confirmed
  live with the primary model, each checked by string search in the real
  transcript: Britannia volume growth 9% (CFO: "close to 9%") and Nestle
  premium portfolio 14% of sales ("from 11% to 14%"). Godrej Consumer,
  HUL, Colgate and Emami transcripts still need their live run (Groq
  daily quota ran out mid-session; the fallback guard correctly refused
  to store those). Tata Consumer's deck states "13% underlying volume
  growth" and is queued for the deck path the same way.
- **Healthcare** (hospitals + pharma): the LLM path is live-UNVALIDATED (the
  Groq daily quota was exhausted before any primary-model run), but the
  ground truth now exists: all 8 hospital operators' Q1 FY27 occupancy and
  ARPOB were READ BY HAND from their NSE press release / deck / transcript,
  cross-checked across documents, and stored in the ledger (source MANUAL,
  quote + corroboration recorded) — Max 75% / Rs 81,900; Medanta 62.6% /
  70,244 (the release's own prose says 70,224, a typo; table and transcript
  agree); Fortis 68.7% / 74,247 (from Rs 2.71 Cr per annum); KIMS 49.0% /
  47,200; Apollo 70% (ARPOB not reported — ARPP only); Aster 64% (ARPP
  only); Rainbow 41.24% / 67,256; Narayana ARPOB 52,603 (from Rs 19.2 Mn,
  annual unit assumed), no occupancy. Use them to grade the LLM path once
  quota resets. Original note: the
  codebase's rule is that a figure isn't trusted until checked against the
  source. TRANSCRIPT CASCADE covers the hospital gap: Max, Medanta, Aster
  state occupancy/ARPOB in prose (live-probed with regex, not yet through
  the LLM — same quota reason). What the live scan of 22 real decks
  established: hospitals
  (Fortis, Medanta, KIMS, Aster, Max) do carry ARPOB and occupancy, but in
  charts with unit differences (Fortis: INR Cr per bed per YEAR; Aster: one
  cluster only; Medanta/KIMS: ARPOB interleaved with ARPP/occupancy);
  Apollo reports revenue per in-patient, not ARPOB. Pharma US share is
  explicit prose for Aurobindo ("US revenue ... 40.0% of consolidated
  revenue") and Alkem ("21.7% to total sales") but a chart or absolute figure
  for Cipla/Dr Reddy's/Lupin/Zydus. The prompt therefore returns null unless
  a figure is explicit, company-wide and in the right unit. Re-run against
  Aurobindo/Alkem (US %) and a hospital with a clean card once the quota
  resets before relying on it. Sun Pharma, Torrent (unreadable PDF),
  Divi's (no deck), Lal Path Labs and Metropolis show none of these KPIs.

Every extracted absolute figure gets combined with the quarterly financial
ledger (`qtr_sales`/`qtr_operating_profit`, already populated by
`app/ingestion/quarterly_results_client.py`'s Tier-1 Screener ingestion,
same quarter) to derive per-tonne/unit ratios — mirroring exactly the
"compute in the ingestion layer, not in the sector framework" pattern the
annual engine's ratio blocks already use, just quarterly-cadence inputs
throughout instead of annual ones.

Metric-key namespace: every field here is `qtr_`-prefixed, matching the
Tier-1 quarterly engine's own convention and the same "TTM"/date-collision
lesson `pnl_history_client.py`/`quarterly_results_client.py` already
codify (never reuse an annual metric_key for quarterly data). The FINAL
derived ratios (`qtr_capacity_utilization`, `qtr_ebitda_per_tonne`,
`qtr_cost_per_tonne`, `qtr_realisation_per_tonne`, `qtr_volume_growth_yoy`)
intentionally mirror the annual engine's metric names with a `qtr_`
prefix — same per-tonne-commodity-economics vocabulary, different cadence,
never mixed together (a sector's scored `ebitda_per_tonne` stays annual-
sourced; `qtr_ebitda_per_tonne` is a separate, quarterly-trend figure,
surfaced through the quarterly dashboard, not blended into sector
scoring).
"""
from __future__ import annotations

import io
import re
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone

import pdfplumber
from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.ingestion import nse_client
from app.ingestion import nse_investor_presentation_client as ipc
from app.ingestion.nse_concall_client import find_transcript_filings
from app.ingestion.annual_report_locator import locate_sections
from app.llm.client import llm_client as default_llm_client
from app.logger import logger

_MAX_TOKENS = 3000

# Which document the values being stored came from. The cascade below tries
# the Investor Presentation first, then the earnings-call transcript; every
# stored row carries ITS OWN source so provenance is never blurred. Transcript
# figures are capped at MEDIUM confidence (management often rounds/approximates:
# "close to 9%"), decks keep HIGH.
_source_ctx: ContextVar[str] = ContextVar("qomi_source", default="NSE_INVESTOR_PRESENTATION")


def _conf(level: str) -> str:
    return "MEDIUM" if (_source_ctx.get() == "NSE_CONCALL" and level == "HIGH") else level
_MAX_CHARS_PER_AREA = 8000

# "quarter ended <date>" is a consistent, boilerplate regulatory phrase
# (Regulation 30, SEBI LODR) present on essentially every filing's cover
# page — confirmed live on 3 real companies with 2 different date-order
# conventions ("30th June 2026" vs "June 30, 2026"), both handled below.
# Parsed directly via regex rather than asking the LLM — more reliable
# than relying on model extraction for a fixed, consistently-worded field,
# and it's one fewer thing that can go wrong per company.
_QUARTER_END_DMY_RE = re.compile(r"quarter ended\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+),?\s*(\d{4})", re.I)
_QUARTER_END_MDY_RE = re.compile(r"quarter ended\s+([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})", re.I)
# Fallback for decks with no "quarter ended <date>" boilerplate at all —
# real gap found live on JSW Steel: its deck (fetched via the external-link
# fallback, a company-authored deck, not a SEBI Reg-30 filing cover letter)
# has no such phrase anywhere, just a "Q1 FY27 Production & Sales" style
# label deep in the content. "Q_ FY__" -> Indian fiscal-year quarter-end
# date (FY27 = year ending March 2027; Q1 FY27 = Apr-Jun 2026, ends
# 2026-06-30; Q4 FY27 ends 2027-03-31).
# Optional "-26" span suffix handles IOC's "Q2 FY 25-26" style — without it
# the regex read FY25 and dated the quarter a year early (caught live on IOC).
_QUARTER_LABEL_RE = re.compile(r"Q(\d)\s*FY[\'’]?\s*(\d{2,4})(?:\s*[-–]\s*(\d{2,4}))?", re.I)
# No-"FY"-token fallback for decks that label columns "Q1-2027" instead of
# "Q1 FY27" (confirmed live on ICICI Bank's "Key ratios" table: "FY2024
# FY2025 FY2026 Q1-2026 Q1-2027" — same Indian-fiscal-year meaning, just a
# bare 4-digit year with a hyphen). Requires a strict 4-digit year (unlike
# `_QUARTER_LABEL_RE`'s 2-4 digit `FY` group) specifically to keep the
# false-positive rate low with no "FY" anchor to lean on.
_QUARTER_LABEL_NO_FY_RE = re.compile(r"Q(\d)\s*[-–]\s*(\d{4})\b")
_QUARTER_END_MONTH_DAY = {1: (6, 30), 2: (9, 30), 3: (12, 31), 4: (3, 31)}


def _quarter_label_to_period(quarter_num: int, fy_year: int) -> str | None:
    if quarter_num not in _QUARTER_END_MONTH_DAY:
        return None
    if fy_year < 100:
        fy_year += 2000
    month, day = _QUARTER_END_MONTH_DAY[quarter_num]
    year = fy_year if quarter_num == 4 else fy_year - 1
    return datetime(year, month, day).date().isoformat()


def _parse_quarter_end_date(text: str) -> str | None:
    m = _QUARTER_END_DMY_RE.search(text)
    if m:
        day, month, year = m.group(1), m.group(2), m.group(3)
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(f"{day} {month} {year}", fmt).date().isoformat()
            except ValueError:
                continue

    m = _QUARTER_END_MDY_RE.search(text)
    if m:
        month, day, year = m.group(1), m.group(2), m.group(3)
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(f"{day} {month} {year}", fmt).date().isoformat()
            except ValueError:
                continue

    # `finditer` + take the LATEST resulting date, not the first regex
    # match — real bug found live on ICICI Bank's "Key ratios" table
    # ("FY2024 FY2025 FY2026 Q1-2026 Q1-2027", oldest-to-newest columns
    # left to right): `.search()`'s leftmost-match default picked up the
    # prior-year comparison column "Q1-2026" instead of the actual current
    # quarter "Q1-2027" later in the same header row, dating every value
    # from that page a full year early. A dense ratio table with multiple
    # quarter/year columns is exactly the shape `_QUARTER_LABEL_RE` was
    # never tested against before this (every other sector's deck use is a
    # single page-TITLE mention, e.g. "Highlights of Q1 FY'27...").
    periods = []
    for m in _QUARTER_LABEL_RE.finditer(text):
        fy = int(m.group(3)) if m.group(3) else int(m.group(2))
        p = _quarter_label_to_period(int(m.group(1)), fy)
        if p:
            periods.append(p)
    for m in _QUARTER_LABEL_NO_FY_RE.finditer(text):
        p = _quarter_label_to_period(int(m.group(1)), int(m.group(2)))
        if p:
            periods.append(p)
    if periods:
        return max(periods)

    return None


def _resolve_statement_type(text: str) -> str:
    """Checks the deck's own early pages for an explicit "Standalone" or
    "Consolidated Financial Results" title (confirmed live on Maruti
    Suzuki: page 1 literally titled "Q1 FY'27 Standalone Financial
    Results") — defaults to CONSOLIDATED otherwise, matching the majority
    pattern seen live (Ambuja/JSW Steel's decks are consolidated-first,
    with only incidental standalone mentions deeper in)."""
    head = text[:2000].lower()
    if "standalone financial results" in head:
        return "STANDALONE"
    return "CONSOLIDATED"


_AREA_PROMPTS = {
    "banking": (
        "This is a page from an Indian BANK or NBFC's quarterly Investor Presentation. Look for a "
        "'Key Ratios'/'Financial Highlights'/'At a Glance' table or infographic stating the CURRENT "
        "quarter's Net Interest Margin (NIM) — for a bank this may be split into 'NIM (Whole Bank)' and "
        "'NIM (Domestic)'; if both are shown, use 'NIM (Whole Bank)' (or the single overall NIM figure if "
        "there's no domestic/whole-bank split) — and Cost to Income Ratio. Both are percentages. Identify "
        "the CURRENT quarter's column explicitly by its quarter label (e.g. 'Q1 FY27') — do not use a "
        "full-year (FY) column, and do not use a prior-quarter or prior-year column. NBFCs sometimes state "
        "'Cost to Income' as 'Opex to NII' or similar — only extract Cost to Income specifically, leave it "
        "null if not literally present. Extract ONLY numbers unambiguously labelled and matched to the "
        "current quarter — if in doubt, return null rather than guessing. Never invent a number. Respond "
        "with JSON:\n"
        "{\n"
        '  "nim_pct": number|null,\n'
        '  "cost_to_income_pct": number|null\n'
        "}"
    ),
    "automobile": (
        "This is a page from an Indian AUTOMOBILE/VEHICLE OEM company's quarterly Investor "
        "Presentation. Look for a 'Highlights' table comparing the CURRENT quarter against the SAME "
        "quarter last year (YoY) and/or the IMMEDIATELY PRECEDING quarter (QoQ) — identify each column "
        "by its EXPLICIT quarter label (e.g. 'Q1 FY27' vs 'Q1 FY26' vs 'Q4 FY26'), never by position "
        "alone, since column order varies by company. Extract the company's total SALES VOLUME (units) "
        "for each period present. Also look for a directly-stated market share % for the current "
        "quarter, if present. Extract ONLY numbers that are unambiguously labelled — if labels and "
        "numbers can't be reliably matched, return null rather than guessing. Report vehicle counts as "
        "plain whole numbers. If a figure is shown in parentheses like (1,234), that means negative — "
        "convert to -1234. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "units_sold_current_quarter": number|null,\n'
        '  "units_sold_yoy_prior_quarter": number|null,\n'
        '  "units_sold_qoq_prior_quarter": number|null,\n'
        '  "market_share_pct": number|null\n'
        "}"
    ),
    "cement": (
        "This is a page from an Indian CEMENT company's quarterly Investor Presentation. Look for a "
        "proper ROW-based financial table with a 'Particulars' column and named metric rows (e.g. "
        "'Volume', 'EBITDA (PMT)'), and separate DATE columns (e.g. 'Jun'26 | Jun'25 | YoY Change | "
        "Mar'26 | QoQ Change') — NOT a bar-chart-style highlights strip with several metrics stacked "
        "side by side as separate mini-charts (that layout extracts as a scrambled, unreliable number "
        "sequence — if this page looks like that instead of a clean row/column table, return null for "
        "everything rather than guessing). In the real table, find the 'Volume' row (in million tonnes "
        "/ MnT) and the 'EBITDA (PMT)' or 'EBITDA/tonne' row (Rs per tonne) — read each period's value "
        "by matching it to its OWN column header date, not by position. A well-formed table's stated "
        "YoY/QoQ % change should roughly match (current-prior)/prior — use this as a sanity check; if "
        "it doesn't roughly match, you may have misread the columns, so return null instead. Report "
        "volume as plain million-tonne numbers. If a figure is shown in parentheses like (1,234), that "
        "means negative — convert to -1234. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "sales_million_tonnes_current_quarter": number|null,\n'
        '  "sales_million_tonnes_yoy_prior_quarter": number|null,\n'
        '  "sales_million_tonnes_qoq_prior_quarter": number|null,\n'
        '  "ebitda_per_tonne_reported": number|null\n'
        "}"
    ),
    "metals": (
        "This is a page from an Indian METALS/MINING company's (steel, aluminium, copper, zinc, or "
        "mining) quarterly Investor Presentation. Look for a 'Production & Sales' table for the CURRENT "
        "quarter and the SAME quarter last year (YoY) — identify each column by its EXPLICIT quarter "
        "label (e.g. 'Q1 FY27' vs 'Q1 FY26'), never by position alone. Prefer the company's overall "
        "CONSOLIDATED total row if the table breaks out multiple entities/operations (e.g. India + "
        "overseas operations) — do not use a single subsidiary/segment row alone. Extract PRODUCTION "
        "volume and SALES volume in million tonnes. Extract ONLY numbers that are unambiguously "
        "labelled — if labels and numbers can't be reliably matched, return null rather than guessing. "
        "If a figure is shown in parentheses like (1,234), that means negative — convert to -1234. "
        "Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "production_million_tonnes_current_quarter": number|null,\n'
        '  "production_million_tonnes_yoy_prior_quarter": number|null,\n'
        '  "sales_million_tonnes_current_quarter": number|null,\n'
        '  "sales_million_tonnes_yoy_prior_quarter": number|null\n'
        "}"
    ),
    "paper": (
        "This is a page from an Indian PAPER company's quarterly Investor Presentation. Look for the "
        "company's PAPER production/sales volume for the CURRENT quarter, and the SAME quarter last "
        "year if shown — identify each column/figure by its EXPLICIT quarter label, never by position "
        "alone. If the company reports multiple product lines (e.g. Paper AND Packaging Board), use "
        "ONLY the figure specifically labelled 'Paper'. Extract ONLY numbers that are unambiguously "
        "labelled — if labels and numbers can't be reliably matched, return null rather than guessing. "
        "Report volume in plain tonnes (convert 'lakh' to tonnes: 1 lakh = 100,000). If a figure is "
        "shown in parentheses like (1,234), that means negative — convert to -1234. Never invent a "
        "number. Respond with JSON:\n"
        "{\n"
        '  "production_tonnes_current_quarter": number|null,\n'
        '  "production_tonnes_yoy_prior_quarter": number|null,\n'
        '  "sales_tonnes_current_quarter": number|null,\n'
        '  "sales_tonnes_yoy_prior_quarter": number|null\n'
        "}"
    ),
    # ChemicalsSector's annual metrics are all cost/revenue RATIOS, not
    # physical volumes — so unlike Cement/Metals/Paper/Automobile, there's
    # no single "units produced" figure to target. Confirmed live on Aarti
    # Industries: a "Business Volumes (Q1)" section gives YoY/QoQ growth %
    # per business segment (Energy / Non-Energy), not a company-wide
    # absolute figure — this prompt asks for the PRIMARY segment's growth
    # only, accepting that as the best available single number rather
    # than inventing a company-wide aggregate that isn't actually stated
    # anywhere. SRF's deck has no comparable section at all (a documented,
    # accepted per-company miss, same as every other area this session).
    "chemicals": (
        "This is a page from an Indian CHEMICALS/SPECIALTY CHEMICALS company's quarterly Investor "
        "Presentation. Look for a 'Business Volumes' or similar section giving volume growth % for the "
        "CURRENT quarter vs the SAME quarter last year (YoY). If multiple business segments/product "
        "lines are shown side by side (e.g. 'Energy' and 'Non-Energy'), report the PRIMARY one — "
        "whichever is listed FIRST or is described elsewhere as the larger revenue contributor — and "
        "name it. Do not average or combine multiple segments into one number. Also look for an EXPORT "
        "REVENUE % of TOTAL company revenue for the current quarter, if directly and unambiguously "
        "stated at the company level (not a single product's domestic/export split). Extract ONLY "
        "numbers that are unambiguously labelled — if labels and numbers can't be reliably matched, "
        "return null rather than guessing. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "primary_segment_name": "string or null",\n'
        '  "volume_growth_yoy_pct": number|null,\n'
        '  "export_revenue_pct": number|null\n'
        "}"
    ),
    # Like Chemicals, a narrative earnings-note deck, not a table — but a
    # stronger signal: confirmed live on Voltas' Q1 FY27 filing, the same
    # paragraph states both the primary segment's YoY volume growth ("RAC
    # volumes grew 45% year on year") AND its market share ("achieved a
    # 17.3% secondary market share").
    "consumer_durables": (
        "This is a page from an Indian CONSUMER DURABLES company's (air conditioners, refrigerators, "
        "washing machines, consumer electronics, small appliances) quarterly Investor Presentation or "
        "earnings note. Identify the company's PRIMARY revenue-driving product segment (e.g. Room Air "
        "Conditioners, Refrigerators, Washing Machines — whichever is described as the largest or most "
        "significant business) and name it. For that primary segment only, extract its year-on-year "
        "UNIT VOLUME growth % for the CURRENT quarter, if directly and unambiguously stated (e.g. 'RAC "
        "volumes grew 45% year on year' -> 45). Also extract its MARKET SHARE % for the current quarter, "
        "if directly and unambiguously stated (e.g. 'achieved a 17.3% secondary market share' -> 17.3) — "
        "prefer an absolute market share figure over a market-share CHANGE (e.g. '+4 percentage points'). "
        "Do not average or combine multiple segments into one number, and do not confuse company-wide "
        "revenue growth with segment unit-volume growth. Extract ONLY numbers that are unambiguously "
        "labelled — if labels and numbers can't be reliably matched, return null rather than guessing. "
        "Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "primary_segment_name": "string or null",\n'
        '  "volume_growth_yoy_pct": number|null,\n'
        '  "market_share_pct": number|null\n'
        "}"
    ),
    # Confirmed live on Chalet Hotels' real Q1 FY27 deck: a genuine
    # ROW-based table with a "Combined Portfolio" total row — reliable,
    # like Cement's row-based table, unlike IHCL's bar-chart infographic
    # (rejected as a locator target, see annual_report_locator.py).
    "hotels": (
        "This is a page from an Indian HOTELS/HOSPITALITY company's quarterly Investor Presentation. Look "
        "for a ROW-based performance table (metric names as rows, e.g. 'Average Daily Rate', 'Occupancy', "
        "'RevPAR') with DATE columns for the CURRENT quarter and the SAME quarter last year (YoY) — "
        "identify each column by its EXPLICIT quarter label (e.g. 'Q1 FY27' vs 'Q1 FY26'), never by "
        "position alone. If the table breaks results out by geography/segment/brand, use ONLY the "
        "'Combined Portfolio' or company-wide TOTAL row — never an individual city/region/brand row. A "
        "well-formed table's stated YoY % change should roughly match (current-prior)/prior — use this as "
        "a sanity check; if it doesn't roughly match, you may have misread the columns, so return null "
        "instead. Extract ONLY numbers that are unambiguously labelled — if labels and numbers can't be "
        "reliably matched, return null rather than guessing. Report Occupancy as a plain percentage "
        "number (e.g. 64.8, not 0.648). Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "adr_current_quarter": number|null,\n'
        '  "adr_yoy_prior_quarter": number|null,\n'
        '  "occupancy_pct_current_quarter": number|null,\n'
        '  "occupancy_pct_yoy_prior_quarter": number|null,\n'
        '  "revpar_current_quarter": number|null,\n'
        '  "revpar_yoy_prior_quarter": number|null\n'
        "}"
    ),
    # Confirmed live on Trent's real Q1 FY27 deck: a clean single-panel
    # company-wide "AT A GLANCE" snapshot (store count, retail area,
    # quarterly revenue), not a bar-chart. SSSG is frequently disclosed
    # only as vague qualitative text ("low single digits", confirmed on
    # Trent's own deck) rather than a precise number — the prompt
    # explicitly instructs to return null rather than guess a number from
    # qualitative language.
    "retail": (
        "This is a page from an Indian RETAIL company's quarterly Investor Presentation. Look for a "
        "company-wide snapshot section (e.g. 'At a Glance') giving the COMPANY-WIDE TOTAL store count, "
        "TOTAL retail area, and TOTAL revenue for the CURRENT quarter — use the company-wide total, never "
        "an individual brand/format/city breakdown. Convert retail area to plain square feet if shown in "
        "'Mn sq ft' (1 Mn sq ft = 1,000,000 sq ft). Report revenue in ₹ crore as shown. Also look for a "
        "directly-stated Same-Store Sales Growth (SSSG) / Like-for-Like (LFL) growth % for the current "
        "quarter, ONLY if given as an explicit precise number — if it's described only in vague "
        "qualitative terms (e.g. 'low single digits', 'healthy growth') with no number attached, return "
        "null rather than guessing a number. Extract ONLY numbers that are unambiguously labelled. Never "
        "invent a number. Respond with JSON:\n"
        "{\n"
        '  "store_count_current_quarter": number|null,\n'
        '  "retail_area_sqft_current_quarter": number|null,\n'
        '  "revenue_cr_current_quarter": number|null,\n'
        '  "sssg_pct": number|null\n'
        "}"
    ),
    # Confirmed live on Godrej Properties' real Q1 FY27 deck (a clean
    # ROW-based "Sales highlights" table) — exact match on booking value
    # and collections, both current-quarter and YoY-prior. Prestige
    # Estates' real deck (a different but structurally comparable layout:
    # each figure states its own value with its own inline YoY% right
    # next to it, e.g. "SALES ₹65,793 mn (-46% YoY)") was checked as a
    # second company but the only live attempt against it hit the Groq
    # quota fallback guard — correctly blocked (the fallback model failed
    # the Mn->Cr conversion and picked the wrong row for a launches
    # figure that has since been dropped, see below). A THIRD field,
    # "total launches area this quarter", was tried and dropped after a
    # real, caught fabrication: the PRIMARY model (not the fallback)
    # returned a launches figure of 3.63 million sq ft for Godrej that
    # does not appear anywhere in the source text at all — confirmed by
    # direct string search. Godrej's own deck has no single clean "Total
    # Launches" number on the located pages (only per-project booking
    # values under a "Key Launches" heading, and a "Business Development"
    # saleable-area figure that is a genuinely different concept — new
    # project ACQUISITIONS, not launches) — the model filled the gap with
    # an invented number instead of returning null. `launch_pipeline_msf`
    # therefore stays unaddressed for this sector; only pre_sales_value
    # and (derived) collections_growth_yoy are filled. Prestige separates
    # GROSS group sales from the company's own attributable "PG Share" —
    # the prompt asks for the company's own economic share where both are
    # shown, matching this sector's MD-spec emphasis on "Developer
    # Economic Share", not gross project value.
    "realty": (
        "This is a page from an Indian REAL ESTATE DEVELOPER's quarterly Investor Presentation. Look for "
        "the company's BOOKING VALUE / PRE-SALES (total value of new sales/bookings) and CUSTOMER "
        "COLLECTIONS for the CURRENT quarter, whether shown as a ROW-based table with explicit quarter-"
        "labelled columns (e.g. 'Q1 FY27' vs 'Q1 FY26'), or as individual figures each with their own "
        "inline growth % (e.g. 'Collections ₹48,022 mn (+6% YoY)'). If the company shows both a GROSS/"
        "group-wide figure and its own attributable economic share (e.g. 'PG Share' or 'Developer Share'), "
        "use the company's OWN SHARE figure, not the gross group figure. Extract ONLY numbers that are "
        "unambiguously labelled — if labels and numbers can't be reliably matched, return null rather than "
        "guessing. Convert 'INR Mn'/'₹ Mn' to crore (divide by 10) so all figures share one unit. If a "
        "figure is shown in parentheses like (1,234), that means negative — convert to -1234. Never invent "
        "a number. Respond with JSON:\n"
        "{\n"
        '  "booking_value_cr_current_quarter": number|null,\n'
        '  "booking_value_cr_yoy_prior_quarter": number|null,\n'
        '  "collections_cr_current_quarter": number|null,\n'
        '  "collections_cr_yoy_prior_quarter": number|null\n'
        "}"
    ),
    # Confirmed live on BPCL's real Q1 FY27 "Investor Handout" (the
    # standardized Reg-30 format every PSU refiner files) — a clean
    # ROW-based table with a single "Gross Refining Margin (GRM)" row and
    # explicit date-labelled columns.
    "oil_gas": (
        "This is a page from an Indian OIL REFINING company's quarterly Investor Presentation or Investor "
        "Handout. Look for a 'Gross Refining Margin' or 'GRM' row in a ROW-based financial table, with "
        "separate DATE-labelled columns for the CURRENT quarter, the SAME quarter last year (YoY), and the "
        "IMMEDIATELY PRECEDING quarter (QoQ) — identify each column by its EXPLICIT period label (e.g. "
        "'Apr-Jun 2026-27' vs 'Apr-Jun 2025-26' vs 'Jan-Mar 2025-26'), never by position alone, since "
        "column order varies by company. Report GRM in US$/bbl as stated — if the table gives it in a "
        "different currency or unit, return null rather than guessing a conversion. Extract ONLY numbers "
        "that are unambiguously labelled — if labels and numbers can't be reliably matched, return null "
        "rather than guessing. If a figure is shown in parentheses like (1,234), that means negative — "
        "convert to -1234. For a CITY GAS DISTRIBUTION / gas company also extract, for the CURRENT quarter and "
        "the whole company: cgd_volume_mmscmd (total gas sales volume in MMSCMD; convert mmscm per quarter "
        "by dividing by days in the quarter ONLY if the document states the per-day figure, else null), "
        "cng_stations (count), png_domestic_connections_lakh (domestic PNG connections in lakh), "
        "cgd_volume_mmscm (total gas sales volume in the QUARTER in MMSCM as stated), cgd_volume_growth_yoy_pct "
        "(only if stated), cgd_gross_margin_per_scm_inr (Rs per SCM as stated). For a GAS TRANSMISSION/MARKETING or "
        "LNG TERMINAL company also: gas_transmission_mmscmd, gas_marketing_mmscmd, lpg_transmission_tmt, "
        "petchem_production_tmt, lhc_production_tmt (thousand tonnes for the quarter), lng_throughput_tbtu (LNG "
        "processed/regasified, TBtu), regas_utilization_pct (company-wide terminal utilisation as stated), "
        "regas_capacity_mmtpa (nameplate), and revenue_cr / ebitda_cr / capex_cr for the same entity (INR crore). "
        "Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "grm_usd_bbl_current_quarter": number|null,\n'
        '  "grm_usd_bbl_yoy_prior_quarter": number|null,\n'
        '  "grm_usd_bbl_qoq_prior_quarter": number|null,\n'
        '  "cgd_volume_mmscmd": number|null,\n'
        '  "cgd_volume_mmscm": number|null,\n'
        '  "cgd_volume_growth_yoy_pct": number|null,\n'
        '  "cng_stations": number|null,\n'
        '  "png_domestic_connections_lakh": number|null,\n'
        '  "cgd_gross_margin_per_scm_inr": number|null,\n'
        '  "gas_transmission_mmscmd": number|null,\n'
        '  "gas_marketing_mmscmd": number|null,\n'
        '  "lpg_transmission_tmt": number|null,\n'
        '  "petchem_production_tmt": number|null,\n'
        '  "lhc_production_tmt": number|null,\n'
        '  "lng_throughput_tbtu": number|null,\n'
        '  "regas_utilization_pct": number|null,\n'
        '  "regas_capacity_mmtpa": number|null,\n'
        '  "revenue_cr": number|null,\n'
        '  "ebitda_cr": number|null,\n'
        '  "capex_cr": number|null\n'
        "}"
    ),
    # HUL states both headline figures explicitly ("Underlying Volume
    # Growth 5%", "Underlying Sales Growth 10%"); many FMCG decks give only
    # qualitative segment bands ("high single digit") — the prompt returns
    # null for those rather than turning a band into a number.
    "fmcg": (
        "This is a page from an Indian FMCG company's quarterly results release or Investor Presentation. "
        "Extract the COMPANY-WIDE (consolidated / total India business) headline growth figures for the "
        "CURRENT quarter vs the same quarter last year: (1) UNDERLYING VOLUME GROWTH % (also called UVG, "
        "volume growth, or India volume growth) and (2) UNDERLYING SALES GROWTH % (USG; like-for-like "
        "sales growth excluding acquisitions/divestments/currency) if stated. Use ONLY an explicit numeric "
        "percentage for the whole company — never a single segment/category (e.g. Home Care, Foods), never "
        "a full-year or MAT figure, and ONLY trust a figure stated in a sentence/headline that names it (e.g. 'Underlying Volume Growth 5%'); if the numbers appear only in a chart or infographic with unlabelled or interleaved figures, return null. If growth is described only qualitatively (e.g. 'high single "
        "digit', 'low single digit decline', 'double digit') return null for that field. A decline is "
        "negative. Never invent or infer a number. Respond with JSON:\n"
        "{\n"
        '  "underlying_volume_growth_pct": number|null,\n'
        '  "underlying_sales_growth_pct": number|null\n'
        "}"
    ),
    # One prompt for both halves of `PharmaSector` ("Healthcare"): hospital
    # operators and pharma. Every field is optional; a hospital returns nulls
    # for the US field and vice versa. Hospital ARPOB/occupancy are usually in
    # CHARTS with interleaved figures and inconsistent units (live scan: Fortis
    # gives ARPOB in INR Cr per bed per YEAR; Aster's card is one cluster only;
    # Medanta/KIMS charts interleave ARPOB with ARPP and occupancy) — the same
    # failure class as the rejected Ambuja/IHCL bar-chart pages, so the prompt
    # is written to return null unless the figure is explicit, company-wide and
    # in the right unit.
    "healthcare": (
        "This is a page from an Indian HEALTHCARE company's quarterly Investor Presentation (a hospital "
        "operator or a pharma company). Extract ONLY what is explicitly stated for the CURRENT quarter and "
        "the WHOLE company: (1) bed_occupancy_pct - overall bed occupancy % of operational beds (hospitals); "
        "(2) arpob_inr_per_day - ARPOB, average revenue per occupied bed per DAY, in rupees (if given in "
        "'000 or lakh convert to rupees; if it is quoted per YEAR, in crore, per patient (ARPP / average "
        "revenue per in-patient), or for a single city/cluster/facility, return null); (3) "
        "(4) alos_days - average length of stay in days (hospitals); (5) arpp_inr - ARPP, average revenue per "
        "IN-PATIENT (per discharge/inpatient volume, not per bed), in rupees; (6) operational_beds - total "
        "operational (or operating) beds, whole company, as a count. "
        "us_revenue_pct - US (or North America) revenue as an explicit % of TOTAL company revenue (pharma). "
        "Return null for anything shown only in a chart with unlabelled or interleaved figures, anything "
        "ambiguous between metrics (e.g. ARPOB vs ARPP), full-year figures, or segment/brand figures. Never "
        "invent, infer or compute a number. Respond with JSON:\n"
        "{\n"
        '  "bed_occupancy_pct": number|null,\n'
        '  "arpob_inr_per_day": number|null,\n'
        '  "us_revenue_pct": number|null,\n'
        '  "alos_days": number|null,\n'
        '  "arpp_inr": number|null,\n'
        '  "operational_beds": number|null\n'
        "}"
    ),
    # Capital Goods / Industrials / Defence share one prompt. Order figures are
    # disclosed in INR crore, INR million or INR billion depending on the issuer
    # (live scan: ABB India crore, Triveni Turbine billion, Praj million, CG Power
    # crore) so the model must convert to CRORE (1 bn = 100 cr, 1 mn = 0.1 cr).
    # Known traps: segment-only backlogs (CG Power lists per-segment backlog next
    # to the group figure), backlog defined on a rolling forecast basis (Thermax
    # TOESL), and 'order balance' meaning backlog.
    "capgoods": (
        "This is a page from an Indian CAPITAL GOODS / ENGINEERING / DEFENCE company's quarterly results "
        "release or Investor Presentation. Extract ONLY what is explicitly stated for the CURRENT quarter "
        "and the WHOLE company (not one segment): (1) order_inflow_cr - order intake / order booking / "
        "orders received in the quarter; (2) order_inflow_yoy_prior_cr - the same figure for the same "
        "quarter a year earlier, if shown; (3) order_backlog_cr - closing order book / order backlog / "
        "order balance / unexecuted orders at quarter end; (4) order_backlog_yoy_prior_cr - closing backlog "
        "a year earlier, if shown; (5) order_inflow_growth_pct and order_backlog_growth_pct - YoY growth "
        "ONLY if the document states the percentage; (6) revenue_cr - revenue from operations for the SAME "
        "quarter and SAME entity as the order figures; (7) export_order_pct - export share of the quarter's "
        "order intake, only if stated. ALL rupee amounts must be converted to INR CRORE (1 billion = 100 "
        "crore, 1 million = 0.1 crore, 1 lakh crore = 100000 crore). Return null for a utilisation quoted as a range (e.g. 70-75%) or for one plant/line only, for segment-only figures, "
        "half-year or full-year figures, targets/guidance, pipeline/L1/bid figures, and anything shown only "
        "in a chart with unlabelled values. Never invent, infer or compute a number. Respond with JSON:\n"
        "{\n"
        '  "order_inflow_cr": number|null,\n'
        '  "order_inflow_yoy_prior_cr": number|null,\n'
        '  "order_backlog_cr": number|null,\n'
        '  "order_backlog_yoy_prior_cr": number|null,\n'
        '  "order_inflow_growth_pct": number|null,\n'
        '  "order_backlog_growth_pct": number|null,\n'
        '  "revenue_cr": number|null,\n'
        '  "export_order_pct": number|null,\n'
        '  "aftermarket_order_pct": number|null,\n'
        '  "capacity_utilization_pct": number|null,\n'
        '  "international_backlog_pct": number|null\n'
        "}"
    ),
    # IT services / software. Fact sheets and results releases state these
    # explicitly (live scan: Infosys fact sheet, TCS/HCL/TechM releases). Traps:
    # INR vs USD revenue, CC vs reported growth, LTM vs quarterly attrition,
    # utilisation with vs without trainees, segment-only growth (HCL quotes
    # '62.1% YoY CC' for an acquisition-boosted line that is not company-wide).
    "it_services": (
        "This is from an Indian IT SERVICES / software company's quarterly results release, fact sheet or "
        "investor presentation. Extract ONLY what is explicitly stated for the CURRENT quarter and the "
        "WHOLE company: (1) cc_growth_yoy_pct - total revenue growth YoY in CONSTANT CURRENCY (not reported "
        "currency, not INR, not a segment); (2) cc_growth_qoq_pct - same, sequential; (3) revenue_usd_mn - "
        "quarterly revenue in US$ MILLION (convert US$ billion x1000); null if only INR is given; "
        "(4) headcount - total employees at quarter end; (5) attrition_pct - LTM (trailing twelve months) "
        "attrition %, IT services; if voluntary and total both appear use the one the company headlines; "
        "(6) utilization_pct - billable utilisation %, INCLUDING trainees when both are shown; "
        "(7) deal_tcv_usd_bn - TOTAL deal wins / order bookings / TCV for the quarter in US$ BILLION; "
        "(8) large_deal_tcv_usd_bn - TCV of LARGE deal wins only, US$ billion (leave (7) null if only large "
        "deals are stated); (9) top5_client_pct and (10) top10_client_pct - share of revenue from the top 5 / "
        "top 10 clients; (11) north_america_revenue_pct - North America share of revenue; "
        "(12) europe_revenue_pct; (13) bfsi_revenue_pct - BFSI / financial services vertical share; "
        "(14) offshore_effort_pct - offshore share of effort/revenue; (15) million_dollar_clients - count of "
        "US$1 million+ clients. Return null for anything not explicitly stated, for guidance/targets, for "
        "figures of one segment or acquisition only, and for annual figures. Never invent, infer or compute a "
        "number. Respond with JSON:\n"
        "{\n"
        '  "cc_growth_yoy_pct": number|null,\n'
        '  "cc_growth_qoq_pct": number|null,\n'
        '  "revenue_usd_mn": number|null,\n'
        '  "headcount": number|null,\n'
        '  "attrition_pct": number|null,\n'
        '  "utilization_pct": number|null,\n'
        '  "deal_tcv_usd_bn": number|null,\n'
        '  "large_deal_tcv_usd_bn": number|null,\n'
        '  "top5_client_pct": number|null,\n'
        '  "top10_client_pct": number|null,\n'
        '  "north_america_revenue_pct": number|null,\n'
        '  "europe_revenue_pct": number|null,\n'
        '  "bfsi_revenue_pct": number|null,\n'
        '  "offshore_effort_pct": number|null,\n'
        '  "million_dollar_clients": number|null\n'
        "}"
    ),
    # Services -> Services spec: commercial/business services, transport operators
    # (airlines, logistics, shipping) and transport infrastructure (ports, airports,
    # roads) share one prompt; every field is optional and a company returns nulls
    # for the fields of the other industries. Units differ wildly by issuer (crore /
    # million; ASK in millions vs billions), so conversions are stated explicitly.
    "services": (
        "This is from an Indian SERVICES company's quarterly results release, fact sheet, traffic update or "
        "investor presentation (staffing/business services, airline, logistics/courier, shipping, port, "
        "airport or road operator, engineering services). Extract ONLY what is explicitly stated for the "
        "CURRENT quarter and the WHOLE company: (1) headcount - total employees/associates at quarter end; "
        "(2) attrition_pct - LTM or annualised employee attrition %; (3) volume_growth_yoy_pct - YoY growth "
        "in the company's headline physical volume (cargo, TEUs, shipments, tonnage, passengers, ASK) if "
        "stated as a %; (4) capacity_utilization_pct - single company-wide utilisation / load / fleet "
        "utilisation %, never a range or one asset; (5) passengers_mn - passengers carried or handled in "
        "MILLION; (6) load_factor_pct - airline passenger load factor %; (7) ask_bn - available seat "
        "kilometres in BILLION; (8) cask_inr and (9) cask_ex_fuel_inr - airline cost per ASK in rupees; "
        "(10) yield_inr - airline passenger yield in rupees per RPK; (11) cargo_volume_mmt - port/terminal "
        "cargo in MILLION TONNES; (12) container_teu_mn - containers in MILLION TEU (convert lakh/thousand); "
        "(13) shipments_mn - shipments/parcels in MILLION; (14) tce_usd_per_day - shipping time-charter "
        "equivalent in US$ per day; (15) order_inflow_cr and (16) order_backlog_cr - orders won in the "
        "quarter / closing contracted order book in INR CRORE; (17) revenue_cr - revenue from operations for "
        "the same entity in INR crore; (18) tonnage_kt - tonnage handled in THOUSAND tonnes; (19) "
        "realisation_per_tonne_inr - revenue per tonne in rupees; (20) warehouse_area_mn_sqft - warehousing "
        "space under management in MILLION sq ft; (21) aero_yield_per_pax_inr and (22) "
        "nonaero_income_per_pax_inr - airport aeronautical yield / non-aeronautical income per passenger in "
        "rupees; (23) fleet_vessels - owned vessels count and (24) fleet_dwt_mn - owned fleet in MILLION dwt; "
        "(25) tce_crude_usd_per_day, (26) tce_product_usd_per_day, (27) tce_dry_bulk_usd_per_day - the "
        "company's OWN average earnings per day for its crude / product / dry-bulk vessels (not market "
        "indices such as Baltic or Suezmax averages); (28) employee_cost_cr - employee benefit expense for the "
        "quarter in INR crore (same entity as revenue_cr). Return null for anything not explicitly stated, for guidance, "
        "annual/YTD figures, single-asset or single-segment figures, and anything only in a chart. Never "
        "invent, infer or compute a number. Respond with JSON:\n"
        "{\n"
        '  "headcount": number|null,\n'
        '  "attrition_pct": number|null,\n'
        '  "volume_growth_yoy_pct": number|null,\n'
        '  "capacity_utilization_pct": number|null,\n'
        '  "passengers_mn": number|null,\n'
        '  "load_factor_pct": number|null,\n'
        '  "ask_bn": number|null,\n'
        '  "cask_inr": number|null,\n'
        '  "cask_ex_fuel_inr": number|null,\n'
        '  "yield_inr": number|null,\n'
        '  "cargo_volume_mmt": number|null,\n'
        '  "container_teu_mn": number|null,\n'
        '  "shipments_mn": number|null,\n'
        '  "tce_usd_per_day": number|null,\n'
        '  "order_inflow_cr": number|null,\n'
        '  "order_backlog_cr": number|null,\n'
        '  "revenue_cr": number|null,\n'
        '  "tonnage_kt": number|null,\n'
        '  "realisation_per_tonne_inr": number|null,\n'
        '  "warehouse_area_mn_sqft": number|null,\n'
        '  "aero_yield_per_pax_inr": number|null,\n'
        '  "nonaero_income_per_pax_inr": number|null,\n'
        '  "fleet_vessels": number|null,\n'
        '  "fleet_dwt_mn": number|null,\n'
        '  "tce_crude_usd_per_day": number|null,\n'
        '  "tce_product_usd_per_day": number|null,\n'
        '  "tce_dry_bulk_usd_per_day": number|null,\n'
        '  "employee_cost_cr": number|null\n'
        "}"
    ),
    # Telecom services + equipment. Operators state these in the results release / the
    # results filing's operating-KPI table (Airtel, Vodafone Idea, Bharti Hexacom, Indus
    # Towers); equipment makers state order books (Tejas, HFCL). Traps: India mobile vs
    # group/Africa figures (Airtel reports both), ARPU in INR vs US$, monthly vs quarterly
    # churn, customers in '000 vs million, tower count vs co-location count.
    "telecom": (
        "This is from an Indian TELECOM company's quarterly results release, results filing or investor "
        "presentation (mobile/broadband operator, tower company or telecom equipment maker). Extract ONLY "
        "what is explicitly stated for the CURRENT quarter and the INDIA business (if the company reports "
        "India and overseas separately use India; otherwise the whole company): (1) arpu_inr - mobile ARPU "
        "in RUPEES per month (never US$); (2) subscribers_mn - mobile customer/subscriber base in MILLION "
        "(convert '000 -> million); (3) subscribers_yoy_prior_mn - the same base a year earlier, if shown; "
        "(4) net_adds_mn - net additions in the quarter, million; (5) churn_pct - MONTHLY churn %; "
        "(6) data_usage_gb_per_sub - data usage per customer per MONTH in GB; (7) subscribers_4g5g_mn - "
        "4G/5G data customers in million and subscribers_4g5g_pct - their share of the customer base ONLY as the "
        "company states it (its own denominator; do not compute); (8) broadband_homes_mn - home-broadband/fixed customers in million; "
        "(9) towers - total tower count as a number; (10) colocations - total co-location count; (11) "
        "tenancy_ratio - tenants per tower if stated; (12) order_inflow_cr and (13) order_backlog_cr - "
        "equipment makers' orders won in the quarter / closing order book in INR CRORE; (14) revenue_cr, "
        "(15) ebitda_cr and (16) capex_cr - consolidated quarter revenue, EBITDA and capital expenditure in "
        "INR crore, same entity. Return null for anything not explicitly stated, for overseas/Africa-only "
        "figures, annual/YTD numbers, guidance and chart-only values. ALSO extract the overseas segment when "
        "the company reports one (Airtel Africa) in the africa_* fields below (ARPU in US$), and group-wide "
        "customers in group_customers_mn; (17) data_revenue_cr - data services revenue in INR crore (for "
        "connectivity companies that split voice vs data); (18) mobile_revenue_cr - India mobile segment "
        "revenue in INR crore and data_traffic_bn_gb - total data carried in the quarter in BILLION GB "
        "(convert 'Mn GBs' /1000); (19) capex_cr as above; (20) spectrum_liability_cr and agr_liability_cr - "
        "deferred spectrum and AGR payment obligations in INR crore, as stated. Never invent, infer or "
        "compute a number. Respond with JSON:\n"
        "{\n"
        '  "arpu_inr": number|null,\n'
        '  "subscribers_mn": number|null,\n'
        '  "subscribers_yoy_prior_mn": number|null,\n'
        '  "net_adds_mn": number|null,\n'
        '  "churn_pct": number|null,\n'
        '  "data_usage_gb_per_sub": number|null,\n'
        '  "subscribers_4g5g_mn": number|null,\n'
        '  "subscribers_4g5g_pct": number|null,\n'
        '  "broadband_homes_mn": number|null,\n'
        '  "towers": number|null,\n'
        '  "colocations": number|null,\n'
        '  "tenancy_ratio": number|null,\n'
        '  "order_inflow_cr": number|null,\n'
        '  "order_backlog_cr": number|null,\n'
        '  "revenue_cr": number|null,\n'
        '  "ebitda_cr": number|null,\n'
        '  "capex_cr": number|null,\n'
        '  "africa_arpu_usd": number|null,\n'
        '  "africa_subscribers_mn": number|null,\n'
        '  "africa_subscribers_yoy_prior_mn": number|null,\n'
        '  "africa_net_adds_mn": number|null,\n'
        '  "africa_churn_pct": number|null,\n'
        '  "africa_data_usage_gb_per_sub": number|null,\n'
        '  "africa_data_customers_mn": number|null,\n'
        '  "africa_towers": number|null,\n'
        '  "africa_mobile_money_active_mn": number|null,\n'
        '  "group_customers_mn": number|null,\n'
        '  "data_revenue_cr": number|null,\n'
        '  "mobile_revenue_cr": number|null,\n'
        '  "data_traffic_bn_gb": number|null,\n'
        '  "spectrum_liability_cr": number|null,\n'
        '  "agr_liability_cr": number|null\n'
        "}"
    ),
    # Power generation / renewables / transmission / distribution. Traps: installed vs
    # operational vs contracted-pipeline MW (only operational is 'installed'), PLF (thermal,
    # plant load factor) vs CUF (solar/wind capacity utilisation) vs availability (PAF),
    # gross vs net generation, group-wide vs one plant/subsidiary, MU vs BU vs GWh,
    # AT&C vs technical distribution loss, monthly vs quarterly transmission availability.
    "power": (
        "This is from an Indian POWER company's quarterly results release, operating update or investor "
        "presentation (generator, renewable developer, transmission or distribution utility, power trader). "
        "Extract ONLY what is explicitly stated for the CURRENT quarter and the WHOLE company/group: "
        "(1) installed_capacity_mw - total OPERATIONAL/commissioned capacity in MW (convert GW x1000; exclude "
        "under-construction, awarded or pipeline capacity); (2) installed_capacity_yoy_prior_mw - the same a "
        "year earlier if shown; (3) thermal_capacity_mw and (4) renewable_capacity_mw - operational, in MW; "
        "(5) capacity_under_construction_mw - under construction / contracted pipeline in MW; (6) "
        "generation_mu - electricity generated or sold in the quarter in MILLION UNITS (MU; 1 BU = 1000 MU, "
        "1 GWh = 1 MU); (7) plf_pct - THERMAL plant load factor % (null for solar/wind); (8) availability_pct - "
        "plant availability factor / declared capacity availability % (generators); (9) cuf_pct - solar/wind "
        "capacity utilisation factor %; (10) ppa_contracted_pct - share of capacity or revenue under "
        "long-term PPAs / regulated tariff, only if stated; (11) avg_tariff_inr_per_kwh - average realisation "
        "or tariff in Rs per kWh; (12) transmission_availability_pct - transmission system availability %; "
        "(13) network_ckm - transmission line length in circuit-km and (14) transformation_capacity_mva; "
        "(15) distribution_loss_pct - distribution/T&D loss %; (16) atc_loss_pct - AT&C loss %; (17) "
        "collection_efficiency_pct; (18) trading_volume_bu - power traded in BILLION units; (19) revenue_cr "
        "and (20) ebitda_cr and (21) capex_cr - quarter figures in INR crore, same entity. Return null for "
        "anything not explicitly stated, for annual/YTD or single-plant figures, for pipeline counted as "
        "capacity, and for chart-only values. Never invent, infer or compute a number. Respond with JSON:\n"
        "{\n"
        '  "installed_capacity_mw": number|null,\n'
        '  "installed_capacity_yoy_prior_mw": number|null,\n'
        '  "thermal_capacity_mw": number|null,\n'
        '  "renewable_capacity_mw": number|null,\n'
        '  "capacity_under_construction_mw": number|null,\n'
        '  "generation_mu": number|null,\n'
        '  "plf_pct": number|null,\n'
        '  "availability_pct": number|null,\n'
        '  "cuf_pct": number|null,\n'
        '  "ppa_contracted_pct": number|null,\n'
        '  "avg_tariff_inr_per_kwh": number|null,\n'
        '  "transmission_availability_pct": number|null,\n'
        '  "network_ckm": number|null,\n'
        '  "transformation_capacity_mva": number|null,\n'
        '  "distribution_loss_pct": number|null,\n'
        '  "atc_loss_pct": number|null,\n'
        '  "collection_efficiency_pct": number|null,\n'
        '  "trading_volume_bu": number|null,\n'
        '  "revenue_cr": number|null,\n'
        '  "ebitda_cr": number|null,\n'
        '  "capex_cr": number|null\n'
        "}"
    ),
    # Water / waste / other regulated utilities (Utilities -> Utilities spec). Traps: contracted
    # or pipeline capacity vs operational, tonnes per quarter vs per day vs per year, MLD vs MGD, order book that
    # mixes EPC with decade-long O&M, group vs one subsidiary.
    "utilities": (
        "This is from an Indian WATER / WASTE-MANAGEMENT / regulated-utility company's quarterly results "
        "release, investor presentation or call. Extract ONLY what is explicitly stated for the CURRENT "
        "quarter and the WHOLE company: (1) order_inflow_cr - orders won in the quarter, INR crore; (2) "
        "order_inflow_yoy_prior_cr - same a year earlier if shown; (3) order_backlog_cr - closing order book "
        "in INR crore (convert million x0.1, billion x100); (4) order_backlog_yoy_prior_cr - year-ago "
        "closing order book if shown; (5) order_inflow_growth_pct / order_backlog_growth_pct - only if the "
        "document states the YoY %; (6) revenue_cr - revenue from operations, same entity, INR crore; "
        "(7) waste_processed_kt - waste processed in the QUARTER in THOUSAND tonnes (0.85 million tonnes = "
        "850); (8) waste_collected_kt - waste collected/transported in the quarter, thousand tonnes; (9) treatment_capacity_mld - water/wastewater treatment capacity "
        "operated or built, in MLD (million litres per day); (10) customers_mn - customers/connections in "
        "million; (11) collection_efficiency_pct; (12) network_km - pipeline/network length in km. Return "
        "null for anything not explicitly stated, for pipeline/awarded-but-uncontracted capacity, "
        "annual/YTD figures, single-project figures, and chart-only values. Never invent, infer or compute a "
        "number. Respond with JSON:\n"
        "{\n"
        '  "order_inflow_cr": number|null,\n'
        '  "order_inflow_yoy_prior_cr": number|null,\n'
        '  "order_backlog_cr": number|null,\n'
        '  "order_backlog_yoy_prior_cr": number|null,\n'
        '  "order_inflow_growth_pct": number|null,\n'
        '  "order_backlog_growth_pct": number|null,\n'
        '  "revenue_cr": number|null,\n'
        '  "waste_processed_kt": number|null,\n'
        '  "waste_collected_kt": number|null,\n'
        '  "treatment_capacity_mld": number|null,\n'
        '  "customers_mn": number|null,\n'
        '  "collection_efficiency_pct": number|null,\n'
        '  "network_km": number|null\n'
        "}"
    ),
}

# Sector name (as resolved by app.sectors.registry.get_framework) -> locator
# area key (app/ingestion/annual_report_locator.py's _AREA_TERMS) -> prompt
# key (_AREA_PROMPTS above) -> metric_key prefix.
_SECTOR_CONFIG = {
    # NIM/Cost-to-Income (2026-09-27) — unlike every other entry here,
    # `_store_extracted()`'s Banks/NBFC branch stores these under the BARE
    # `nim`/`cost_to_income_ratio` metric keys (no `qtr_{prefix}_` prefix),
    # matching `banking_ingestion.py`'s existing convention — the same keys
    # `banking_data_bridge.py`/`scoring.py`'s efficiency scorers already
    # read, so this becomes a second, far-broader-coverage source for
    # metrics that previously only came from a ~9-company BSE-OCR pilot.
    "Banks": {"locator_area": "banking_quarterly_metrics", "prompt": "banking", "prefix": "banking"},
    "NBFCs": {"locator_area": "banking_quarterly_metrics", "prompt": "banking", "prefix": "banking"},
    "Housing Finance": {"locator_area": "banking_quarterly_metrics", "prompt": "banking", "prefix": "banking"},
    "Microfinance": {"locator_area": "banking_quarterly_metrics", "prompt": "banking", "prefix": "banking"},
    "Gold Loans": {"locator_area": "banking_quarterly_metrics", "prompt": "banking", "prefix": "banking"},
    "Automobile": {"locator_area": "automobile_quarterly_metrics", "prompt": "automobile", "prefix": "automobile"},
    "Cement": {"locator_area": "cement_quarterly_metrics", "prompt": "cement", "prefix": "cement"},
    "Chemicals": {"locator_area": "chemicals_quarterly_metrics", "prompt": "chemicals", "prefix": "chemicals"},
    "Specialty Chemicals": {"locator_area": "chemicals_quarterly_metrics", "prompt": "chemicals", "prefix": "chemicals"},
    "Metals": {"locator_area": "metals_quarterly_metrics", "prompt": "metals", "prefix": "metals"},
    "Mining": {"locator_area": "metals_quarterly_metrics", "prompt": "metals", "prefix": "metals"},
    "Forest Materials": {"locator_area": "paper_quarterly_metrics", "prompt": "paper", "prefix": "paper"},
    "Consumer Durables": {"locator_area": "consumer_durables_quarterly_metrics", "prompt": "consumer_durables", "prefix": "consumer_durables"},
    "Hotels & Restaurants": {"locator_area": "hotels_quarterly_metrics", "prompt": "hotels", "prefix": "hotels"},
    "Retail": {"locator_area": "retail_quarterly_metrics", "prompt": "retail", "prefix": "retail"},
    "Real Estate": {"locator_area": "realty_quarterly_metrics", "prompt": "realty", "prefix": "realty"},
    "Oil & Gas": {"locator_area": "oil_gas_quarterly_metrics", "prompt": "oil_gas", "prefix": "oilgas"},
    "Fast Moving Consumer Goods": {"locator_area": "fmcg_quarterly_metrics", "prompt": "fmcg", "prefix": "fmcg"},
    "Healthcare": {"locator_area": "healthcare_quarterly_metrics", "prompt": "healthcare", "prefix": "healthcare"},
    "Capital Goods": {"locator_area": "capgoods_quarterly_metrics", "prompt": "capgoods", "prefix": "capgoods"},
    "Industrials": {"locator_area": "capgoods_quarterly_metrics", "prompt": "capgoods", "prefix": "capgoods"},
    "Defence": {"locator_area": "capgoods_quarterly_metrics", "prompt": "capgoods", "prefix": "capgoods"},
    "Power": {"locator_area": "power_quarterly_metrics", "prompt": "power", "prefix": "pow"},
    "Utilities": {"locator_area": "utilities_quarterly_metrics", "prompt": "utilities", "prefix": "util"},
    "Renewable Energy": {"locator_area": "power_quarterly_metrics", "prompt": "power", "prefix": "pow"},
    "Telecom": {"locator_area": "telecom_quarterly_metrics", "prompt": "telecom", "prefix": "tel"},
    "Services": {"locator_area": "services_quarterly_metrics", "prompt": "services", "prefix": "svc"},
    "Logistics": {"locator_area": "services_quarterly_metrics", "prompt": "services", "prefix": "svc"},
    "Aviation": {"locator_area": "services_quarterly_metrics", "prompt": "services", "prefix": "svc"},
    "Infrastructure": {"locator_area": "services_quarterly_metrics", "prompt": "services", "prefix": "svc"},
    "Information Technology": {"locator_area": "it_quarterly_metrics", "prompt": "it_services", "prefix": "it"},
    "Construction": {"locator_area": "capgoods_quarterly_metrics", "prompt": "capgoods", "prefix": "capgoods"},
}


def extract_area(prompt_key: str, text: str, llm_client=None, prefix: str = "") -> dict:
    client = llm_client or default_llm_client
    return client.chat_json(prefix + _AREA_PROMPTS[prompt_key], text[:_MAX_CHARS_PER_AREA], max_tokens=_MAX_TOKENS)


def _prior_year_period(period: str) -> str | None:
    """Same-quarter-prior-year ISO date, used only by the Retail branch to
    compute store_count_growth_yoy against OUR OWN previously-ingested
    ledger value — unlike every other sector here, Trent's deck (the only
    real candidate found) doesn't disclose a prior-year store count on the
    same page, only the current total, so there is no same-deck pair to
    derive growth from. Returns None on an unparseable period rather than
    raising."""
    try:
        d = datetime.strptime(period, "%Y-%m-%d")
        return d.replace(year=d.year - 1).date().isoformat()
    except ValueError:
        return None


def _to_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _latest_fiscal_value(db: Session, company_id: str, metric_key: str, statement_type: str, period: str | None = None):
    """Same TTM-exclusion discipline as annual_report_ingestion.py's
    `_latest_fiscal_pnl_value` — `qtr_sales`/`qtr_operating_profit` never
    carry a "TTM" pseudo-period today, but excluding it costs nothing and
    keeps this helper safe if that ever changes. When `period` is given,
    fetches that EXACT period (used to match a specific prior quarter);
    otherwise the latest one on record."""
    if period is not None:
        winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
        return winner
    all_rows = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    fiscal_periods = sorted({r.period for r in all_rows if r.period != "TTM"}, reverse=True)
    if not fiscal_periods:
        return None
    winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, fiscal_periods[0], statement_type=statement_type)
    return winner


def _ingest_from_deck(db: Session, company_id: str, symbol: str, sector_name: str) -> list:
    """Fetches this company's latest quarterly Investor Presentation (if
    one exists and resolves to real, extractable text — see
    nse_investor_presentation_client.py), extracts the sector-appropriate
    physical KPIs, and computes per-tonne/unit ratios against the same
    quarter's Screener-sourced `qtr_sales`/`qtr_operating_profit`. Never
    raises — logs and returns whatever it managed to insert (possibly
    empty), matching every other ingestion path's contract. Returns []
    immediately for a sector with no configured area (most sectors don't
    have one yet — this is not itself a failure)."""
    inserted = []
    config = _SECTOR_CONFIG.get(sector_name)
    if config is None:
        return inserted

    fetched = ipc.fetch_latest_investor_presentation(symbol)
    if fetched is None:
        logger.info("quarterly_operating_metrics_ingestion: no usable investor presentation found",
                    symbol=symbol, sector=sector_name)
        return inserted
    pdf_bytes, source_url, filing = fetched

    document = ipc.store_investor_presentation(db, company_id, symbol, filing, pdf_bytes, source_url)
    if document is None:
        return inserted

    try:
        sections, _statement_types = locate_sections(pdf_bytes)
    except Exception as e:
        logger.warning("quarterly_operating_metrics_ingestion: locator failed", symbol=symbol, error=str(e))
        return inserted

    page_indices = sections.get(config["locator_area"], [])
    if not page_indices:
        return inserted

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        area_text = "\n\n".join(
            (pdf.pages[i].extract_text() or "") for i in page_indices if i < len(pdf.pages)
        )
        full_text_for_metadata = "\n\n".join((p.extract_text() or "") for p in pdf.pages[:3])
    if not area_text:
        return inserted

    period = _parse_quarter_end_date(full_text_for_metadata) or _parse_quarter_end_date(area_text)
    if period is None:
        logger.warning("quarterly_operating_metrics_ingestion: could not parse quarter-end date, skipping",
                        symbol=symbol)
        return inserted
    statement_type = _resolve_statement_type(full_text_for_metadata)

    try:
        extracted = extract_area(config["prompt"], area_text)
    except Exception as e:
        logger.warning("quarterly_operating_metrics_ingestion: extraction failed", symbol=symbol, error=str(e))
        return inserted

    # Same fallback-LLM guard as the annual engine — skip storage entirely
    # rather than risk a wrong value tagged as trustworthy.
    if default_llm_client.last_used_fallback:
        logger.warning("quarterly_operating_metrics_ingestion: skipping, fallback LLM served this extraction",
                        symbol=symbol, sector=sector_name)
        return inserted

    source_document = f"NSE Investor Presentation ({filing.get('an_dt', 'unknown date')})"
    return _store_extracted(db, company_id, sector_name, config, extracted, period, statement_type,
                            source_url, source_document, inserted)


# Prepended to the sector prompt when the document is an earnings-call
# transcript rather than a slide deck. Transcripts are prose (which is why
# they succeed where charts fail) but are full of analyst questions, guidance
# and multi-year figures that look like the target.
_TRANSCRIPT_PREFIX = (
    "NOTE: this text is an EARNINGS CALL TRANSCRIPT, not a slide or table. Use ONLY figures that "
    "MANAGEMENT states about the CURRENT reported quarter for the whole company. Ignore numbers that "
    "appear only inside an analyst's question, forward guidance/targets, multi-year CAGRs, full-year "
    "figures and single segments/brands/cities. Where the instructions below mention table columns or "
    "prior-period values, return null for any value the speaker does not state in words. ")


_NSE_ANNOUNCEMENTS_URL = "https://www.nseindia.com/api/corporate-announcements"


def _find_nse_filings(symbol: str, kind: str, session, lookback_days: int = 120) -> list[dict]:
    """Newest-first NSE filings of one kind: "press" (desc "Press Release" —
    the results press release, which for hospitals carries a clean KPI table
    with year-ago and prior-quarter columns) or "transcript". Never raises."""
    if kind == "transcript":
        try:
            rows = find_transcript_filings(symbol, session=session, lookback_days=lookback_days)
        except Exception:
            return []
    else:
        to = datetime.now()
        params = {"index": "equities", "symbol": symbol,
                  "from_date": (to - timedelta(days=lookback_days)).strftime("%d-%m-%Y"),
                  "to_date": to.strftime("%d-%m-%Y")}
        try:
            r = session.get(_NSE_ANNOUNCEMENTS_URL, params=params, timeout=20)
            r.raise_for_status()
            wanted = "Outcome of Board Meeting" if kind == "outcome" else "Press Release"
            rows = [x for x in (r.json() or []) if x.get("desc") == wanted and x.get("attchmntFile")]
        except Exception as e:
            logger.warning("quarterly_operating_metrics_ingestion: press-release search failed", symbol=symbol, error=str(e))
            return []
    def _key(f):
        try:
            return datetime.strptime(f["an_dt"].split(" ")[0], "%d-%b-%Y")
        except (KeyError, ValueError):
            return datetime.min
    return sorted(rows, key=_key, reverse=True)


_KIND_META = {
    "press": {"source": "NSE_PRESS_RELEASE", "label": "NSE results press release", "prefix": "", "max_docs": 3},
    "outcome": {"source": "NSE_RESULTS_FILING", "label": "NSE results filing", "prefix": "", "max_docs": 2},
    "transcript": {"source": "NSE_CONCALL", "label": "NSE earnings call transcript", "prefix": _TRANSCRIPT_PREFIX, "max_docs": 1},
}


def _ingest_from_filing(db: Session, company_id: str, symbol: str, sector_name: str, kind: str) -> list:
    """Later documents in the source cascade (after the Investor
    Presentation): the results press release ("press") and the earnings-call
    transcript ("transcript"). Tries up to `max_docs` newest filings and uses
    the first that locates the sector's KPI area AND yields a stored value —
    press releases include non-results ones (acquisitions, awards), which the
    locator/period checks skip. Rows keep their own source; transcript rows
    are capped at MEDIUM confidence. Never raises."""
    inserted: list = []
    config = _SECTOR_CONFIG.get(sector_name)
    meta = _KIND_META[kind]
    if config is None:
        return inserted
    try:
        session = nse_client._session()
        filings = _find_nse_filings(symbol, kind, session)[: meta["max_docs"]]
    except Exception as e:
        logger.warning("quarterly_operating_metrics_ingestion: filing search failed", symbol=symbol, kind=kind, error=str(e))
        return inserted

    for filing in filings:
        try:
            r = session.get(filing["attchmntFile"], timeout=40, headers={"Referer": nse_client.BOOTSTRAP_URL})
            r.raise_for_status()
            pdf_bytes = r.content
            xt = 1.5 if kind == "outcome" else 3  # results filings can be letter-spaced (Airtel)
            sections, _ = locate_sections(pdf_bytes, x_tolerance=xt)
            page_indices = sections.get(config["locator_area"], [])
            if not page_indices:
                continue
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                area_text = "\n\n".join((pdf.pages[i].extract_text(x_tolerance=xt) or "") for i in page_indices if i < len(pdf.pages))
                head = "\n\n".join((p.extract_text() or "") for p in pdf.pages[:2])
        except Exception as e:
            logger.warning("quarterly_operating_metrics_ingestion: filing fetch/locate failed", symbol=symbol, kind=kind, error=str(e))
            continue
        if not area_text:
            continue
        period = _parse_quarter_end_date(head) or _parse_quarter_end_date(area_text)
        if period is None:
            logger.warning("quarterly_operating_metrics_ingestion: quarter unparseable, skipping filing", symbol=symbol, kind=kind)
            continue
        try:
            extracted = extract_area(config["prompt"], area_text, prefix=meta["prefix"])
        except Exception as e:
            logger.warning("quarterly_operating_metrics_ingestion: extraction failed", symbol=symbol, kind=kind, error=str(e))
            continue
        if default_llm_client.last_used_fallback:
            logger.warning("quarterly_operating_metrics_ingestion: skipping, fallback LLM served this extraction",
                            symbol=symbol, sector=sector_name, kind=kind)
            return inserted
        token = _source_ctx.set(meta["source"])
        try:
            inserted = _store_extracted(db, company_id, sector_name, config, extracted, period,
                                        _resolve_statement_type(head), filing["attchmntFile"],
                                        f"{meta['label']} ({filing.get('an_dt', 'unknown date')})", [])
        finally:
            _source_ctx.reset(token)
        if inserted:
            return inserted
    return inserted


def ingest_quarterly_operating_metrics(db: Session, company_id: str, symbol: str, sector_name: str) -> list:
    """Source cascade for a company's sector KPIs: (1) the latest quarterly
    Investor Presentation, then — only if that yielded nothing — (2) the NSE
    results press release, then (3) the earnings-call transcript. (Outcome-of-
    board-meeting filings were checked on 8 hospitals and carry financial
    statements only — no operating KPIs — so they are deliberately not a layer.)
    Each stored row keeps its own source and confidence. Returns [] immediately for a sector with no configured area.
    Never raises."""
    if sector_name not in _SECTOR_CONFIG:
        return []
    toll_rows: list = []
    if sector_name == "Infrastructure":
        from app.ingestion.nse_toll_disclosure_client import ingest_monthly_toll_revenue
        toll_rows = ingest_monthly_toll_revenue(db, company_id, symbol)
    if sector_name == "Telecom":
        from app.ingestion.trai_client import ingest_trai_market_share
        toll_rows = ingest_trai_market_share(db, symbol, company_id)  # industry-level regulator source, independent of filings
    if sector_name == "Power":
        from app.ingestion.cea_client import ingest_cea_sector_plf
        toll_rows = ingest_cea_sector_plf(db, symbol, company_id)  # industry benchmark, independent of the company's filings
    if sector_name == "Oil & Gas" and symbol in ("PETRONET", "GAIL", "GSPL"):
        from app.ingestion.ppac_client import ingest_ppac_gas_data
        toll_rows = ingest_ppac_gas_data(db, symbol, company_id)  # regulator data, independent of the company's filings
    stages = [lambda: _ingest_from_deck(db, company_id, symbol, sector_name),
              lambda: _ingest_from_filing(db, company_id, symbol, sector_name, "press")]
    if sector_name == "Telecom":  # the results filing carries the operating-KPI table (Airtel, Hexacom, Vi)
        stages.append(lambda: _ingest_from_filing(db, company_id, symbol, sector_name, "outcome"))
    stages.append(lambda: _ingest_from_filing(db, company_id, symbol, sector_name, "transcript"))
    for stage in stages:
        inserted = stage()
        if inserted:
            return toll_rows + inserted
    return toll_rows


def _store_extracted(db: Session, company_id: str, sector_name: str, config: dict, extracted: dict,
                     period: str, statement_type: str, source_url: str, source_document: str,
                     inserted: list) -> list:
    """Stores one extraction result under the sector-specific key layout and
    derives ratios. Shared by the deck and transcript paths — the document
    type only changes provenance (`_source_ctx`), never the key layout."""
    now = datetime.now(timezone.utc)
    prefix = config["prefix"]

    def _store(field: str, value, unit: str, key_suffix: str) -> None:
        v = _to_float(value)
        if v is None:
            return
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key=f"qtr_{prefix}_{key_suffix}", period=period,
            value=v, unit=unit, statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
            confidence=_conf("HIGH"), source_url=source_url, source_document=source_document, source_date=now,
            raw_reported_value=str(value),
        )
        if row is not None:
            inserted.append(row)

    # Banks/NBFCs — bare `nim`/`cost_to_income_ratio` keys, NOT `_store()`'s
    # `qtr_{prefix}_` pattern (see `_SECTOR_CONFIG`'s comment on why: these
    # must match `banking_ingestion.py`'s existing metric-key convention so
    # `banking_data_bridge.py`'s already-working `_METRIC_KEYS` lookup and
    # `scoring.py`'s bank/NBFC efficiency scorers pick them up with no
    # further wiring).
    if sector_name in ("Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans"):
        for field, metric_key, unit in (("nim_pct", "nim", "%"), ("cost_to_income_pct", "cost_to_income_ratio", "%")):
            v = _to_float(extracted.get(field))
            if v is None:
                continue
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=metric_key, period=period,
                value=v, unit=unit, statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
                confidence=_conf("HIGH"), source_url=source_url, source_document=source_document, source_date=now,
                raw_reported_value=str(extracted.get(field)),
            )
            if row is not None:
                inserted.append(row)
        return inserted

    if sector_name == "Automobile":
        _store("units_sold_current_quarter", extracted.get("units_sold_current_quarter"), "units", "units_sold")
        _store("units_sold_yoy_prior_quarter", extracted.get("units_sold_yoy_prior_quarter"), "units", "units_sold_yoy_prior")
        _store("units_sold_qoq_prior_quarter", extracted.get("units_sold_qoq_prior_quarter"), "units", "units_sold_qoq_prior")
        _store("market_share_pct", extracted.get("market_share_pct"), "%", "market_share")
    elif sector_name == "Cement":
        _store("sales_million_tonnes_current_quarter", extracted.get("sales_million_tonnes_current_quarter"), "MT", "sales_mnt")
        _store("sales_million_tonnes_yoy_prior_quarter", extracted.get("sales_million_tonnes_yoy_prior_quarter"), "MT", "sales_mnt_yoy_prior")
        _store("sales_million_tonnes_qoq_prior_quarter", extracted.get("sales_million_tonnes_qoq_prior_quarter"), "MT", "sales_mnt_qoq_prior")
        # No cost_per_tonne_reported field for Cement — the clean row-based
        # table (see the "cement" prompt above) doesn't have one; cost/tonne
        # is always derived (realisation - ebitda) in _compute_ratios below.
        _store("ebitda_per_tonne_reported", extracted.get("ebitda_per_tonne_reported"), "INR", "ebitda_per_tonne_reported")
    elif sector_name in ("Metals", "Mining"):
        _store("production_million_tonnes_current_quarter", extracted.get("production_million_tonnes_current_quarter"), "MT", "production_mnt")
        _store("production_million_tonnes_yoy_prior_quarter", extracted.get("production_million_tonnes_yoy_prior_quarter"), "MT", "production_mnt_yoy_prior")
        _store("sales_million_tonnes_current_quarter", extracted.get("sales_million_tonnes_current_quarter"), "MT", "sales_mnt")
        _store("sales_million_tonnes_yoy_prior_quarter", extracted.get("sales_million_tonnes_yoy_prior_quarter"), "MT", "sales_mnt_yoy_prior")
    elif sector_name == "Forest Materials":
        _store("production_tonnes_current_quarter", extracted.get("production_tonnes_current_quarter"), "tonnes", "production_tonnes")
        _store("production_tonnes_yoy_prior_quarter", extracted.get("production_tonnes_yoy_prior_quarter"), "tonnes", "production_tonnes_yoy_prior")
        _store("sales_tonnes_current_quarter", extracted.get("sales_tonnes_current_quarter"), "tonnes", "sales_tonnes")
        _store("sales_tonnes_yoy_prior_quarter", extracted.get("sales_tonnes_yoy_prior_quarter"), "tonnes", "sales_tonnes_yoy_prior")
    elif sector_name in ("Chemicals", "Specialty Chemicals"):
        # Unlike every other sector here, this is a growth % DIRECTLY
        # reported (segment-level, see the "chemicals" prompt's own
        # comment) — not an absolute current+prior pair needing later
        # ratio computation, so it's stored straight under the same final
        # `qtr_volume_growth_yoy` key the other sectors' _compute_ratios
        # block derives, for cross-sector dashboard consistency. Also
        # stores the segment name as a raw reference field (not itself a
        # numeric metric) via raw_reported_value, and skips
        # _compute_ratios entirely below — there's no tonne-denominated
        # absolute volume here to build per-tonne ratios from.
        growth = _to_float(extracted.get("volume_growth_yoy_pct"))
        if growth is not None:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_volume_growth_yoy", period=period,
                value=growth, unit="%", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
                confidence=_conf("HIGH"), source_url=source_url, source_document=source_document, source_date=now,
                raw_reported_value=f"{extracted.get('primary_segment_name')}: {growth}",
                calculation_formula=f"segment '{extracted.get('primary_segment_name')}' YoY growth, "
                                     "directly stated — not a company-wide aggregate",
            )
            if row is not None:
                inserted.append(row)
        _store("export_revenue_pct", extracted.get("export_revenue_pct"), "%", "export_revenue_pct")
        return inserted
    elif sector_name == "Consumer Durables":
        # Same shape as the Chemicals branch above — a growth % DIRECTLY
        # reported (segment-level), not an absolute current+prior pair, so
        # no _compute_ratios step (no tonne-denominated volume here).
        # Stored under the shared `qtr_volume_growth_yoy` key for
        # cross-sector dashboard consistency; market share gets its own
        # `qtr_consumer_durables_market_share` key, mirroring Automobile's
        # `qtr_automobile_market_share`.
        growth = _to_float(extracted.get("volume_growth_yoy_pct"))
        if growth is not None:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_volume_growth_yoy", period=period,
                value=growth, unit="%", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
                confidence=_conf("HIGH"), source_url=source_url, source_document=source_document, source_date=now,
                raw_reported_value=f"{extracted.get('primary_segment_name')}: {growth}",
                calculation_formula=f"segment '{extracted.get('primary_segment_name')}' YoY volume growth, "
                                     "directly stated — not a company-wide aggregate",
            )
            if row is not None:
                inserted.append(row)
        _store("market_share_pct", extracted.get("market_share_pct"), "%", "market_share")
        return inserted
    elif sector_name == "Hotels & Restaurants":
        # HotelsSector's NA fields (occupancy_rate, arr, revpar) are all
        # ABSOLUTE current-quarter values, not growth rates — unlike
        # Automobile/Cement/Metals there's no derived growth metric to
        # compute here, so only the current-quarter figures are surfaced
        # in quarterly_sector_kpis.py; the yoy_prior figures are still
        # stored (useful raw history) but not displayed as their own card,
        # same precedent as qtr_automobile_units_sold_yoy_prior.
        _store("adr_current_quarter", extracted.get("adr_current_quarter"), "INR", "arr")
        _store("adr_yoy_prior_quarter", extracted.get("adr_yoy_prior_quarter"), "INR", "arr_yoy_prior")
        _store("occupancy_pct_current_quarter", extracted.get("occupancy_pct_current_quarter"), "%", "occupancy")
        _store("occupancy_pct_yoy_prior_quarter", extracted.get("occupancy_pct_yoy_prior_quarter"), "%", "occupancy_yoy_prior")
        _store("revpar_current_quarter", extracted.get("revpar_current_quarter"), "INR", "revpar")
        _store("revpar_yoy_prior_quarter", extracted.get("revpar_yoy_prior_quarter"), "INR", "revpar_yoy_prior")
        return inserted
    elif sector_name == "Retail":
        # RetailSector's NA fields are store_count_growth_yoy, sssg,
        # revenue_per_sqft. Trent's deck (the only real candidate found)
        # gives a clean CURRENT store count/retail area/revenue snapshot
        # but no prior-year comparison on the same page — unlike every
        # other sector, growth is derived by looking up OUR OWN
        # previously-ingested qtr_retail_store_count from the same quarter
        # a year ago (see _prior_year_period), so it naturally stays null
        # until a second year of quarterly ingestion accumulates. SSSG is
        # frequently disclosed only as vague qualitative text (confirmed
        # live: Trent's own Q1 FY27 deck says "low single digits", no
        # number) — the prompt is instructed to return null rather than
        # guess a figure, so qtr_retail_sssg is a genuine, documented gap
        # for now, not a bug.
        _store("store_count_current_quarter", extracted.get("store_count_current_quarter"), "count", "store_count")
        _store("sssg_pct", extracted.get("sssg_pct"), "%", "sssg")

        revenue_cr = _to_float(extracted.get("revenue_cr_current_quarter"))
        area_sqft = _to_float(extracted.get("retail_area_sqft_current_quarter"))
        if revenue_cr is not None and area_sqft:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_retail_revenue_per_sqft", period=period,
                value=round(revenue_cr * 1e7 / area_sqft, 2), unit="INR", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
                confidence="MEDIUM",
                calculation_formula="revenue_cr_current_quarter * 1e7 / retail_area_sqft_current_quarter "
                                     "(a single-quarter figure, not annualized)",
                source_url=source_url, source_document=source_document, source_date=now,
            )
            if row is not None:
                inserted.append(row)

        store_count_row = next((r for r in inserted if r.metric_key == "qtr_retail_store_count"), None)
        if store_count_row is not None:
            prior_period = _prior_year_period(period)
            if prior_period is not None:
                prior_value, _ = metric_store.get_authoritative_value(
                    db, company_id, "qtr_retail_store_count", prior_period, statement_type=statement_type)
                if prior_value is not None and prior_value.value:
                    growth = (float(store_count_row.value) - float(prior_value.value)) / float(prior_value.value) * 100
                    row = metric_store.insert_metric_value(
                        db, company_id=company_id, metric_key="qtr_retail_store_count_growth_yoy", period=period,
                        value=round(growth, 2), unit="%", statement_type=statement_type,
                        source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
                        confidence="MEDIUM",
                        calculation_formula=f"(qtr_retail_store_count[{period}] - qtr_retail_store_count[{prior_period}]) "
                                             f"/ qtr_retail_store_count[{prior_period}] * 100 — against our own prior-year "
                                             "ledger value, not a same-deck comparison",
                        source_url=source_url, source_document=source_document, source_date=now,
                    )
                    if row is not None:
                        inserted.append(row)
        return inserted
    elif sector_name == "Real Estate":
        # RealEstateSector's `pre_sales_value` NA field is filled directly
        # from booking_value (REPORTED). `collections_growth_yoy` is
        # derived from the SAME deck's current+yoy_prior collections pair
        # (like Cement/Automobile), not our own ledger lookback (unlike
        # Retail's store_count_growth_yoy) — real estate decks reliably
        # give both periods on the same page. `launch_pipeline_msf` is
        # NOT addressed here — dropped after a real, caught fabrication
        # (see the "realty" prompt's own comment above).
        _store("booking_value_cr_current_quarter", extracted.get("booking_value_cr_current_quarter"), "INR Cr", "pre_sales_value")
        _store("booking_value_cr_yoy_prior_quarter", extracted.get("booking_value_cr_yoy_prior_quarter"), "INR Cr", "pre_sales_value_yoy_prior")
        _store("collections_cr_current_quarter", extracted.get("collections_cr_current_quarter"), "INR Cr", "collections")
        _store("collections_cr_yoy_prior_quarter", extracted.get("collections_cr_yoy_prior_quarter"), "INR Cr", "collections_yoy_prior")

        by_key = {row.metric_key: row for row in inserted}
        current_row = by_key.get("qtr_realty_collections")
        prior_row = by_key.get("qtr_realty_collections_yoy_prior")
        if current_row is not None and prior_row is not None and prior_row.value:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_realty_collections_growth_yoy", period=period,
                value=round((float(current_row.value) - float(prior_row.value)) / float(prior_row.value) * 100, 2),
                unit="%", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
                confidence="MEDIUM",
                calculation_formula="(qtr_realty_collections - qtr_realty_collections_yoy_prior) / "
                                     "qtr_realty_collections_yoy_prior * 100",
                source_url=source_url, source_document=source_document, source_date=now,
            )
            if row is not None:
                inserted.append(row)
        return inserted
    elif sector_name == "Oil & Gas":
        # OilGasSector's `grm` NA field is an ABSOLUTE value (USD/bbl),
        # not a growth rate — stored directly, no _compute_ratios step
        # (no tonne-denominated volume here; GRM is already a per-barrel
        # spread figure the company states directly). yoy_prior/qoq_prior
        # are stored as raw history (not surfaced as their own card),
        # same precedent as Hotels' *_yoy_prior fields.
        _store("grm_usd_bbl_current_quarter", extracted.get("grm_usd_bbl_current_quarter"), "USD/bbl", "grm")
        _store("grm_usd_bbl_yoy_prior_quarter", extracted.get("grm_usd_bbl_yoy_prior_quarter"), "USD/bbl", "grm_yoy_prior")
        _store("grm_usd_bbl_qoq_prior_quarter", extracted.get("grm_usd_bbl_qoq_prior_quarter"), "USD/bbl", "grm_qoq_prior")
        _store("cgd_volume_mmscmd", extracted.get("cgd_volume_mmscmd"), "MMSCMD", "cgd_volume_mmscmd")
        _store("cgd_volume_mmscm", extracted.get("cgd_volume_mmscm"), "MMSCM", "cgd_volume_mmscm")
        _cgd_g = _to_float(extracted.get("cgd_volume_growth_yoy_pct"))
        if _cgd_g is not None:
            _row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_volume_growth_yoy", period=period, value=_cgd_g, unit="%",
                statement_type=statement_type, source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
                confidence=_conf("HIGH"), source_url=source_url, source_document=source_document, source_date=now,
                raw_reported_value=str(_cgd_g))
            if _row is not None:
                inserted.append(_row)
        for _f, _u, _k in [("gas_transmission_mmscmd", "MMSCMD", "gas_transmission_mmscmd"),
                           ("gas_marketing_mmscmd", "MMSCMD", "gas_marketing_mmscmd"),
                           ("lpg_transmission_tmt", "kt", "lpg_transmission_kt"), ("petchem_production_tmt", "kt", "petchem_production_kt"),
                           ("lhc_production_tmt", "kt", "lhc_production_kt"), ("lng_throughput_tbtu", "TBtu", "lng_throughput_tbtu"),
                           ("regas_utilization_pct", "%", "regas_utilization"), ("regas_capacity_mmtpa", "MMTPA", "regas_capacity_mmtpa"),
                           ("capex_cr", "INR Cr", "capex")]:
            _store(_f, extracted.get(_f), _u, _k)
        _rev, _ebd, _cpx = (_to_float(extracted.get(k)) for k in ("revenue_cr", "ebitda_cr", "capex_cr"))
        if _rev and _ebd is not None and _cpx is not None:
            _row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=f"qtr_{prefix}_ebitda_minus_capex_margin", period=period,
                value=round((_ebd - _cpx) / _rev * 100, 2), unit="%", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="(ebitda_cr - capex_cr) / revenue_cr * 100", source_url=source_url,
                source_document=source_document, source_date=now)
            if _row is not None:
                inserted.append(_row)
        _store("cng_stations", extracted.get("cng_stations"), "units", "cng_stations")
        _store("png_domestic_connections_lakh", extracted.get("png_domestic_connections_lakh"), "lakh", "png_connections_lakh")
        _store("cgd_gross_margin_per_scm_inr", extracted.get("cgd_gross_margin_per_scm_inr"), "INR/SCM", "cgd_margin_per_scm")
        return inserted
    elif sector_name == "Fast Moving Consumer Goods":
        # Directly-stated company-wide growth %s. UVG goes under the shared
        # `qtr_volume_growth_yoy` key (same key Chemicals/Consumer Durables
        # use). Price/mix is DERIVED, never reported: (1+USG)/(1+UVG)-1 —
        # underlying sales growth net of volume, the standard decomposition.
        uvg = _to_float(extracted.get("underlying_volume_growth_pct"))
        usg = _to_float(extracted.get("underlying_sales_growth_pct"))
        if uvg is not None:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_volume_growth_yoy", period=period,
                value=uvg, unit="%", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
                confidence=_conf("HIGH"), source_url=source_url, source_document=source_document, source_date=now,
                raw_reported_value=str(uvg),
                calculation_formula="company-wide underlying volume growth, directly stated",
            )
            if row is not None:
                inserted.append(row)
        _store("underlying_sales_growth_pct", usg, "%", "underlying_sales_growth")
        if uvg is not None and usg is not None and uvg > -100:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_fmcg_price_mix_growth", period=period,
                value=round(((1 + usg / 100) / (1 + uvg / 100) - 1) * 100, 2), unit="%", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
                confidence="MEDIUM", source_url=source_url, source_document=source_document, source_date=now,
                calculation_formula="(1 + underlying_sales_growth) / (1 + underlying_volume_growth) - 1",
            )
            if row is not None:
                inserted.append(row)
        return inserted

    elif sector_name == "Healthcare":
        _store("bed_occupancy_pct", extracted.get("bed_occupancy_pct"), "%", "bed_occupancy")
        _store("arpob_inr_per_day", extracted.get("arpob_inr_per_day"), "INR", "arpob")
        _store("us_revenue_pct", extracted.get("us_revenue_pct"), "%", "us_revenue_pct")
        _store("alos_days", extracted.get("alos_days"), "days", "alos")
        _store("arpp_inr", extracted.get("arpp_inr"), "INR", "arpp")
        _store("operational_beds", extracted.get("operational_beds"), "count", "operational_beds")
        return inserted
    elif sector_name in ("Services", "Logistics", "Aviation", "Infrastructure"):
        for field, unit, suffix in [
            ("headcount", "units", "headcount"), ("attrition_pct", "%", "attrition"),
            ("capacity_utilization_pct", "%", "capacity_utilization"), ("passengers_mn", "Mn", "passengers_mn"),
            ("load_factor_pct", "%", "load_factor"), ("ask_bn", "Bn", "ask_bn"), ("cask_inr", "INR", "cask"),
            ("cask_ex_fuel_inr", "INR", "cask_ex_fuel"), ("yield_inr", "INR", "yield"),
            ("cargo_volume_mmt", "MT", "cargo_volume_mmt"), ("container_teu_mn", "Mn", "container_teu_mn"),
            ("shipments_mn", "Mn", "shipments_mn"), ("tce_usd_per_day", "USD/day", "tce_usd_per_day"),
            ("order_inflow_cr", "INR Cr", "order_inflow"), ("order_backlog_cr", "INR Cr", "order_backlog"),
            ("tonnage_kt", "kt", "tonnage_kt"), ("realisation_per_tonne_inr", "INR", "realisation_per_tonne"),
            ("warehouse_area_mn_sqft", "Mn sq ft", "warehouse_area_mn_sqft"),
            ("aero_yield_per_pax_inr", "INR", "aero_yield_per_pax"),
            ("nonaero_income_per_pax_inr", "INR", "nonaero_income_per_pax"),
            ("fleet_vessels", "units", "fleet_vessels"), ("fleet_dwt_mn", "Mn dwt", "fleet_dwt_mn"),
            ("tce_crude_usd_per_day", "USD/day", "tce_crude"), ("tce_product_usd_per_day", "USD/day", "tce_product"),
            ("tce_dry_bulk_usd_per_day", "USD/day", "tce_dry_bulk"), ("employee_cost_cr", "INR Cr", "employee_cost"),
        ]:
            _store(field, extracted.get(field), unit, suffix)
        emp = next((r for r in inserted if r.metric_key == f"qtr_{prefix}_employee_cost"), None)
        rev_for_cost = _to_float(extracted.get("revenue_cr"))
        if emp is not None and rev_for_cost:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=f"qtr_{prefix}_employee_cost_pct", period=period,
                value=round(float(emp.value) / rev_for_cost * 100, 2), unit="%", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="employee_cost_cr / revenue_cr * 100 (same document)",
                source_url=source_url, source_document=source_document, source_date=now)
            if row is not None:
                inserted.append(row)
        stated_growth = _to_float(extracted.get("volume_growth_yoy_pct"))
        if stated_growth is not None:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_volume_growth_yoy", period=period, value=stated_growth,
                unit="%", statement_type=statement_type, source=_source_ctx.get(), source_tier=1,
                reported_or_calculated="REPORTED", confidence=_conf("HIGH"), source_url=source_url,
                source_document=source_document, source_date=now, raw_reported_value=str(stated_growth))
            if row is not None:
                inserted.append(row)
        rev = _to_float(extracted.get("revenue_cr"))
        inflow = next((r for r in inserted if r.metric_key == f"qtr_{prefix}_order_inflow"), None)
        if inflow is not None and rev:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=f"qtr_{prefix}_book_to_bill", period=period,
                value=round(float(inflow.value) / rev, 2), unit="x", statement_type=statement_type,
                source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="order_inflow_cr / revenue_cr (same document, same quarter)",
                source_url=source_url, source_document=source_document, source_date=now)
            if row is not None:
                inserted.append(row)
        return inserted
    elif sector_name == "Utilities":
        for field, unit, suffix in [
            ("order_inflow_cr", "INR Cr", "order_inflow"), ("order_inflow_yoy_prior_cr", "INR Cr", "order_inflow_yoy_prior"),
            ("order_backlog_cr", "INR Cr", "order_backlog"), ("order_backlog_yoy_prior_cr", "INR Cr", "order_backlog_yoy_prior"),
            ("waste_processed_kt", "kt", "waste_processed_kt"), ("waste_collected_kt", "kt", "waste_collected_kt"),
            ("treatment_capacity_mld", "MLD", "treatment_capacity_mld"), ("customers_mn", "Mn", "customers_mn"),
            ("collection_efficiency_pct", "%", "collection_efficiency"), ("network_km", "km", "network_km"),
        ]:
            _store(field, extracted.get(field), unit, suffix)
        _store_order_ratios(db, company_id, prefix, period, statement_type, source_url, source_document, now,
                            extracted, inserted)
        return inserted
    elif sector_name in ("Power", "Renewable Energy"):
        for field, unit, suffix in [
            ("installed_capacity_mw", "MW", "installed_capacity_mw"),
            ("installed_capacity_yoy_prior_mw", "MW", "installed_capacity_yoy_prior_mw"),
            ("thermal_capacity_mw", "MW", "thermal_capacity_mw"), ("renewable_capacity_mw", "MW", "renewable_capacity_mw"),
            ("capacity_under_construction_mw", "MW", "capacity_pipeline_mw"), ("generation_mu", "MU", "generation_mu"),
            ("plf_pct", "%", "plf"), ("availability_pct", "%", "availability"), ("cuf_pct", "%", "cuf"),
            ("ppa_contracted_pct", "%", "ppa_contracted_pct"), ("avg_tariff_inr_per_kwh", "INR/kWh", "avg_tariff"),
            ("transmission_availability_pct", "%", "transmission_availability"),
            ("network_ckm", "ckm", "network_ckm"), ("transformation_capacity_mva", "MVA", "transformation_mva"),
            ("distribution_loss_pct", "%", "td_loss"), ("atc_loss_pct", "%", "atc_loss"),
            ("collection_efficiency_pct", "%", "collection_efficiency"), ("trading_volume_bu", "Bn units", "trading_volume_bu"),
            ("capex_cr", "INR Cr", "capex"),
        ]:
            _store(field, extracted.get(field), unit, suffix)
        by = {r.metric_key: float(r.value) for r in inserted}
        cap, cap_prior = by.get(f"qtr_{prefix}_installed_capacity_mw"), by.get(f"qtr_{prefix}_installed_capacity_yoy_prior_mw")

        def _derived(key, value, unit, formula):
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=f"qtr_{prefix}_{key}", period=period, value=round(value, 2),
                unit=unit, statement_type=statement_type, source=_source_ctx.get(), source_tier=1,
                reported_or_calculated="CALCULATED", confidence="MEDIUM", calculation_formula=formula,
                source_url=source_url, source_document=source_document, source_date=now)
            if row is not None:
                inserted.append(row)

        if cap is not None and cap_prior:
            _derived("capacity_growth_yoy", (cap - cap_prior) / cap_prior * 100, "%", "(operational MW - year-ago MW) / year-ago MW * 100")
        rev, ebitda, capex = (_to_float(extracted.get(k)) for k in ("revenue_cr", "ebitda_cr", "capex_cr"))
        if rev and ebitda is not None and capex is not None:
            _derived("ebitda_minus_capex_margin", (ebitda - capex) / rev * 100, "%", "(ebitda_cr - capex_cr) / revenue_cr * 100")
        if rev and ebitda is not None:
            _derived("ebitda_margin", ebitda / rev * 100, "%", "ebitda_cr / revenue_cr * 100 (same document)")
        return inserted
    elif sector_name == "Telecom":
        for field, unit, suffix in [
            ("arpu_inr", "INR", "arpu"), ("subscribers_mn", "Mn", "subscribers_mn"),
            ("subscribers_yoy_prior_mn", "Mn", "subscribers_yoy_prior_mn"), ("net_adds_mn", "Mn", "net_adds_mn"),
            ("churn_pct", "%", "churn"), ("data_usage_gb_per_sub", "GB", "data_usage_gb"),
            ("subscribers_4g5g_mn", "Mn", "subscribers_4g5g_mn"), ("subscribers_4g5g_pct", "%", "subscribers_4g5g_pct"),
            ("broadband_homes_mn", "Mn", "broadband_homes_mn"),
            ("towers", "units", "towers"), ("colocations", "units", "colocations"),
            ("tenancy_ratio", "x", "tenancy"), ("order_inflow_cr", "INR Cr", "order_inflow"),
            ("order_backlog_cr", "INR Cr", "order_backlog"), ("capex_cr", "INR Cr", "capex"),
            ("africa_arpu_usd", "USD", "africa_arpu_usd"), ("africa_subscribers_mn", "Mn", "africa_subscribers_mn"),
            ("africa_subscribers_yoy_prior_mn", "Mn", "africa_subscribers_yoy_prior_mn"),
            ("africa_net_adds_mn", "Mn", "africa_net_adds_mn"), ("africa_churn_pct", "%", "africa_churn"),
            ("africa_data_usage_gb_per_sub", "GB", "africa_data_usage_gb"),
            ("africa_data_customers_mn", "Mn", "africa_data_customers_mn"), ("africa_towers", "units", "africa_towers"),
            ("africa_mobile_money_active_mn", "Mn", "africa_mobile_money_active_mn"),
            ("group_customers_mn", "Mn", "group_customers_mn"),
            ("data_traffic_bn_gb", "Bn GB", "data_traffic_bn_gb"),
            ("spectrum_liability_cr", "INR Cr", "spectrum_liability"), ("agr_liability_cr", "INR Cr", "agr_liability"),
        ]:
            _store(field, extracted.get(field), unit, suffix)

        def _derived(key, value, unit, formula):
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=f"qtr_{prefix}_{key}", period=period, value=round(value, 2),
                unit=unit, statement_type=statement_type, source=_source_ctx.get(), source_tier=1,
                reported_or_calculated="CALCULATED", confidence="MEDIUM", calculation_formula=formula,
                source_url=source_url, source_document=source_document, source_date=now)
            if row is not None:
                inserted.append(row)

        by = {r.metric_key: float(r.value) for r in inserted}
        subs, prior = by.get(f"qtr_{prefix}_subscribers_mn"), by.get(f"qtr_{prefix}_subscribers_yoy_prior_mn")
        if subs is not None and prior:
            _derived("subscriber_growth_yoy", (subs - prior) / prior * 100, "%", "(subscribers - year-ago subscribers) / year-ago * 100")
        a_subs, a_prior = by.get(f"qtr_{prefix}_africa_subscribers_mn"), by.get(f"qtr_{prefix}_africa_subscribers_yoy_prior_mn")
        if a_subs is not None and a_prior:
            _derived("africa_subscriber_growth_yoy", (a_subs - a_prior) / a_prior * 100, "%", "(Africa customers - year-ago) / year-ago * 100")
        _rev = _to_float(extracted.get("revenue_cr"))
        _data_rev = _to_float(extracted.get("data_revenue_cr"))
        if _rev and _data_rev is not None:
            _derived("data_revenue_pct", _data_rev / _rev * 100, "%", "data_revenue_cr / revenue_cr * 100 (same document)")
        _mob_rev, _gb = _to_float(extracted.get("mobile_revenue_cr")), by.get(f"qtr_{prefix}_data_traffic_bn_gb")
        if _mob_rev and _gb:
            _derived("revenue_per_gb", _mob_rev / (_gb * 100), "INR", "mobile_revenue_cr / (data_traffic_bn_gb * 100) — includes voice revenue")
        towers, colo = by.get(f"qtr_{prefix}_towers"), by.get(f"qtr_{prefix}_colocations")
        if towers and colo and f"qtr_{prefix}_tenancy" not in by:
            _derived("tenancy", colo / towers, "x", "colocations / towers")
        rev, ebitda, capex = (_to_float(extracted.get(k)) for k in ("revenue_cr", "ebitda_cr", "capex_cr"))
        if rev and ebitda is not None and capex is not None:
            _derived("ebitda_minus_capex_margin", (ebitda - capex) / rev * 100, "%", "(ebitda_cr - capex_cr) / revenue_cr * 100")
        _store_order_ratios(db, company_id, prefix, period, statement_type, source_url, source_document, now,
                            {"revenue_cr": extracted.get("revenue_cr")}, inserted)
        return inserted
    elif sector_name == "Information Technology":
        for field, unit, suffix in [
            ("cc_growth_yoy_pct", "%", "cc_growth_yoy"), ("cc_growth_qoq_pct", "%", "cc_growth_qoq"),
            ("revenue_usd_mn", "USD Mn", "revenue_usd_mn"), ("headcount", "units", "headcount"),
            ("attrition_pct", "%", "attrition"), ("utilization_pct", "%", "utilization"),
            ("deal_tcv_usd_bn", "USD Bn", "deal_tcv"), ("large_deal_tcv_usd_bn", "USD Bn", "large_deal_tcv"),
            ("top5_client_pct", "%", "top5_client_pct"), ("top10_client_pct", "%", "top10_client_pct"),
            ("north_america_revenue_pct", "%", "north_america_pct"), ("europe_revenue_pct", "%", "europe_pct"),
            ("bfsi_revenue_pct", "%", "bfsi_pct"), ("offshore_effort_pct", "%", "offshore_effort_pct"),
            ("million_dollar_clients", "units", "million_dollar_clients"),
        ]:
            _store(field, extracted.get(field), unit, suffix)
        rev = next((r for r in inserted if r.metric_key == "qtr_it_revenue_usd_mn"), None)
        hc = next((r for r in inserted if r.metric_key == "qtr_it_headcount"), None)
        if rev is not None and hc is not None and hc.value:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="qtr_it_revenue_per_employee", period=period,
                value=round(float(rev.value) * 4 / float(hc.value) * 1000, 2), unit="USD k",
                statement_type=statement_type, source=_source_ctx.get(), source_tier=1,
                reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="revenue_usd_mn * 4 / period-end headcount * 1000 (annualised quarter)",
                source_url=source_url, source_document=source_document, source_date=now,
            )
            if row is not None:
                inserted.append(row)
        return inserted
    elif sector_name in ("Capital Goods", "Industrials", "Defence", "Construction"):
        _store("order_inflow_cr", extracted.get("order_inflow_cr"), "INR Cr", "order_inflow")
        _store("order_inflow_yoy_prior_cr", extracted.get("order_inflow_yoy_prior_cr"), "INR Cr", "order_inflow_yoy_prior")
        _store("order_backlog_cr", extracted.get("order_backlog_cr"), "INR Cr", "order_backlog")
        _store("order_backlog_yoy_prior_cr", extracted.get("order_backlog_yoy_prior_cr"), "INR Cr", "order_backlog_yoy_prior")
        _store("export_order_pct", extracted.get("export_order_pct"), "%", "export_order_pct")
        _store("aftermarket_order_pct", extracted.get("aftermarket_order_pct"), "%", "aftermarket_order_pct")
        _store("capacity_utilization_pct", extracted.get("capacity_utilization_pct"), "%", "capacity_utilization")
        _store("international_backlog_pct", extracted.get("international_backlog_pct"), "%", "international_backlog_pct")
        _store_order_ratios(db, company_id, prefix, period, statement_type, source_url, source_document, now,
                            extracted, inserted)
        return inserted

    _compute_ratios(db, company_id, sector_name, prefix, period, statement_type, source_url, source_document, now, inserted)
    return inserted



def _store_order_ratios(db, company_id, prefix, period, statement_type, source_url, source_document, now,
                        extracted, inserted) -> None:
    """Capital Goods order-book ratios. A YoY growth the document itself states
    is stored REPORTED and wins; otherwise it is derived from the current and
    year-ago figures (CALCULATED). Book-to-bill uses the revenue figure the SAME
    document gives for the same entity as the orders. Backlog/TTM revenue needs
    four consecutive Screener quarters ending at `period`; skipped otherwise."""
    by_key = {row.metric_key: row for row in inserted}

    def _put(suffix, value, unit, kind, formula=None, confidence="MEDIUM", raw=None):
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key=f"qtr_{prefix}_{suffix}", period=period,
            value=round(value, 2), unit=unit, statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated=kind,
            confidence=_conf(confidence) if kind == "REPORTED" else confidence, calculation_formula=formula,
            source_url=source_url, source_document=source_document, source_date=now, raw_reported_value=raw,
        )
        if row is not None:
            inserted.append(row)

    for base, label in (("order_inflow", "order_inflow"), ("order_backlog", "order_backlog")):
        stated = _to_float(extracted.get(f"{base}_growth_pct"))
        cur, prior = by_key.get(f"qtr_{prefix}_{base}"), by_key.get(f"qtr_{prefix}_{base}_yoy_prior")
        if stated is not None:
            _put(f"{label}_growth_yoy", stated, "%", "REPORTED", confidence="HIGH", raw=str(stated))
        elif cur is not None and prior is not None and prior.value:
            _put(f"{label}_growth_yoy", (float(cur.value) - float(prior.value)) / float(prior.value) * 100, "%",
                 "CALCULATED", formula=f"(qtr_{prefix}_{base} - qtr_{prefix}_{base}_yoy_prior) / qtr_{prefix}_{base}_yoy_prior * 100")

    inflow, revenue = by_key.get(f"qtr_{prefix}_order_inflow"), _to_float(extracted.get("revenue_cr"))
    if inflow is not None and revenue:
        _put("book_to_bill", float(inflow.value) / revenue, "x", "CALCULATED",
             formula="order_inflow_cr / revenue_cr (same document, same quarter)")

    backlog = by_key.get(f"qtr_{prefix}_order_backlog")
    if backlog is not None:
        from app.calculations.quarterly_intelligence.series import quarter_series
        sales = quarter_series(db, company_id, "qtr_sales", statement_type)
        last4 = [p for p in sorted(sales) if p <= period][-4:]
        # four quarters ending at `period`: first one must be ~9 months before it
        if len(last4) == 4 and last4[-1] == period and (
                datetime.fromisoformat(period) - datetime.fromisoformat(last4[0])).days <= 290:
            ttm = sum(float(sales[p]) for p in last4)
            if ttm > 0:
                _put("order_backlog_to_ttm_revenue", float(backlog.value) / ttm, "x", "CALCULATED",
                     formula="order_backlog_cr / sum(qtr_sales, last 4 quarters)")


def _compute_ratios(db: Session, company_id: str, sector_name: str, prefix: str, period: str,
                     statement_type: str, source_url: str, source_document: str, now: datetime,
                     inserted: list) -> None:
    """Derives volume_growth_yoy + per-tonne/unit ratios from the raw
    fields just stored, combined with the SAME quarter's
    `qtr_sales`/`qtr_operating_profit` (Screener-sourced, already in the
    ledger via quarterly_results_client.py's Tier-1 ingestion). Reuses
    the exact same "prefer a directly-reported figure over a derived one"
    precedent the annual engine's Metals ratio block established."""
    by_key = {row.metric_key: row for row in inserted}

    current_key = f"qtr_{prefix}_units_sold" if sector_name == "Automobile" else (
        f"qtr_{prefix}_sales_mnt" if sector_name in ("Cement", "Metals", "Mining") else f"qtr_{prefix}_sales_tonnes"
    )
    yoy_key = current_key + "_yoy_prior"
    current_row = by_key.get(current_key)
    yoy_row = by_key.get(yoy_key)

    if current_row is not None and yoy_row is not None and yoy_row.value:
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="qtr_volume_growth_yoy", period=period,
            value=round((float(current_row.value) - float(yoy_row.value)) / float(yoy_row.value) * 100, 2),
            unit="%", statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
            confidence="MEDIUM", calculation_formula=f"({current_key} - {yoy_key}) / {yoy_key} * 100",
            source_url=source_url, source_document=source_document, source_date=now,
        )
        if row is not None:
            inserted.append(row)

    if sector_name not in ("Cement", "Metals", "Mining"):
        return  # per-tonne ratios only meaningful for tonne-denominated sectors

    volume_row = current_row
    if volume_row is None or not volume_row.value:
        return
    volume_mnt = float(volume_row.value)

    reported_ebitda = by_key.get(f"qtr_{prefix}_ebitda_per_tonne_reported")
    reported_cost = by_key.get(f"qtr_{prefix}_cost_per_tonne_reported")

    revenue_row = _latest_fiscal_value(db, company_id, "qtr_sales", statement_type, period=period)
    ebitda_row = _latest_fiscal_value(db, company_id, "qtr_operating_profit", statement_type, period=period)

    realisation = None
    if revenue_row is not None and revenue_row.value:
        realisation = float(revenue_row.value) * 10 / volume_mnt
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="qtr_realisation_per_tonne", period=period,
            value=round(realisation, 2), unit="INR", statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
            confidence="MEDIUM", calculation_formula=f"qtr_sales_cr * 10 / {current_key}",
            source_url=source_url, source_document=source_document, source_date=now,
        )
        if row is not None:
            inserted.append(row)

    ebitda_per_tonne = float(reported_ebitda.value) if reported_ebitda is not None and reported_ebitda.value is not None else None
    if ebitda_per_tonne is not None:
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="qtr_ebitda_per_tonne", period=period,
            value=ebitda_per_tonne, unit="INR", statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
            confidence=_conf("HIGH"), calculation_formula="directly stated in the company's own deck — not derived",
            source_url=source_url, source_document=source_document, source_date=now,
        )
        if row is not None:
            inserted.append(row)
    elif ebitda_row is not None and ebitda_row.value:
        ebitda_per_tonne = float(ebitda_row.value) * 10 / volume_mnt
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="qtr_ebitda_per_tonne", period=period,
            value=round(ebitda_per_tonne, 2), unit="INR", statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
            confidence="MEDIUM", calculation_formula=f"qtr_operating_profit_cr * 10 / {current_key}",
            source_url=source_url, source_document=source_document, source_date=now,
        )
        if row is not None:
            inserted.append(row)

    cost_per_tonne = float(reported_cost.value) if reported_cost is not None and reported_cost.value is not None else None
    if cost_per_tonne is not None:
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="qtr_cost_per_tonne", period=period,
            value=cost_per_tonne, unit="INR", statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated="REPORTED",
            confidence=_conf("HIGH"), calculation_formula="directly stated in the company's own deck — not derived",
            source_url=source_url, source_document=source_document, source_date=now,
        )
        if row is not None:
            inserted.append(row)
    elif realisation is not None and ebitda_per_tonne is not None:
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="qtr_cost_per_tonne", period=period,
            value=round(realisation - ebitda_per_tonne, 2), unit="INR", statement_type=statement_type,
            source=_source_ctx.get(), source_tier=1, reported_or_calculated="CALCULATED",
            confidence="MEDIUM", calculation_formula="qtr_realisation_per_tonne - qtr_ebitda_per_tonne",
            source_url=source_url, source_document=source_document, source_date=now,
        )
        if row is not None:
            inserted.append(row)
