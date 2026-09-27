"""THE Annual Report Extraction Engine — canonical reference for every
sector-specific note-extraction area in this app. See "Important md files/
Annual_Report_Fetching_Extraction_Engine.md" for the upstream master spec
this module implements (section location, period control, standalone/
consolidated scope, sign normalization, units, confidence tiers, source
lineage). Before adding a new extraction area for a new sector (Metals &
Mining, Construction Materials, etc. — see "Important md files/Sector
analysis framework/"), CHECK THE AREA REGISTRY BELOW first: an existing
area may already cover what's needed, or a near-miss may only need a
keyword/prompt tweak in annual_report_locator.py rather than a whole new
area.

Pipeline: NSE-primary/BSE-fallback document fetch (_fetch_nse_annual_report/
_fetch_bse_annual_report) -> keyword-density page locator
(annual_report_locator.py's locate_sections(), also resolving each area's
STANDALONE/CONSOLIDATED scope) -> one targeted LLM call per area
(_AREA_PROMPTS, "never invent a number") -> fallback-LLM guard (below;
skips storage rather than risk a wrong value) -> metric_store insert with
full source lineage (source_url/source_document/source_date/confidence).

AREA REGISTRY (area key -> what it extracts -> status):

| Area                | Extracts                                             | Status |
|----------------------|-------------------------------------------------------|--------|
| asset_quality         | PCR, slippage ratio                                    | WIRED (banking-only) |
| funding                | CASA ratio                                              | WIRED (banking-only) |
| capital                 | CET1, Tier 1/2 ratios                                   | WIRED (banking-only) |
| other_liabilities       | deferred_revenue, accrued_expenses breakdown            | WIRED (universal, any sector) |
| ppe                      | Gross PPE / accumulated depreciation / CWIP             | BUILT, NOT WIRED — live testing found it silently returns wrong-year figures often enough not to trust; a more dangerous failure mode than a null. Do not wire to storage without a validated fix. |
| raw_material             | Cost of Materials Consumed                              | WIRED (universal; validated on Pidilite, Aarti) |
| energy_cost              | Power & Fuel expense                                     | WIRED (universal; validated on Pidilite, Aarti) |
| revenue_geography        | domestic/export revenue split, customer concentration    | WIRED (universal; validated on Pidilite, Aarti) |
| rd_expenditure            | R&D capital/recurring/total spend                        | WIRED (universal; validated on Pidilite, Aarti) |
| cement_operating_metrics  | Cement production/installed capacity (MMT/MTPA), capacity utilization % | WIRED (Cement-sector; first area sourced from MD&A rather than notes-to-accounts; validated on UltraTech Cement, documented miss on Ambuja Cements — see prompt comment) |
| paper_operating_metrics   | Paper production/sales volume (tonnes), installed capacity, capacity utilization % | WIRED (Forest Materials-sector; narrative-tolerant prompt, no prior-year field — validated on TNPL, documented miss on JK Paper) |
| metals_operating_metrics  | Metal production/sales volume (million tonnes), directly-reported EBITDA/tonne | WIRED (Metals & Mining-sector; validated on JSW Steel (full data incl. direct EBITDA/tonne) and Tata Steel (volume only), documented miss on Hindalco — scrambled chart text) |
| automobile_operating_metrics | Vehicle units sold (current+prior year), market share %, dealer inventory days | WIRED (Automobile OEM-sector; validated on Maruti Suzuki (volume + dealer inventory) and Bajaj Auto (volume + growth % + market share, all in one table)) |

Every wired area gets two section-agnostic guarantees for free: the
fallback-LLM-detection guard (`default_llm_client.last_used_fallback`)
skips STORAGE entirely rather than risk a wrong value tagged HIGH
confidence, and `locate_sections()`'s per-area statement_type resolution
means the correct STANDALONE/CONSOLIDATED tag travels with each area
independently rather than being assumed uniform across the whole report.

Not yet covered (candidates for a NEW area, not a rebuild of this
machinery): sector-specific narrative/MD&A KPIs from the master spec's
Universal Operating-KPI Dictionary for other sectors (e.g. Metals &
Mining's ore grade/recovery/cash-cost) — `cement_operating_metrics` above
is the first area sourced from MD&A rather than notes-to-accounts, so its
locator/prompt design (narrow, high-precision anchor terms; explicit
"return null if the layout is a scattered infographic, don't guess"
instruction; per-tonne cost breakdown deliberately NOT extracted after a
live-caught field-swap risk) is the template to reuse, not a from-scratch
problem. Check annual_report_locator.py's _AREA_TERMS first for a
close-enough existing keyword set before adding a new one.

Extracts metrics no other source in this app supplies, from NSE's annual
report — real text extraction (pdfplumber), no OCR needed.

Originally banking-only: the three metrics BSE's quarterly filing can't
supply (CASA ratio, Provision Coverage Ratio, slippage ratio), plus
CET1/Tier 1 as a bonus supplement to BSE's CAR. Generalized to every sector
(2026-09-16) with one universal area shipped — the Other Liabilities
breakdown (Screener folds accrued expenses and deferred revenue into one
aggregate `other_liabilities` line with no way to separate them), validated
live against two real reports (TCS: deferred_revenue=694; Coforge:
deferred_revenue=158, both correct and reproducible across repeated runs).

A second area, Gross PPE, is BUILT but deliberately NOT wired to storage
(see its own prompt's comment below) — live testing against the same two
companies found it silently returns wrong-year figures often enough not to
trust yet, a materially different and more dangerous failure mode than an
honest null. Both areas were chosen over local Llama for the same reason:
Groq's `gpt-oss-20b` (this module's existing LLM, `app/llm/client.py`)
measurably outperformed a local `qwen3-embedding`+`llama3.2:3b` pipeline
tested on the same real tables — local Llama's errors were silent digit
transpositions, not just nulls, the worse failure mode for an app whose
whole design principle is never fabricating a number.

Page selection is keyword-based (app/ingestion/annual_report_locator.py) —
the earlier semantic/embedding approach (qwen3-embedding via local Ollama,
app/ingestion/embeddings/) was removed: it added a slow, NSE- and
Ollama-availability-dependent indexing step that stalled the pipeline for
minutes on every run, and Screener.in now covers most of what that was
built to reach more directly and reliably. See ARCHITECTURE.md /
IMPLEMENTATION_PLAN.md for the removal note.

One small, targeted LLM call per disclosure area rather than one giant call:
keeps each request's token footprint predictable (same max_tokens=3000 lesson
learned in banking_ingestion.py — gpt-oss-20b needs real budget for internal
reasoning even in JSON mode) and lets one area's failure not sink the others.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone

import pdfplumber
from sqlalchemy.orm import Session

from app.ingestion import bse_client, nse_client
from app.ingestion.annual_report_locator import locate_sections
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Document
from app.infrastructure.redis.client import cache_get, cache_set
from app.infrastructure.storage.minio_client import put_document
from app.llm.client import llm_client as default_llm_client
from app.logger import logger

_BATCH_GATE_TTL = 60 * 60 * 24 * 300  # mirrors orchestrator.py's per-company annual-report gate

_MAX_TOKENS = 3000
_MAX_CHARS_PER_AREA = 8000
# ppe/other_liabilities can run a bit larger than the banking areas' 8000
# (real single pages here can be 8-9k chars each) — but NOT much larger:
# this account's Groq tier has an 8000-TOKEN-PER-MINUTE hard cap (confirmed
# live: a 413 rate-limit error on a ~9,500-token request), which is almost
# certainly why 8000 CHARS was chosen for the original banking areas in the
# first place — English runs ~4 chars/token, so 8000 chars stays safely
# under budget once max_tokens=3000 (output) and prompt overhead are
# accounted for. `annual_report_locator.py`'s `_AREA_PEAK_ONLY` selection
# (a tight ±1 page margin around the single best-matching page, not a wide
# window) is what actually solved the "real table missing from the
# extracted text" problem here — this override just gives a little more
# headroom for that tight selection, not a license to widen it further.
_MAX_CHARS_OVERRIDE = {
    "ppe": 12000, "other_liabilities": 12000,
    # Same fix, same reason — real bug caught live 2026-09-20 on Aarti
    # Industries' rd_expenditure area: its 3-page peak-page selection
    # totalled 22,424 chars with the actual R&D table starting at char
    # 11,777 — the default 8000-char cutoff sliced the table out entirely
    # before the LLM ever saw it (silently returning all-null, not an
    # extraction failure, a truncation failure). 12000 mirrors ppe/
    # other_liabilities' already-proven-safe budget under Groq's 8000-
    # tokens-per-minute cap.
    "raw_material": 12000, "energy_cost": 12000, "revenue_geography": 12000,
    # rd_expenditure needs a bit more than the others — confirmed on Aarti
    # Industries that its R&D table sits inside a two-column PDF layout
    # (pdfplumber interleaves the R&D table's left column with an unrelated
    # corporate-governance paragraph from the right column, line by line),
    # pushing the table's closing "Total" row to ~char 12,250 even though
    # the table's own heading appears at ~11,777. The interleaved narrative
    # text doesn't corrupt the actual data lines themselves (each stays
    # intact and correctly labelled), it just pushes everything later.
    "rd_expenditure": 13000,
    # Confirmed live on UltraTech Cement: the 3-page peak selection (pages
    # 122-124) totals 14,946 chars, with "Capacity Utilisation"/"Installed
    # capacity" starting around char 7,000-7,470 — close enough to the
    # default 8000-char cutoff to risk truncation on a company whose table
    # sits slightly later on the page (same truncation-not-failure pattern
    # already caught on Aarti's rd_expenditure area).
    "cement_operating_metrics": 10000,
    # Confirmed live on JSW Steel: the real "crude steel production stood
    # at..." sentence sits at char 7,072 within the 3-page peak selection
    # (16,284 chars total) — close enough to the default 8000-char cutoff
    # to risk truncation on a company whose equivalent text sits slightly
    # later on the page (same truncation-not-failure pattern as the other
    # operating-metrics areas).
    "metals_operating_metrics": 12000,
}

_AREA_PROMPTS = {
    "asset_quality": (
        "Extract asset-quality figures from this Indian bank's annual report notes-to-accounts. "
        "If a field isn't present, return null. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "provision_coverage_ratio_pct": number|null,\n'
        '  "slippage_ratio_pct": number|null,\n'
        '  "fresh_slippages_amount": number|null,\n'
        '  "opening_standard_advances": number|null,\n'
        '  "restructured_assets_pct": number|null,\n'
        '  "period_label": "as-at date printed in the text, or null"\n'
        "}"
    ),
    "funding": (
        "Extract the CASA (Current + Savings Account deposits) figures from this Indian bank's "
        "annual report. If a field isn't present, return null. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "casa_ratio_pct": number|null,\n'
        '  "casa_deposits_amount": number|null,\n'
        '  "total_deposits_amount": number|null,\n'
        '  "period_label": "as-at date printed in the text, or null"\n'
        "}"
    ),
    "capital": (
        "Extract capital-adequacy figures from this Indian bank's annual report. If a field isn't "
        "present, return null. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "cet1_ratio_pct": number|null,\n'
        '  "tier1_ratio_pct": number|null,\n'
        '  "tier2_ratio_pct": number|null,\n'
        '  "period_label": "as-at date printed in the text, or null"\n'
        "}"
    ),
    # Universal (any sector). NOT wired to storage (see _AREA_METRIC_FIELDS
    # below — "ppe" has no entry there, so ingest_annual_report() never even
    # calls this) — kept here as working groundwork, not shipped. Live
    # testing against two real reports (TCS, Coforge) found this genuinely
    # unreliable in a dangerous way: it doesn't fail loudly, it sometimes
    # returns a fully-populated, plausible-looking JSON that's silently
    # wrong. Confirmed on Coforge: gross_block_opening/closing came back
    # correct (7894/8132), but accumulated_depreciation_closing and
    # net_carrying_amount both came back as the PRIOR year's closing
    # figures (3693/4201) instead of the requested year's (4171/3961) — the
    # same "table has two side-by-side year blocks with identically-labelled
    # rows" confusion documented for TCS below, just manifesting as
    # wrong-year rather than wrong-digit. Re-enable only after a fix that's
    # been validated to actually close this failure mode, not just prompt
    # tweaks (already tried and insufficient) — a MISSING_INPUT gap is
    # strictly safer than an occasionally-wrong "AVAILABLE" one.
    #
    # Values in these schedules are shown in parentheses, e.g. "(28,176)",
    # when they represent a deduction/decrease for that line (disposals,
    # depreciation-for-the-year) — but gross_block/accumulated_depreciation/
    # net_carrying_amount/CWIP are all requested here as the POSITIVE
    # closing MAGNITUDE of that balance, not a signed movement, so
    # parentheses on those specific lines should NOT flip the sign
    # (accumulated depreciation is shown parenthesized as a contra-asset in
    # the table, but is reported here as a positive amount).
    "ppe": (
        "Extract the Gross PPE figures from this Indian company's Property, Plant & Equipment "
        "note (the schedule showing Cost/gross block, additions, disposals, accumulated "
        "depreciation, and net carrying amount). Use the 'Total' column, never an individual "
        "asset category (land, buildings, plant, etc). If the table shows more than one fiscal "
        "year, use only the MOST RECENT one. The table may have TWO lines both labelled "
        "'Accumulated depreciation as at' for the same year — one dated the year's START (the "
        "OPENING balance) and one dated the year's END (the CLOSING balance, always the larger "
        "number since depreciation accumulates); use only the END-dated one for "
        "accumulated_depreciation_closing. Report gross_block/accumulated_depreciation/"
        "net_carrying_amount/capital_work_in_progress as positive magnitudes even where the table "
        "shows them in parentheses. If a field isn't present, return null. Never invent a number. "
        "Respond with JSON:\n"
        "{\n"
        '  "gross_block_opening": number|null,\n'
        '  "gross_block_closing": number|null,\n'
        '  "accumulated_depreciation_closing": number|null,\n'
        '  "net_carrying_amount": number|null,\n'
        '  "capital_work_in_progress": number|null,\n'
        '  "period_label": "as-at date printed in the text, or null"\n'
        "}"
    ),
    "other_liabilities": (
        "Extract the breakdown of Other Liabilities / Other Current Liabilities from this Indian "
        "company's balance sheet notes, for the most recent fiscal year shown (use the most "
        "recent 'As at' column if two years are shown).\n\n"
        "Map each line to ONE of the fields below ONLY if its label clearly means that concept — "
        "a close synonym is fine (e.g. 'Advance received from customers' → deferred_revenue, since "
        "that's a standard synonym for contract-liability/deferred-revenue balances), but a bare, "
        "generic label like 'Others' or 'Miscellaneous' with NO further description must go to "
        "other_current_liabilities, never be upgraded to a more specific field just because that "
        "field is in this schema and needs a value — you do not know what an unlabelled 'Others' "
        "line actually consists of. If a field's concept genuinely isn't broken out as its own "
        "line at all, return null for it — never invent a number, and never re-guess a different "
        "line for the same field if you're not confident; nulls are expected and fine for most "
        "companies on most of these fields. Values shown in parentheses like (1,234) are negative "
        "— convert to -1234. Respond with JSON:\n"
        "{\n"
        '  "deferred_revenue": number|null,\n'
        '  "accrued_expenses": number|null,\n'
        '  "statutory_liabilities": number|null,\n'
        '  "other_current_liabilities": number|null,\n'
        '  "period_label": "as-at date printed in the text, or null"\n'
        "}"
    ),
    # Chemicals-sector areas (2026-09-20) — all four prompts validated
    # against Pidilite Industries' real FY2025-26 standalone statements
    # before shipping (see annual_report_locator.py's comment for the
    # exact pages/figures confirmed). Sector-agnostic by construction —
    # every Ind-AS-reporting Indian company has a P&L statement and a
    # Board's Report annexure in this same shape, not just chemicals
    # companies; nothing here special-cases chemicals specifically.
    "raw_material": (
        "Extract the Cost of Materials Consumed figure from this Indian company's Statement of "
        "Profit and Loss (or the detailed note it references) — the amount shown next to the line "
        "labelled 'Cost of Materials Consumed', for the MOST RECENT year shown (if two columns are "
        "shown, use the more recent one, usually the left column). Do not sum multiple expense "
        "lines together, and do not confuse this with 'Purchases of Stock-in-Trade' or 'Changes in "
        "Inventories' — those are separate P&L lines. If a full breakdown note (Opening Inventory + "
        "Purchases - Closing Inventory) is shown instead of a single P&L line, use its TOTAL row, "
        "never compute it yourself from the components. If this line genuinely isn't present (common "
        "for services/IT/financial companies with no manufacturing), return null. If the figure is "
        "shown in parentheses like (1,234), that means negative — convert to -1234 (unusual for this "
        "field, but do not assume it can't happen). Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "raw_material_cost": number|null,\n'
        '  "period_label": "year ended date printed next to the figure, or null"\n'
        "}"
    ),
    "energy_cost": (
        "Extract the electricity/power expense figure from this Indian company's Other Expenses or "
        "Manufacturing Expenses note — it is ONE line among many in a longer expense breakdown (do "
        "not confuse it with 'Water Charges', 'Rent', 'Insurance', 'Freight', or the note's TOTAL — "
        "those are different lines), for the MOST RECENT year shown (if two columns are shown, use "
        "the more recent one, usually the left column). The label varies by company — accept any of "
        "'Power and Fuel', 'Power, Fuel and Water Charges', 'Power Cost', 'Power & Fuel', or a bare "
        "'Power' / 'Electricity Expenses' line if that is genuinely how this company labels it. Only "
        "use a combined 'Power, Fuel and Water' line if power/fuel isn't separately broken out from "
        "water — do not attempt to split a combined figure yourself. If this line genuinely isn't "
        "present, return null. If the figure is shown in parentheses like (1,234), that means "
        "negative — convert to -1234. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "power_fuel_cost": number|null,\n'
        '  "period_label": "year ended date printed next to the figure, or null"\n'
        "}"
    ),
    "revenue_geography": (
        "Extract two things from this Indian company's Segment Information / geography disclosure "
        "note, for the MOST RECENT year shown (if two columns are shown, use the more recent one, "
        "usually the left column):\n"
        "1. Revenue split by geography — the two lines are typically labelled 'India' and 'Outside "
        "India' (sometimes 'Within India'/'Outside India', a named list of countries for 'Outside "
        "India', or 'Local Sales'/'Export Sales' — map 'Local Sales' to domestic_revenue and "
        "'Export Sales' to export_revenue). Use the revenue-based-on-geography table specifically, "
        "not segment revenue by business line and not segment ASSETS by geography (a similar but "
        "different table sometimes on the same page).\n"
        "2. Customer concentration — look for a sentence about revenue from any single external "
        "customer. If it states a specific company/percentage (e.g. 'Customer X contributed 15% of "
        "revenue'), report that percentage. If it states the negative (e.g. 'there is no single "
        "customer which amounts to 10% or more of revenue'), report 0 — that is a real, confirmed "
        "finding, not a missing value. If neither kind of statement is present at all, return null.\n"
        "If a revenue figure is shown in parentheses like (1,234), that means negative — convert to "
        "-1234 (unusual for revenue, but do not assume it can't happen, e.g. a return/adjustment "
        "year). Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "domestic_revenue": number|null,\n'
        '  "export_revenue": number|null,\n'
        '  "single_customer_max_pct": number|null,\n'
        '  "period_label": "year ended date printed next to the figures, or null"\n'
        "}"
    ),
    "rd_expenditure": (
        "Extract the Research and Development expenditure table from this Indian company's Board's "
        "Report annexure on Conservation of Energy / Technology Absorption, for the MOST RECENT year "
        "shown (if two columns are shown, use the more recent one, usually the left column). The "
        "table typically has 'Capital' and 'Recurring' rows and a 'Total' row — the non-capital row "
        "is sometimes labelled 'Revenue' instead of 'Recurring' (same concept: R&D spend expensed "
        "in the year, not capitalized) — map either label to rd_expenditure_recurring. Use the "
        "Total row for rd_expenditure_total; if there's no Total row, only the Capital+Recurring/"
        "Revenue breakdown, report those two individually and leave rd_expenditure_total null "
        "rather than adding them yourself. Some tables show 3 years of columns — always use the "
        "MOST RECENT (leftmost) column only. If this disclosure genuinely isn't present (common for "
        "companies with no R&D program), return null for all fields. If a figure is shown in "
        "parentheses like (1,234), that means negative — convert to -1234. Never invent a number. "
        "Respond with JSON:\n"
        "{\n"
        '  "rd_expenditure_total": number|null,\n'
        '  "rd_expenditure_capital": number|null,\n'
        '  "rd_expenditure_recurring": number|null,\n'
        '  "period_label": "year ended date printed next to the figures, or null"\n'
        "}"
    ),
    # Cement-sector area (2026-09-20) — lives in the Management Discussion &
    # Analysis "Financial Performance" block, not notes-to-accounts.
    # Confirmed live on UltraTech Cement's real FY2025-26 report: a clean
    # "Particulars / FY26 / FY25 / % change" table gives Installed Capacity
    # (MTPA) and Production (MMT) directly — these 4 fields (both years'
    # capacity/production + the utilisation %) came back byte-identical
    # across two separate live extraction runs, a single unambiguous table.
    # Cross-checked on Ambuja Cements' real report: this table does NOT
    # exist there in extractable text form (its equivalent figures are laid
    # out as a scattered infographic/dashboard) — the locator still finds a
    # candidate page there, so this prompt must be conservative enough to
    # return null rather than mis-attribute a nearby unrelated number.
    #
    # Deliberately does NOT also ask for the per-tonne cost breakdown
    # (energy/raw-material/freight cost per tonne) even though UltraTech's
    # same page states them directly in a narrative "Cost Highlights"
    # block — live-tested and REJECTED: across two separate extraction runs
    # of the identical text, the raw-material and freight per-tonne figures
    # came back SWAPPED on the second run (₹653/₹1,146 vs ₹1,146/₹653), the
    # 3-column "Energy Cost | Input Material Costs | Freight and Forwarding
    # Expenses" narrative block apparently reads ambiguously enough that
    # LLM sampling isn't stable on it, even though the capacity/production
    # table on the SAME page never showed this problem. This app has none
    # of these three components as a scored CementSector metric anyway
    # (only the derived `cost_per_tonne` = realisation - EBITDA/tonne,
    # computed from production_mmt + Screener P&L data below, unaffected
    # by this narrative block) — same "don't wire what's been demonstrated
    # unreliable" precedent as the "ppe" area above.
    "cement_operating_metrics": (
        "This is a page from an Indian CEMENT company's annual report Management Discussion & "
        "Analysis section. Look for a clear 'Particulars / [year] / [prior year] / % change' style "
        "table with rows for Installed Capacity and Production (or Cement Production). Extract ONLY "
        "if the table unambiguously labels each number — if this page is a scattered infographic/"
        "dashboard where numbers and their labels can't be reliably matched (numbers and labels not "
        "clearly paired, e.g. a grid of unlabeled stat tiles), return null for every field rather than "
        "guessing. Report BOTH years for capacity/production so growth can be computed. Capacity/"
        "Production are usually in 'MTPA'/'MMT' (Million Tonnes Per Annum / Million Metric Tonnes) — "
        "report as plain million-tonne numbers (e.g. 143.83, not '143.83 MMT'). If a figure is shown "
        "in parentheses like (1,234), that means negative — convert to -1234. Never invent a number. "
        "Respond with JSON:\n"
        "{\n"
        '  "installed_capacity_mtpa": number|null,\n'
        '  "production_mmt": number|null,\n'
        '  "production_mmt_prior_year": number|null,\n'
        '  "capacity_utilization_pct": number|null,\n'
        '  "period_label": "year ended date printed next to the figures, or null"\n'
        "}"
    ),
    # Forest Materials (Paper)-sector area (2026-09-20). Unlike Cement's
    # clean current+prior-year table, confirmed live that Paper companies'
    # MD&A disclosure varies a lot: TNPL's real report gives current-year
    # Paper production/sales volume as a narrative "Performance Highlights"
    # bullet ("Paper sales was 4.48 lakh MT... Domestic Sales accounts for
    # 80% and Exports at 20%"), with NO prior-year comparison figure at
    # all — so this area deliberately does NOT ask for a prior year (no
    # volume_growth_yoy for this sector yet, a documented gap, not a
    # guess). JK Paper's report has no comparable disclosure in
    # extractable text — same "return null, don't guess" conservatism as
    # cement_operating_metrics handles the Ambuja Cements miss.
    "paper_operating_metrics": (
        "This is a page from an Indian PAPER company's annual report Management Discussion & "
        "Analysis section. Look for the company's PAPER production volume and PAPER sales volume for "
        "the year — may be stated in a table OR in narrative text (e.g. 'Paper production was X lakh "
        "MT', 'Paper sales was Y lakh MT'). If the company reports MULTIPLE product lines separately "
        "(e.g. Paper AND Packaging Board/Paperboard), use ONLY the figure specifically labelled "
        "'Paper' — do not sum or substitute a different product line's figure. Also look for installed "
        "capacity (tonnes or MTPA) and a directly-stated capacity utilization %, if present. Extract "
        "ONLY numbers that are unambiguously labelled — if this page is a scattered infographic/"
        "dashboard where numbers and labels can't be reliably matched, return null rather than "
        "guessing. Convert 'lakh' units to plain tonnes (1 lakh = 100,000, e.g. '4.34 lakh MT' -> "
        "434000). If a figure is shown in parentheses like (1,234), that means negative — convert to "
        "-1234. Never invent a number. Respond with JSON:\n"
        "{\n"
        '  "production_tonnes": number|null,\n'
        '  "sales_tonnes": number|null,\n'
        '  "installed_capacity_tonnes": number|null,\n'
        '  "capacity_utilization_pct": number|null,\n'
        '  "period_label": "year ended date printed next to the figures, or null"\n'
        "}"
    ),
    # Metals & Mining-sector area (2026-09-20). Confirmed live on JSW
    # Steel's real report: a clean MD&A "Production and Sales" section
    # gives current+prior-year crude steel production AND sales volume
    # (both Consolidated and Standalone), PLUS a directly-stated EBITDA/
    # tonne narrative figure ("EBITDA per tonne was at Rs.9,015... higher
    # by 7% y-o-y") — when this direct figure exists, prefer it outright
    # over deriving one from pnl_operating_profit/volume (same "trust the
    # company's own reported number" precedent as Cement's
    # capacity_utilization_pct). Tata Steel's report has usable narrative
    # data too ("combined saleable steel production... stood at 22.04 MT...
    # higher than FY2024-25 (20.34 MT) by 8%") but no direct EBITDA/tonne
    # figure. Hindalco's report has no comparably extractable text — its
    # production data is embedded in rotated chart labels that pdfplumber
    # extracts as scrambled, reversed digit strings — an accepted miss,
    # same conservatism as the other operating-metrics areas.
    "metals_operating_metrics": (
        "This is a page from an Indian METALS/MINING company's (steel, aluminium, copper, zinc, or "
        "mining) annual report Management Discussion & Analysis section. Look for the company's metal "
        "PRODUCTION volume and SALES volume for the year — may be stated in a table OR narrative text "
        "(e.g. 'crude steel production stood at X MnT... higher than FY[prior] (Y MnT) by Z%'). "
        "Prefer CONSOLIDATED figures if both Consolidated and Standalone are shown on this page; use "
        "Standalone only if Consolidated isn't present. If the company reports multiple commodities/"
        "product lines (e.g. Aluminium AND Copper), use ONLY the company's PRIMARY/largest metal line, "
        "not a byproduct or minor segment. Also look for a DIRECTLY-STATED EBITDA per tonne figure in "
        "the narrative (e.g. 'EBITDA per tonne was at Rs.X') — extract this only if it is an explicit "
        "sentence, never estimate one yourself. Extract ONLY numbers that are unambiguously labelled — "
        "if this page is a chart with scrambled/reversed digit text or a scattered infographic where "
        "numbers and labels can't be reliably matched, return null rather than guessing. Report "
        "production/sales as plain million-tonne numbers (e.g. 'MnT'/'MMT'/'MT' all mean million "
        "tonnes here — report 21.30 for '21.30 MnT', not the raw string). If a figure is shown in "
        "parentheses like (1,234), that means negative — convert to -1234. Never invent a number. "
        "Respond with JSON:\n"
        "{\n"
        '  "production_million_tonnes": number|null,\n'
        '  "production_million_tonnes_prior_year": number|null,\n'
        '  "sales_million_tonnes": number|null,\n'
        '  "ebitda_per_tonne_reported": number|null,\n'
        '  "period_label": "year ended date printed next to the figures, or null"\n'
        "}"
    ),
    # Automobile (OEM)-sector area (2026-09-20). Confirmed live on two real
    # reports with genuinely different disclosure styles: Maruti Suzuki's
    # early "Company Overview" section has a clean "Total Sales Volume (in
    # units)" 5-year callout with actual numbers as plain text (not a bar
    # chart image), giving current AND prior year in one place; Bajaj
    # Auto's MD&A instead has a "Table 1: Domestic Sale of Motorcycles"
    # 5-year table with company sales, growth %, AND market share % all
    # together — market_share is sometimes genuinely company-disclosed
    # (sourced from SIAM data in the report itself), not always requiring
    # third-party industry data as originally assumed.
    "automobile_operating_metrics": (
        "This is a page from an Indian AUTOMOBILE/VEHICLE OEM company's annual report. Look for the "
        "company's own vehicle sales/units volume for the CURRENT and PRIOR year — may be a multi-year "
        "callout list (e.g. 'Total Sales Volume (in units): 2,422,713 / 2,234,266 / ...' where the "
        "FIRST/LARGEST-labelled number is the most recent year) or a table with year rows (e.g. "
        "'2026 | 13,064,789 | 6.6% | 2,043,316 | 0.6% | 15.6%' — columns are typically Year | Industry "
        "volume | Industry growth | Company volume | Company growth | Company market share). If the "
        "company reports multiple products/segments (e.g. Motorcycles AND Three-Wheelers), use ONLY "
        "the FIRST/PRIMARY product table on this page, not a secondary one. Also look for: a directly-"
        "stated market share % for the CURRENT year, and a directly-stated dealer inventory figure in "
        "days/months of stock (e.g. 'dealer inventory remained low at around 12 days of stock'). "
        "Extract ONLY numbers that are unambiguously labelled — if this page is a scattered infographic "
        "where numbers and labels can't be reliably matched, return null rather than guessing. Report "
        "vehicle counts as plain whole numbers (e.g. 2422713, not '2,422,713' or '24.2 lakh'). If a "
        "figure is shown in parentheses like (1,234), that means negative — convert to -1234. Never "
        "invent a number. Respond with JSON:\n"
        "{\n"
        '  "units_sold": number|null,\n'
        '  "units_sold_prior_year": number|null,\n'
        '  "market_share_pct": number|null,\n'
        '  "dealer_inventory_days": number|null,\n'
        '  "period_label": "year ended date printed next to the figures, or null"\n'
        "}"
    ),
}

# (metric_key, field, unit)
_AREA_METRIC_FIELDS = {
    "asset_quality": [
        ("provision_coverage_ratio", "provision_coverage_ratio_pct", "%"),
        ("slippage_ratio", "slippage_ratio_pct", "%"),
    ],
    "funding": [
        ("casa_ratio", "casa_ratio_pct", "%"),
    ],
    "capital": [
        ("cet1_ratio", "cet1_ratio_pct", "%"),
        ("tier1_ratio", "tier1_ratio_pct", "%"),
    ],
    # "ppe" deliberately has NO entry here — see the "ppe" prompt's own
    # comment above for why extraction is built but not wired to storage.
    "other_liabilities": [
        ("deferred_revenue", "deferred_revenue", "cr"),
        ("accrued_expenses", "accrued_expenses", "cr"),
    ],
    # Chemicals-sector areas (2026-09-20) — validated live against two real
    # reports with genuinely different disclosure phrasing (Pidilite
    # Industries, Aarti Industries) before wiring to storage, same bar as
    # every area above. `raw_material_cost` note: some companies bundle
    # packing material/fuel/stores into this figure (confirmed on Aarti:
    # "Cost of Materials Consumed (Incl. Packing Material, Fuel, Stores &
    # Spares)"), others report a pure raw-material figure (Pidilite) — the
    # extracted number is always correctly what THIS company itself labels
    # "Cost of Materials Consumed," but the underlying composition isn't
    # perfectly comparable company-to-company. Document this at the
    # SectorMetric/description level, not by trying to un-bundle it here.
    "raw_material": [
        ("raw_material_cost", "raw_material_cost", "cr"),
    ],
    "energy_cost": [
        ("power_fuel_cost", "power_fuel_cost", "cr"),
    ],
    "revenue_geography": [
        ("export_revenue_reported", "export_revenue", "cr"),
        ("domestic_revenue_reported", "domestic_revenue", "cr"),
        ("single_customer_max_pct", "single_customer_max_pct", "%"),
    ],
    "rd_expenditure": [
        ("rd_expenditure_total", "rd_expenditure_total", "cr"),
        ("rd_expenditure_capital", "rd_expenditure_capital", "cr"),
        ("rd_expenditure_recurring", "rd_expenditure_recurring", "cr"),
    ],
    "cement_operating_metrics": [
        ("cement_installed_capacity_mtpa", "installed_capacity_mtpa", "MT"),
        ("cement_production_mmt", "production_mmt", "MT"),
        ("cement_production_mmt_prior", "production_mmt_prior_year", "MT"),
        ("capacity_utilization", "capacity_utilization_pct", "%"),
    ],
    "paper_operating_metrics": [
        ("paper_production_tonnes", "production_tonnes", "tonnes"),
        ("paper_sales_tonnes", "sales_tonnes", "tonnes"),
        ("paper_installed_capacity_tonnes", "installed_capacity_tonnes", "tonnes"),
        ("capacity_utilization", "capacity_utilization_pct", "%"),
    ],
    "metals_operating_metrics": [
        ("metals_production_mnt", "production_million_tonnes", "MT"),
        ("metals_production_mnt_prior", "production_million_tonnes_prior_year", "MT"),
        ("metals_sales_mnt", "sales_million_tonnes", "MT"),
        ("metals_ebitda_per_tonne_reported", "ebitda_per_tonne_reported", "INR"),
    ],
    "automobile_operating_metrics": [
        ("automobile_units_sold", "units_sold", "units"),
        ("automobile_units_sold_prior", "units_sold_prior_year", "units"),
        ("market_share", "market_share_pct", "%"),
        ("dealer_inventory_days", "dealer_inventory_days", "days"),
    ],
}


def _latest_fiscal_pnl_value(db: Session, company_id: str, metric_key: str, statement_type: str, n_prior: int = 0):
    """Same as `metric_store.get_latest_period_value()` but explicitly
    excludes the literal "TTM" pseudo-period `pnl_history_client.py` stores
    trailing-twelve-months `pnl_*` figures under — "TTM" sorts AFTER every
    real "YYYY-MM-DD" period in plain string comparison, so
    `get_latest_period_value()`'s own max()-over-periods would otherwise
    silently pick TTM revenue instead of the real fiscal year matching an
    annual-report-extracted figure (real bug found 2026-09-20 building the
    Cement per-tonne ratios below: realisation_per_tonne/ebitda_per_tonne
    came out computed against TTM revenue, not FY2025-26 revenue, with no
    error — just a plausible-looking but period-mismatched number). Matching
    the annual-report row's OWN period exactly was tried first and rejected:
    too brittle whenever the LLM's own `period_label` extraction lands on a
    fallback date rather than a clean fiscal year-end.

    `n_prior` (added for the Automobile area's ASP-growth calc, 2026-09-20):
    0 = latest fiscal period (the default, every existing caller), 1 = the
    period immediately before that, by SORT ORDER of whatever periods
    actually exist in the ledger — not "latest period's year minus 1" date
    arithmetic, which would be wrong whenever an annual-report row's own
    `period_label` fell back to a non-fiscal-year-end date (confirmed
    common live: UltraTech's cement_operating_metrics row landed on
    "2026-07-24", the document fetch date, not "2026-03-31")."""
    all_rows = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    fiscal_periods = sorted({r.period for r in all_rows if r.period != "TTM"}, reverse=True)
    if len(fiscal_periods) <= n_prior:
        return None
    period = fiscal_periods[n_prior]
    winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
    return winner


def _to_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _extract_pages_text(pdf_bytes: bytes, page_indices: list[int]) -> str:
    if not page_indices:
        return ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        chunks = []
        for i in page_indices:
            if i < len(pdf.pages):
                chunks.append(pdf.pages[i].extract_text() or "")
        return "\n\n".join(chunks)


def extract_area(area: str, text: str, llm_client=None) -> dict:
    client = llm_client or default_llm_client
    prompt = _AREA_PROMPTS[area]
    max_chars = _MAX_CHARS_OVERRIDE.get(area, _MAX_CHARS_PER_AREA)
    return client.chat_json(prompt, text[:max_chars], max_tokens=_MAX_TOKENS)


def _parse_period(period_label: str | None, fallback: datetime) -> str:
    if period_label:
        for fmt in ("%B %d, %Y", "%d.%m.%Y", "%d-%m-%Y", "%B %d %Y"):
            try:
                return datetime.strptime(period_label.strip(), fmt).date().isoformat()
            except ValueError:
                continue
    return fallback.date().isoformat()


def _store_annual_report_document(db: Session, company_id: str, symbol: str, source: str,
                                   storage_key: str, url: str | None, pdf_bytes: bytes) -> None:
    """Durably store the annual report PDF in MinIO — Architecture v2
    Stage 7. Unifies with bse_client.py's filings under one queryable,
    checksummed store instead of this being local-disk-only (already
    durable via nse_client.py's/bse_client.py's own local-disk cache, but
    only on this one machine, with no sha256 or queryable metadata). Never
    raises. `source` is "NSE_ANNUAL_REPORT" or "BSE_ANNUAL_REPORT"."""
    try:
        if db.query(Document).filter_by(storage_key=storage_key).first():
            return
        sha256 = put_document(storage_key, pdf_bytes, content_type="application/pdf")
        if sha256 is None:
            return
        db.add(Document(
            id=str(uuid.uuid4()), company_id=company_id, source=source,
            document_type="ANNUAL_REPORT", url=url,
            sha256=sha256, storage_key=storage_key, file_size=len(pdf_bytes),
            retrieved_at=datetime.now(timezone.utc),
        ))
        db.flush()
    except Exception as e:
        logger.warning("annual_report_ingestion: document storage failed", symbol=symbol, error=str(e))


def _fetch_nse_annual_report(symbol: str) -> tuple[bytes, str, datetime, str, str] | None:
    """Returns (pdf_bytes, storage_key_suffix, broadcast_date, source_url,
    source_document) on success, None if NSE genuinely has nothing on file.
    Raises on a fetch/network failure (caller decides whether to fall back
    to BSE) — distinct from the "nothing on file" case, which is not an
    error and should NOT trigger a BSE fallback attempt for a company NSE
    has simply never listed."""
    session = nse_client._session()
    filing = nse_client.find_latest_annual_report(symbol, session=session)
    if not filing:
        return None
    pdf_bytes = nse_client.download_annual_report(filing, symbol, session=session)

    fallback_date = datetime.now()
    try:
        fallback_date = datetime.strptime(filing.get("broadcast_dttm", ""), "%d-%b-%Y %H:%M:%S")
    except ValueError:
        pass
    storage_key = f"nse/annual_report_{filing.get('fromYr')}_{filing.get('toYr')}.pdf"
    source_document = f"NSE Annual Report FY{filing.get('fromYr')}-{filing.get('toYr')}"
    return pdf_bytes, storage_key, fallback_date, filing["fileName"], source_document


def _fetch_bse_annual_report(symbol: str) -> tuple[bytes, str, datetime, str, str] | None:
    """Same return contract as `_fetch_nse_annual_report()` — BSE as a
    secondary source, tried only when NSE has nothing on file. Real gap
    found 2026-09-16: Pine Labs (a very recently listed company) had zero
    NSE annual-report coverage, but its FY2025-26 report IS on BSE
    (confirmed live, scrip 544606) — BSE's listing requirements evidently
    moved faster for this IPO than NSE's. See `bse_client.py`'s own
    `find_latest_annual_report()` docstring for the endpoint."""
    scrip_code = bse_client.resolve_scrip_code(symbol)
    if not scrip_code:
        return None
    filing = bse_client.find_latest_annual_report(scrip_code)
    if not filing:
        return None
    pdf_bytes = bse_client.download_annual_report(filing, symbol)

    year = filing.get("Year", "unknown")
    fallback_date = datetime.now()
    try:
        # BSE's Annual Report rows carry no filing-date field of their own
        # (only the fiscal Year) — approximate with the fiscal year-end.
        fallback_date = datetime.strptime(f"31-Mar-{year}", "%d-%b-%Y")
    except ValueError:
        pass
    storage_key = f"bse/annual_report_{year}.pdf"
    source_document = f"BSE Annual Report FY{year}"
    return pdf_bytes, storage_key, fallback_date, filing["PDFDownload"], source_document


def ingest_annual_report(db: Session, company_id: str, symbol: str) -> list:
    """Fetch (or reuse the cached copy of) a company's latest annual
    report — NSE primary, BSE as a secondary source when NSE genuinely has
    nothing on file (see `_fetch_bse_annual_report()`'s own docstring for
    why this matters: NSE and BSE's listing/filing timelines can diverge
    for a recently-listed company) — locate the relevant disclosure pages,
    extract what's extractable per area, store every value with
    provenance. Runs for any sector — the bank-only areas (asset_quality/
    funding/capital) simply find no matching pages and are skipped for
    non-bank companies (see `annual_report_locator.py`'s per-area keyword
    terms). Never raises for "nothing found anywhere" or "unreachable" —
    logs and returns an empty list, matching every other ingestion path's
    graceful-degradation contract."""
    inserted = []
    fetched = None
    source = None
    try:
        fetched = _fetch_nse_annual_report(symbol)
        source = "NSE_ANNUAL_REPORT"
    except Exception as e:
        logger.warning("annual_report_ingestion: NSE fetch failed, trying BSE", symbol=symbol, error=str(e))

    if fetched is None:
        try:
            fetched = _fetch_bse_annual_report(symbol)
            source = "BSE_ANNUAL_REPORT"
        except Exception as e:
            logger.warning("annual_report_ingestion: BSE fetch also failed", symbol=symbol, error=str(e))

    if fetched is None:
        logger.info("annual_report_ingestion: no annual report found on NSE or BSE", symbol=symbol)
        return inserted

    pdf_bytes, storage_key_suffix, fallback_date, source_url, source_document = fetched
    storage_key = f"{company_id}/{storage_key_suffix}"

    _store_annual_report_document(db, company_id, symbol, source, storage_key, source_url, pdf_bytes)

    try:
        sections, area_statement_types = locate_sections(pdf_bytes)
    except Exception as e:
        logger.warning("annual_report_ingestion: locator failed", symbol=symbol, error=str(e))
        return inserted

    for area, metric_fields in _AREA_METRIC_FIELDS.items():
        # Per-area, not a blanket assumption — see locate_sections()'s own
        # docstring for the real bug this fixes (every insert here used to
        # rely on metric_store's bare "STANDALONE" default regardless of
        # which statement type the selected pages actually came from).
        statement_type = area_statement_types.get(area, "STANDALONE")
        try:
            page_indices = sections.get(area, [])
            if not page_indices:
                continue
            text = _extract_pages_text(pdf_bytes, page_indices)
            if not text:
                continue
            extracted = extract_area(area, text)
            # Real bug caught live 2026-09-20: `default_llm_client` already
            # exposes `last_used_fallback` (module docstring: "Callers
            # should treat a fallback-served answer as lower-confidence
            # than a primary one") specifically because the local Ollama
            # fallback model's failure mode is silent digit transposition,
            # not an honest null — confirmed reproducing exactly that on a
            # real extraction (12,539.33 → 12,349.33) the very first time
            # Groq's rate limit forced a fallback mid-run. This attribute
            # was never checked here before, so every area in this file
            # (not just the new Chemicals ones) could silently persist a
            # fallback-served value tagged confidence="HIGH"/REPORTED —
            # the exact "occasionally-wrong AVAILABLE" failure mode the ppe
            # area's own docstring calls worse than a missing value. Skip
            # storage entirely rather than downgrade confidence: a skipped
            # area just retries on the next ingestion run (annual reports
            # don't change), so there's no real cost to waiting for a
            # reliable answer instead of keeping a hedge-quality one.
            if default_llm_client.last_used_fallback:
                logger.warning("annual_report_ingestion: skipping area, fallback LLM served this "
                                "extraction (unreliable, not a primary-model answer)",
                                symbol=symbol, area=area)
                continue
        except Exception as e:
            logger.warning("annual_report_ingestion: extraction failed", symbol=symbol, area=area, error=str(e))
            continue

        period = _parse_period(extracted.get("period_label"), fallback_date)
        got_slippage_ratio = False
        for metric_key, field, unit in metric_fields:
            value = _to_float(extracted.get(field))
            if value is None:
                continue
            row = metric_store.insert_metric_value(
                db,
                company_id=company_id,
                metric_key=metric_key,
                period=period,
                value=value,
                unit=unit,
                statement_type=statement_type,
                source=source,
                source_tier=1,
                reported_or_calculated="REPORTED",
                confidence="HIGH",
                source_url=source_url,
                source_document=source_document,
                source_date=fallback_date,
                raw_reported_value=str(extracted.get(field)),
            )
            if row is not None:
                inserted.append(row)
                if metric_key == "slippage_ratio":
                    got_slippage_ratio = True

        # slippage_ratio is often not disclosed as a ready-made percentage —
        # derive it from the NPA movement schedule's raw figures instead,
        # reusing this same extraction call rather than spending another one.
        if area == "asset_quality" and not got_slippage_ratio:
            fresh = _to_float(extracted.get("fresh_slippages_amount"))
            opening = _to_float(extracted.get("opening_standard_advances"))
            if fresh is not None and opening:
                row = metric_store.insert_metric_value(
                    db,
                    company_id=company_id,
                    metric_key="slippage_ratio",
                    period=period,
                    value=round(fresh / opening * 100, 2),
                    unit="%",
                    statement_type=statement_type,
                    source=source,
                    source_tier=1,
                    reported_or_calculated="CALCULATED",
                    confidence="MEDIUM",
                    calculation_formula="fresh_slippages_amount / opening_standard_advances * 100, "
                                        "from annual-report NPA movement schedule",
                    source_url=source_url,
                    source_document=source_document,
                    source_date=fallback_date,
                )
                if row is not None:
                    inserted.append(row)

    # Chemicals-sector derived ratios (2026-09-20) — computed here, not in
    # ChemicalsSector._compute_special_metric(), because that method has no
    # DB access (only the `metrics`/`financial_data` dicts) and pnl_sales
    # lives in a different ingestion source's ledger rows entirely
    # (pnl_history_client.py, not this function's own LLM extraction).
    # Matches statement_type to whichever type the NUMERATOR actually
    # resolved to (see locate_sections()'s per-area statement_type fix
    # above) rather than assuming both sides share one blanket type — e.g.
    # if raw_material_cost happened to resolve CONSOLIDATED for some
    # report, this divides by CONSOLIDATED pnl_sales, never STANDALONE, so
    # numerator and denominator can't end up silently mismatched scopes.
    _inserted_by_key = {row.metric_key: row for row in inserted}
    _single_input_ratios = {
        "raw_material_cost_pct": "raw_material_cost",
        "energy_cost_pct": "power_fuel_cost",
        "rd_to_revenue_pct": "rd_expenditure_total",
    }
    for ratio_key, numerator_key in _single_input_ratios.items():
        num_row = _inserted_by_key.get(numerator_key)
        if num_row is not None:
            num_value, num_period, num_stype = float(num_row.value), num_row.period, num_row.statement_type
        else:
            # This run's own extraction for `numerator_key` may have been
            # skipped (most commonly: Groq rate-limited during this area,
            # fell back to Ollama, discarded per this module's "never store
            # an unreliable fallback answer" rule) even though an EARLIER
            # run already captured and stored the raw figure. Real gap
            # found live on GNFC (2026-09-22): `raw_material_cost` (3,915
            # Cr) was sitting in the ledger from a prior run, but this run's
            # re-extraction got rate-limited, so `_inserted_by_key` had
            # nothing for it and the ratio was silently skipped — even
            # though every ingredient needed to compute it was already on
            # file. Checking the ledger directly before giving up means one
            # rate-limited run no longer erases a ratio a previous run
            # already had everything for.
            existing = None
            for stype in ("CONSOLIDATED", "STANDALONE"):
                candidate = metric_store.get_latest_period_value(db, company_id, numerator_key, statement_type=stype)
                if candidate is not None and candidate.value is not None:
                    existing = candidate
                    break
            if existing is None:
                continue
            num_value, num_period, num_stype = float(existing.value), existing.period, existing.statement_type

        revenue_row = _latest_fiscal_pnl_value(db, company_id, "pnl_sales", num_stype)
        if revenue_row is None or not revenue_row.value:
            continue
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key=ratio_key, period=num_period,
            value=round(num_value / float(revenue_row.value) * 100, 2), unit="%",
            statement_type=num_stype,
            source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
            calculation_formula=f"{numerator_key} / pnl_sales * 100 (annual-report figure over "
                                 f"Screener P&L revenue, same statement_type)",
            source_url=source_url, source_document=source_document, source_date=fallback_date,
        )
        if row is not None:
            inserted.append(row)

    export_row = _inserted_by_key.get("export_revenue_reported")
    domestic_row = _inserted_by_key.get("domestic_revenue_reported")
    if export_row is not None and domestic_row is not None:
        total = float(export_row.value) + float(domestic_row.value)
        if total > 0:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="export_revenue_pct", period=export_row.period,
                value=round(float(export_row.value) / total * 100, 2), unit="%",
                statement_type=export_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="export_revenue_reported / (export_revenue_reported + "
                                     "domestic_revenue_reported) * 100",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

    # Cement-sector derived ratios (2026-09-20) — same "compute here, not in
    # CementSector._compute_special_metric()" reasoning as the Chemicals
    # ratios above (no DB access in that method; pnl_sales/pnl_operating_profit
    # live in a different ingestion source's ledger rows entirely). Metric
    # keys match CementSector.key_metrics()'s ids exactly
    # (volume_growth_yoy/realisation_per_tonne/ebitda_per_tonne/
    # cost_per_tonne) so ledger_bridge.py's automatic by-name bridge picks
    # them up with zero sector-framework code changes, same mechanism the
    # Chemicals ratios and capacity_utilization (stored directly above,
    # already under that exact metric_key) already rely on.
    production_row = _inserted_by_key.get("cement_production_mmt")
    production_prior_row = _inserted_by_key.get("cement_production_mmt_prior")
    if production_row is not None and production_prior_row is not None and production_prior_row.value:
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="volume_growth_yoy", period=production_row.period,
            value=round((float(production_row.value) - float(production_prior_row.value))
                        / float(production_prior_row.value) * 100, 2), unit="%",
            statement_type=production_row.statement_type,
            source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
            calculation_formula="(cement_production_mmt - cement_production_mmt_prior) / "
                                 "cement_production_mmt_prior * 100, both from the same MD&A table",
            source_url=source_url, source_document=source_document, source_date=fallback_date,
        )
        if row is not None:
            inserted.append(row)

    if production_row is not None and production_row.value:
        revenue_row = _latest_fiscal_pnl_value(db, company_id, "pnl_sales", production_row.statement_type)
        ebitda_row = _latest_fiscal_pnl_value(db, company_id, "pnl_operating_profit", production_row.statement_type)
        realisation = None
        if revenue_row is not None and revenue_row.value:
            # revenue (Rs crore) * 1e7 / (production_mmt * 1e6 tonnes) = revenue*10/production_mmt
            realisation = float(revenue_row.value) * 10 / float(production_row.value)
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="realisation_per_tonne", period=production_row.period,
                value=round(realisation, 2), unit="INR",
                statement_type=production_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="pnl_sales_cr * 10 / cement_production_mmt (Rs crore -> Rs/tonne "
                                     "via 1 crore=1e7, 1 million tonnes=1e6 unit conversion)",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

        ebitda_per_tonne = None
        if ebitda_row is not None and ebitda_row.value:
            ebitda_per_tonne = float(ebitda_row.value) * 10 / float(production_row.value)
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="ebitda_per_tonne", period=production_row.period,
                value=round(ebitda_per_tonne, 2), unit="INR",
                statement_type=production_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="pnl_operating_profit_cr * 10 / cement_production_mmt",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

        if realisation is not None and ebitda_per_tonne is not None:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="cost_per_tonne", period=production_row.period,
                value=round(realisation - ebitda_per_tonne, 2), unit="INR",
                statement_type=production_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="realisation_per_tonne - ebitda_per_tonne (total cost/tonne "
                                     "implied by the Realization - Costs = EBITDA bridge)",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

    # Forest Materials (Paper)-sector derived ratios (2026-09-20) — same
    # "compute here, not in ForestMaterialsSector._compute_special_metric()"
    # reasoning as Cement's block above. Reuses the exact same final
    # metric_key names (capacity_utilization/realisation_per_tonne/
    # ebitda_per_tonne/cost_per_tonne) as CementSector — these are shared,
    # per-tonne-commodity-economics vocabulary, not Cement-specific; a
    # given company can only ever be classified into ONE sector, so there
    # is no cross-company collision risk (metric_store is keyed by
    # company_id already). Uses SALES volume, not production volume, for
    # the per-tonne ratios — revenue realizes on units sold, not produced
    # (a small correction over the Cement block above, which used
    # production_mmt for this; the two are close enough on a steady-state
    # cement business that it wasn't worth revisiting there, but sales and
    # production volumes for a paper company can differ enough — e.g.
    # inventory drawdown/buildup years — that using the more correct
    # figure was worth doing properly here).
    paper_sales_row = _inserted_by_key.get("paper_sales_tonnes")
    paper_production_row = _inserted_by_key.get("paper_production_tonnes")
    paper_capacity_row = _inserted_by_key.get("paper_installed_capacity_tonnes")
    paper_volume_row = paper_sales_row or paper_production_row

    # capacity_utilization_pct wasn't directly reported this run but both
    # production and capacity were extracted — a legitimate CALCULATED
    # fallback (not stored twice: the main loop above only inserts this
    # key when capacity_utilization_pct was DIRECTLY extracted).
    if ("capacity_utilization" not in _inserted_by_key and paper_production_row is not None
            and paper_capacity_row is not None and paper_capacity_row.value):
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="capacity_utilization",
            period=paper_production_row.period,
            value=round(float(paper_production_row.value) / float(paper_capacity_row.value) * 100, 2),
            unit="%", statement_type=paper_production_row.statement_type,
            source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
            calculation_formula="paper_production_tonnes / paper_installed_capacity_tonnes * 100",
            source_url=source_url, source_document=source_document, source_date=fallback_date,
        )
        if row is not None:
            inserted.append(row)

    if paper_volume_row is not None and paper_volume_row.value:
        revenue_row = _latest_fiscal_pnl_value(db, company_id, "pnl_sales", paper_volume_row.statement_type)
        ebitda_row = _latest_fiscal_pnl_value(db, company_id, "pnl_operating_profit", paper_volume_row.statement_type)
        realisation = None
        if revenue_row is not None and revenue_row.value:
            # revenue (Rs crore) * 1e7 / volume (plain tonnes) — unlike
            # Cement's *10 shortcut, paper volume here is already in plain
            # tonnes, not million tonnes, so the full 1e7 multiplier applies.
            realisation = float(revenue_row.value) * 1e7 / float(paper_volume_row.value)
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="realisation_per_tonne", period=paper_volume_row.period,
                value=round(realisation, 2), unit="INR",
                statement_type=paper_volume_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="pnl_sales_cr * 1e7 / paper_sales_tonnes (falls back to "
                                     "paper_production_tonnes if sales volume wasn't disclosed)",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

        ebitda_per_tonne = None
        if ebitda_row is not None and ebitda_row.value:
            ebitda_per_tonne = float(ebitda_row.value) * 1e7 / float(paper_volume_row.value)
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="ebitda_per_tonne", period=paper_volume_row.period,
                value=round(ebitda_per_tonne, 2), unit="INR",
                statement_type=paper_volume_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="pnl_operating_profit_cr * 1e7 / paper_sales_tonnes",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

        if realisation is not None and ebitda_per_tonne is not None:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="cost_per_tonne", period=paper_volume_row.period,
                value=round(realisation - ebitda_per_tonne, 2), unit="INR",
                statement_type=paper_volume_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="realisation_per_tonne - ebitda_per_tonne (total cost/tonne "
                                     "implied by the Realization - Costs = EBITDA bridge)",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

    # Metals & Mining-sector derived ratios (2026-09-20) — same "compute
    # here, not in MetalsSector._compute_special_metric()" reasoning as
    # Cement/Paper above. Uses `production_volume_growth` as the final
    # metric_key (NOT `volume_growth_yoy` — MetalsSector's key_metrics()
    # declares this metric under a different name than CementSector's,
    # confirmed against app/sectors/metals.py before writing this).
    # `ebitda_per_tonne`/`cost_per_tonne` reuse the same shared metric_key
    # names as Cement/Paper (no collision risk — a company belongs to
    # exactly one sector). Prefers a DIRECTLY-reported EBITDA/tonne over
    # the derived pnl_operating_profit/volume figure when both exist —
    # same "trust the company's own number" precedent as
    # capacity_utilization_pct in the Cement/Paper blocks.
    metals_production_row = _inserted_by_key.get("metals_production_mnt")
    metals_production_prior_row = _inserted_by_key.get("metals_production_mnt_prior")
    metals_sales_row = _inserted_by_key.get("metals_sales_mnt")
    metals_ebitda_reported_row = _inserted_by_key.get("metals_ebitda_per_tonne_reported")
    metals_volume_row = metals_sales_row or metals_production_row

    if (metals_production_row is not None and metals_production_prior_row is not None
            and metals_production_prior_row.value):
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="production_volume_growth",
            period=metals_production_row.period,
            value=round((float(metals_production_row.value) - float(metals_production_prior_row.value))
                        / float(metals_production_prior_row.value) * 100, 2), unit="%",
            statement_type=metals_production_row.statement_type,
            source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
            calculation_formula="(metals_production_mnt - metals_production_mnt_prior) / "
                                 "metals_production_mnt_prior * 100, both from the same MD&A disclosure",
            source_url=source_url, source_document=source_document, source_date=fallback_date,
        )
        if row is not None:
            inserted.append(row)

    if metals_ebitda_reported_row is not None and metals_ebitda_reported_row.value is not None:
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="ebitda_per_tonne",
            period=metals_ebitda_reported_row.period, value=float(metals_ebitda_reported_row.value),
            unit="INR", statement_type=metals_ebitda_reported_row.statement_type,
            source=source, source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
            calculation_formula="directly stated in the company's own MD&A narrative — not derived",
            source_url=source_url, source_document=source_document, source_date=fallback_date,
        )
        if row is not None:
            inserted.append(row)

    if metals_volume_row is not None and metals_volume_row.value:
        revenue_row = _latest_fiscal_pnl_value(db, company_id, "pnl_sales", metals_volume_row.statement_type)
        ebitda_row = _latest_fiscal_pnl_value(db, company_id, "pnl_operating_profit", metals_volume_row.statement_type)
        realisation = None
        if revenue_row is not None and revenue_row.value:
            # revenue (Rs crore) * 1e7 / (volume_mnt * 1e6 tonnes) = revenue*10/volume_mnt
            realisation = float(revenue_row.value) * 10 / float(metals_volume_row.value)
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="realisation_per_tonne",
                period=metals_volume_row.period, value=round(realisation, 2), unit="INR",
                statement_type=metals_volume_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="pnl_sales_cr * 10 / metals_sales_mnt (falls back to "
                                     "metals_production_mnt if sales volume wasn't disclosed)",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

        # Only derive ebitda_per_tonne if the company DIDN'T already give a
        # direct figure above — never overwrite a REPORTED value with a
        # lower-confidence CALCULATED one for the same period.
        ebitda_per_tonne = float(metals_ebitda_reported_row.value) if (
            metals_ebitda_reported_row is not None and metals_ebitda_reported_row.value is not None) else None
        if ebitda_per_tonne is None and ebitda_row is not None and ebitda_row.value:
            ebitda_per_tonne = float(ebitda_row.value) * 10 / float(metals_volume_row.value)
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="ebitda_per_tonne",
                period=metals_volume_row.period, value=round(ebitda_per_tonne, 2), unit="INR",
                statement_type=metals_volume_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="pnl_operating_profit_cr * 10 / metals_sales_mnt",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

        if realisation is not None and ebitda_per_tonne is not None:
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key="cost_per_tonne",
                period=metals_volume_row.period, value=round(realisation - ebitda_per_tonne, 2), unit="INR",
                statement_type=metals_volume_row.statement_type,
                source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                calculation_formula="realisation_per_tonne - ebitda_per_tonne (total cost/tonne "
                                     "implied by the Realization - Costs = EBITDA bridge)",
                source_url=source_url, source_document=source_document, source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

    # Automobile (OEM)-sector derived ratios (2026-09-20) — same "compute
    # here, not in AutomobileSector._compute_special_metric()" reasoning as
    # the other sector ratio blocks above. `market_share`/`dealer_inventory_
    # days` need no computation — stored directly by the main loop above
    # under the exact metric_key names AutomobileSector.key_metrics()
    # expects. `volume_growth_yoy` uses the same-report current+prior-year
    # units (like Cement); `asp_growth` additionally needs the PRIOR
    # fiscal year's pnl_sales — via `_latest_fiscal_pnl_value(...,
    # n_prior=1)`, not date arithmetic on the (possibly fallback-derived,
    # non-fiscal-year-end) resolved period.
    auto_units_row = _inserted_by_key.get("automobile_units_sold")
    auto_units_prior_row = _inserted_by_key.get("automobile_units_sold_prior")

    if auto_units_row is not None and auto_units_prior_row is not None and auto_units_prior_row.value:
        row = metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="volume_growth_yoy", period=auto_units_row.period,
            value=round((float(auto_units_row.value) - float(auto_units_prior_row.value))
                        / float(auto_units_prior_row.value) * 100, 2), unit="%",
            statement_type=auto_units_row.statement_type,
            source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
            calculation_formula="(automobile_units_sold - automobile_units_sold_prior) / "
                                 "automobile_units_sold_prior * 100, both from the same MD&A disclosure",
            source_url=source_url, source_document=source_document, source_date=fallback_date,
        )
        if row is not None:
            inserted.append(row)

        current_revenue_row = _latest_fiscal_pnl_value(db, company_id, "pnl_sales", auto_units_row.statement_type, n_prior=0)
        prior_revenue_row = _latest_fiscal_pnl_value(db, company_id, "pnl_sales", auto_units_row.statement_type, n_prior=1)
        if (current_revenue_row is not None and current_revenue_row.value
                and prior_revenue_row is not None and prior_revenue_row.value):
            current_asp = float(current_revenue_row.value) * 1e7 / float(auto_units_row.value)
            prior_asp = float(prior_revenue_row.value) * 1e7 / float(auto_units_prior_row.value)
            if prior_asp:
                row = metric_store.insert_metric_value(
                    db, company_id=company_id, metric_key="asp_growth", period=auto_units_row.period,
                    value=round((current_asp - prior_asp) / prior_asp * 100, 2), unit="%",
                    statement_type=auto_units_row.statement_type,
                    source=source, source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
                    calculation_formula="ASP = pnl_sales_cr * 1e7 / automobile_units_sold, for the "
                                         "current and immediately-preceding fiscal year each "
                                         "(pnl_sales at n_prior=0 and n_prior=1); "
                                         "asp_growth = (ASP_current - ASP_prior) / ASP_prior * 100",
                    source_url=source_url, source_document=source_document, source_date=fallback_date,
                )
                if row is not None:
                    inserted.append(row)

    return inserted


def _bank_stocks(db: Session):
    """Active stocks that resolve to the Banks sector framework — same
    resolution the pipeline itself uses (app/sectors/registry.py), not a
    separate ad-hoc text filter, so this never drifts from what
    orchestrator.py actually treats as a bank."""
    from app.infrastructure.database.models import Stock
    from app.sectors.registry import get_framework

    candidates = (
        db.query(Stock)
        .filter(Stock.is_active == True, Stock.industry.ilike("%bank%"))
        .all()
    )
    return [
        s for s in candidates
        if get_framework(s.sector or "", industry=s.industry, basic_industry=s.basic_industry).sector_name == "Banks"
    ]


def ingest_all_banks_annual_reports(db: Session, max_companies_per_run: int = 5) -> dict:
    """Batch driver for "all banks" — bounded and resumable, not a single
    unbounded run. Skips any bank already covered within the last ~300 days
    (the same Redis gate key orchestrator.py's inline call uses, so a bank
    processed here won't be redundantly re-processed by a later analysis
    run, and vice versa). Meant to be invoked repeatedly (daily cron, or
    manually) until the whole banking universe is covered — one unbounded
    run would blow through the Groq account's daily token quota on the
    first handful of companies (observed today: a 200,000/day cap).
    """
    processed, skipped, failed = [], [], []
    for stock in _bank_stocks(db):
        if len(processed) >= max_companies_per_run:
            break
        gate_key = f"banking_annual_report:{stock.id}"
        if cache_get(gate_key):
            skipped.append(stock.id)
            continue
        try:
            rows = ingest_annual_report(db, company_id=stock.id, symbol=stock.symbol)
            db.commit()
            processed.append({"company_id": stock.id, "values_inserted": len(rows)})
        except Exception as e:
            db.rollback()
            logger.warning("ingest_all_banks_annual_reports: company failed", stock_id=stock.id, error=str(e))
            failed.append(stock.id)
        cache_set(gate_key, "1", _BATCH_GATE_TTL)

    logger.info("ingest_all_banks_annual_reports: run complete",
                processed=len(processed), skipped=len(skipped), failed=len(failed))
    return {"processed": processed, "skipped": skipped, "failed": failed}
