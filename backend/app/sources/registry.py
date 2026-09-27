"""Source status registry — Architecture v2 Stage 6 (reframed 2026-09-12).

Stage 6 was originally scoped as "build RBI/SEBI/MCA ingestion adapters."
Live probing found all three genuinely blocked right now:
  - RBI: 403 on the main site to a plain request; dbie.rbi.org.in currently
    has a broken/mismatched SSL certificate. Not retried with a cookie-
    bootstrap session (the fix that worked for NSE) — worth trying before
    assuming this is permanent.
  - SEBI: the orders search page loads fine (GET), but submitting an actual
    search (POST) trips a WAF — "Unauthorized Activity Has Been Detected."
    Likely needs real browser automation to have any chance; deliberately
    not attempted now (not worth the engineering time on an uncertain
    payoff per this decision).
  - MCA: 403 on the company-lookup endpoint; the real public lookup is
    CAPTCHA-gated. Deliberately not pursued — bypassing a CAPTCHA is a
    government portal's explicit anti-automation control, not a technical
    inconvenience to route around.

Rather than silently pretend these sources don't exist, or keep retrying
against walls that won't move, this registry records what's actually
reachable right now so any caller (a route, an MCP tool, or a future
session picking this up) can check before assuming a source works — a
blocked source should read BLOCKED, never silently return nothing with no
explanation. Not a live health-check system: status is a manually-verified
snapshot (`verified_at`), refreshed by hand when a source is re-probed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

_VALID_STATUSES = {"ACTIVE", "PARTIAL", "BLOCKED", "RESTRICTED"}
_VALID_TYPES = {"exchange", "regulator", "aggregator", "primary_document", "calculated", "manual"}


@dataclass(frozen=True)
class SourceDefinition:
    id: str
    type: str
    tier: int  # matches metric_store.py's source_tier convention: 1 = highest authority
    status: str  # ACTIVE | PARTIAL | BLOCKED | RESTRICTED
    notes: str
    verified_at: str  # ISO date of the last live check this status is based on

    def __post_init__(self):
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}' for source '{self.id}'")
        if self.type not in _VALID_TYPES:
            raise ValueError(f"Invalid type '{self.type}' for source '{self.id}'")


SOURCE_REGISTRY: dict[str, SourceDefinition] = {
    "RBI": SourceDefinition(
        id="RBI", type="regulator", tier=1, status="BLOCKED",
        notes=("Main site 403s a plain request; dbie.rbi.org.in has a broken/mismatched "
               "SSL certificate right now. Not retried with a cookie-bootstrap session "
               "(the NSE-style fix) — untested whether that would help here too."),
        verified_at="2026-09-12",
    ),
    "SEBI": SourceDefinition(
        id="SEBI", type="regulator", tier=1, status="BLOCKED",
        notes=("Orders search page loads (GET), but a search submission (POST) trips a "
               "WAF: 'Unauthorized Activity Has Been Detected'. Would likely need real "
               "browser automation (Playwright) to have any chance — deliberately not "
               "attempted, per the decision not to sink engineering time into an "
               "uncertain-payoff WAF fight right now."),
        verified_at="2026-09-12",
    ),
    "MCA": SourceDefinition(
        id="MCA", type="regulator", tier=1, status="RESTRICTED",
        notes=("Company-lookup endpoint 403s directly; the real public lookup is "
               "CAPTCHA-gated. Deliberately not pursued — bypassing a CAPTCHA is a "
               "government portal's explicit anti-automation control, not a technical "
               "inconvenience to route around."),
        verified_at="2026-09-12",
    ),
    "NSE_XBRL": SourceDefinition(
        id="NSE_XBRL", type="exchange", tier=1, status="PARTIAL",
        notes="Documented but unverified from this environment — NSE has historically blocked datacenter IPs on some endpoints even while others (annual reports, shareholding pattern) work fine.",
        verified_at="2026-09-06",
    ),
    "NSE_ANNUAL_REPORT": SourceDefinition(
        id="NSE_ANNUAL_REPORT", type="exchange", tier=1, status="ACTIVE",
        notes="Reachable via a cookie-bootstrap session (app/ingestion/nse_client.py). Historically flaky — was hard-blocked earlier in this project, then found reachable — treat as flaky-but-live, not guaranteed permanent.",
        verified_at="2026-09-11",
    ),
    "NSE_SHAREHOLDING": SourceDefinition(
        id="NSE_SHAREHOLDING", type="exchange", tier=1, status="ACTIVE",
        notes="corporate-share-holdings-master API + linked per-quarter XBRL filings, confirmed live (app/ingestion/shareholding_client.py).",
        verified_at="2026-09-11",
    ),
    "BSE_RESULTS_API": SourceDefinition(
        id="BSE_RESULTS_API", type="exchange", tier=1, status="ACTIVE",
        notes="Structured TabResults_PAR/w snapshot, in active use (app/ingestion/banking_ingestion.py).",
        verified_at="2026-09-06",
    ),
    "BSE_FILING_OCR": SourceDefinition(
        id="BSE_FILING_OCR", type="exchange", tier=1, status="ACTIVE",
        notes="Scanned SEBI-format quarterly filings, Tesseract OCR + LLM extraction, in active use.",
        verified_at="2026-09-06",
    ),
    "BSE_EARNINGS_CALL": SourceDefinition(
        id="BSE_EARNINGS_CALL", type="exchange", tier=1, status="ACTIVE",
        notes=("Earnings-call/press-conference transcripts filed on BSE as a Regulation 30 "
               "disclosure, alongside (not part of) the standard financial-results filing. "
               "Real text layer (no OCR) — confirmed live on Infosys's Q1 FY27 transcript: "
               "exact attrition/headcount/TCV/DSO figures stated in prepared remarks. "
               "Sector-agnostic adapter (any company can file one), though the extraction "
               "schema built so far only covers IT-services operational KPIs "
               "(app/ingestion/earnings_call_client.py) — other sectors can add their own "
               "extraction schema against the same adapter later."),
        verified_at="2026-09-12",
    ),
    "SCREENER": SourceDefinition(
        id="SCREENER", type="aggregator", tier=2, status="ACTIVE",
        notes="Third-party aggregator via openscreener/Playwright, in active use across balance sheet, quarterly metrics, classification, and historical-valuation ingestion.",
        verified_at="2026-09-11",
    ),
    "COMPANY_IR": SourceDefinition(
        id="COMPANY_IR", type="primary_document", tier=1, status="PARTIAL",
        notes="Valid source category in metric_store.py's schema; no dedicated ingestion adapter built yet.",
        verified_at="2026-09-06",
    ),
    "MONEYCONTROL": SourceDefinition(
        id="MONEYCONTROL", type="aggregator", tier=2, status="PARTIAL",
        notes="Valid source category in metric_store.py's schema; no ingestion adapter built yet.",
        verified_at="2026-09-06",
    ),
    "CALCULATED": SourceDefinition(
        id="CALCULATED", type="calculated", tier=2, status="ACTIVE",
        notes="Derived in Python from other already-ingested figures (e.g. cost_to_income_ratio, credit_cost) — not an external source at all.",
        verified_at="2026-09-06",
    ),
    "MANUAL": SourceDefinition(
        id="MANUAL", type="manual", tier=1, status="ACTIVE",
        notes="Human-entered correction/override via POST /api/banking/{company_id}/metrics.",
        verified_at="2026-09-06",
    ),
    "YAHOO_FINANCE": SourceDefinition(
        id="YAHOO_FINANCE", type="aggregator", tier=2, status="ACTIVE",
        notes=("Extended fundamental data beyond the core statements already used — "
               "analyst targets/ratings (own separate row from IndMoney's, never "
               "blended), forward EPS/revenue estimates, insider transactions, "
               "corporate actions, news, earnings calendar, governance risk scores "
               "(app/ingestion/yfinance_extended_client.py). Unlike analyst_consensus's "
               "IndMoney row, this is fully autonomous — the backend calls yfinance "
               "directly, no agent-fetch step needed. tier=2: third-party aggregator, "
               "same tier as Screener.in, not a primary regulatory/exchange source."),
        verified_at="2026-09-13",
    ),
    "INDMONEY": SourceDefinition(
        id="INDMONEY", type="manual", tier=3, status="ACTIVE",
        notes=("Third-party analyst consensus (sentiment, target price), stored in the "
               "separate analyst_consensus table, never blended into fa_metric_data_points "
               "or this platform's own scoring — see migration 0012's docstring. Reachable "
               "only via an MCP connector inside a Claude session, not a public HTTP API — "
               "so unlike every other source here, ingestion is agent-fetched-then-POSTed, "
               "not an autonomous backend batch job. tier=3 reflects that this is opinion, "
               "not a fact being cross-validated against other sources."),
        verified_at="2026-09-12",
    ),
}


def list_sources() -> list[dict]:
    return [asdict(s) for s in SOURCE_REGISTRY.values()]


def get_source(source_id: str) -> SourceDefinition | None:
    return SOURCE_REGISTRY.get(source_id)
