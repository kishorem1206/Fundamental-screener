"""Sector measures and management outlook, read from what the company itself
files with the exchange: investor presentations, results press releases and
earnings-call transcripts.

These are the operating figures the financial statements do not carry — order
book, store count, beds and occupancy, seat capacity, volumes, revenue per
user. Each is a COMPANY_CLAIM: the company's own statement, quoted with its
page, not an audited figure. The reader is deliberately narrow: a measure is
taken only where the wording and a plausible number sit together on the page,
and a filing that does not state a measure in a recognised form yields nothing.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.bie.annual_report_extract import page_texts
from app.bie.documents import archive, content_of
from app.bie.evidence import clear_document_facts, quote_on_page, record_fact
from app.infrastructure.database.models import BieFact, Document, Stock

_N = r"(-?\d[\d,]*(?:\.\d+)?)"
_RUPEE = r"(?:₹|`|Rs\.?|INR)\s*"
_SCALE = r"(lakh\s+crores?|lakh\s+cr\b|crores?|cr\b|billion|bn\b|trillion|million|mn\b)"
_TO_CRORE = {"lakh crore": 1e5, "lakh cr": 1e5, "crore": 1.0, "cr": 1.0, "billion": 100.0, "bn": 100.0, "trillion": 1e5, "million": 0.1, "mn": 0.1}
# How a stated scale converts to the unit a measure is stored in.
_SCALES = {"INR crore": _TO_CRORE, "GW": {"gw": 1.0, "mw": 0.001}, "USD billion": {"billion": 1.0, "bn": 1.0, "million": 0.001, "mn": 0.001}}
_USD = r"(?:US\s*\$|USD|\$)\s*"
_WINDOW = timedelta(days=240)
MAX_FILINGS = 7

# (group, pattern on sector + basic industry, measures). A measure is (key, label, unit, lowest, highest, patterns);
# a pattern's first group is the number and an optional second group its scale.
GROUPS = (
    ("Stores", r"retail|restaurant|e-retail", (
        ("stores", "Stores", "count", 5, 200000, (rf"(?:total\s+)?(?:store|outlet|restaurant)\s+count\s+(?:to|of|at|stood\s+at|is)\s+{_N}", rf"{_N}\s+(?:stores|outlets|restaurants)\s+as\s+(?:on|of|at)",
                                                  rf"(?:network|total)\s+of\s+{_N}\s+(?:stores|outlets|restaurants)", rf"operat(?:es|ing|ed)\s+{_N}\s+(?:stores|outlets|restaurants)")),
        ("stores_added", "Stores added in the period", "count", 1, 5000, (rf"(?:added|opened)\s+{_N}\s+(?:new\s+)?(?:stores|outlets|restaurants)", rf"{_N}\s+(?:new\s+)?(?:stores|outlets|restaurants)\s+(?:were\s+)?(?:added|opened)")),
        ("like_for_like_growth", "Like-for-like sales growth", "%", -60, 100, (rf"(?:like[- ]for[- ]like|\bLFL\b|same[- ]stores?\s+sales?)[^.\n%]{{0,70}}?{_N}\s*%",)),
        ("retail_area", "Retail area", "million sq ft", 0.05, 500, (rf"retail\s+(?:business\s+)?area[^.\n\d]{{0,50}}{_N}\s*(?:million|mn)\s*sq",)),
    )),
    ("Cement", r"cement", (
        ("sales_volume", "Sales volume", "million tonnes", 0.1, 500, (rf"(?:sales|cement|grey\s+cement)\s+volumes?\*?[^\n\d]{{0,45}}{_N}\s*(?:mnt\b|mt\b|million\s+(?:tonnes|tons|mt))", rf"sales\s+volumes?\*?\s+{_N}\b")),
        ("capacity", "Capacity", "million tonnes a year", 0.5, 1000, (rf"capacity[^\n\d]{{0,60}}{_N}\s*(?:mtpa|mnt\b|million\s+tonnes)",)),
        ("ebitda_per_tonne", "EBITDA per tonne", "INR", 100, 5000, (rf"EBITDA\s*(?:/|per)\s*(?:mt|t(?:onne)?)\b[^\n\d]{{0,30}}{_RUPEE}?{_N}",)),
    )),
    ("Steel", r"iron|steel|alumin|zinc|copper|metal", (
        ("production", "Crude steel or metal production", "million tonnes", 0.05, 200, (rf"(?:crude\s+steel|metal|aluminium|zinc)\s+production[^\n\d]{{0,60}}{_N}\s*(?:mn\b|million|mt\b)",)),
        ("deliveries", "Deliveries or sales volume", "million tonnes", 0.05, 200, (rf"(?:deliveries|sales\s+volumes?)[^\n\d]{{0,60}}{_N}\s*(?:mn\b|million|mt\b)",)),
    )),
    ("Vehicles", r"passenger cars|2/3 wheelers|commercial vehicles|tractor", (
        ("units_sold", "Units sold in the period", "units", 500, 5e7, (rf"total\s+(?:sales|volumes?|dispatches)[^\n\d]{{0,50}}{_N}\s+(?:units|vehicles)", rf"sold\s+(?:a\s+total\s+of\s+)?{_N}\s+(?:units|vehicles)",
                                                                       rf"(?m)^\s*(?:grand\s+)?total(?:\s+sales)?\s*(?:\([^)\n]*\))?\s+{_N}\b")),
    )),
    ("Hospitals", r"hospital|healthcare service", (
        ("beds", "Beds", "count", 100, 200000, (rf"(?:operating|operational|census|total|capacity)\s+beds\s*:?\s*{_N}", rf"\bbeds\s+{_N}\b")),
        ("occupancy", "Occupancy", "%", 20, 100, (rf"occupancy[^\n\d]{{0,35}}{_N}\s*%",)),
        ("arpob", "Revenue per occupied bed per day", "INR", 5000, 300000, (rf"ARPOB[^\n\d]{{0,45}}{_RUPEE}?{_N}",)),
    )),
    ("Airlines", r"airline", (
        ("load_factor", "Passenger load factor", "%", 40, 100, (rf"load\s+factor[^\n\d]{{0,45}}{_N}\s*%",)),
        ("capacity_ask", "Capacity (available seat-km)", "billion", 0.5, 2000, (rf"\bASKs?\b\*?\s*\(\s*(?:billion|bn)\s*\)\s*{_N}", rf"capacity[^\n\d]{{0,40}}{_N}\s*billion\s+ASK")),
        ("rask", "Revenue per seat-km", "INR", 1, 20, (rf"\bRASK\b\*?\s*\(\s*(?:INR|Rs\.?|₹)\s*\)\s*{_N}",)),
        ("cask", "Cost per seat-km", "INR", 1, 20, (rf"\bCASK\b\*?\s*\(\s*(?:INR|Rs\.?|₹)\s*\)\s*{_N}",)),
        ("fleet", "Aircraft in fleet", "count", 5, 3000, (rf"fleet\s+(?:of|size)[^\n\d]{{0,30}}{_N}\s+aircraft", rf"{_N}\s+aircraft\s+(?:as\s+(?:on|of|at)|in\s+(?:the\s+)?fleet)")),
    )),
    ("Telecom", r"telecom", (
        ("arpu", "Average revenue per user per month", "INR", 30, 2000, (rf"\bARPU\b[^\n\d]{{0,70}}{_RUPEE}{_N}",)),
        ("customers", "Customers", "million", 0.5, 3000, (rf"(?:customer|subscriber)\s+base[^\n\d]{{0,70}}{_N}\s*(?:million|mn\b)",)),
    )),
    ("Power", r"power|electric utilit", (
        ("capacity", "Capacity in operation", "GW", 0.05, 600, (rf"(?:operational|installed|commercial|operating)\s+capacity[^\n\d,;]{{0,30}}{_N}\s*(GW|MW)\b", rf"under\s+operation\s*[-–:]?\s*{_N}\s*(GW|MW)\b")),
        ("under_construction", "Capacity under construction", "GW", 0.05, 600, (rf"{_N}\s*(GW|MW)\s+under\s+construction",)),
        ("plant_load_factor", "Plant load factor", "%", 20, 100, (rf"(?:\bPLF\b|plant\s+load\s+factor)[^\n\d]{{0,45}}{_N}\s*%",)),
        ("generation", "Generation", "billion units", 0.5, 2000, (rf"generation[^\n\d]{{0,45}}{_N}\s*(?:BU\b|billion\s+units)",)),
    )),
    ("IT services", r"information technology|computers - software|it enabled", (
        ("deal_wins", "Deal wins (total contract value)", "USD billion", 0.01, 100, (rf"(?:\bTCV\b|total\s+contract\s+value|deal\s+wins?|order\s+book)[^\n\d$]{{0,70}}{_USD}{_N}\s*(billion|bn\b|million|mn\b)",)),
        ("headcount", "Employees", "count", 1000, 2e6, (rf"(?:headcount|workforce\s+strength|total\s+(?:employees|headcount)|employee\s+strength)[^\n\d]{{0,50}}{_N}",)),
        ("attrition", "Attrition", "%", 2, 50, (rf"attrition[^\n\d]{{0,70}}{_N}\s*%",)),
    )),
    ("Pharma", r"pharmaceutical|biotech", (
        ("rd_share", "R&D spend as a share of sales", "%", 0.5, 40, (rf"R&D\s+(?:investment|spend|expenses?|expenditure)\s*(?:at|of|:)?\s*{_N}\s*%\s+of\s+(?:net\s+)?(?:sales|revenue)",)),
        ("andas_filed", "US generic applications filed to date", "count", 5, 5000, (rf"{_N}\s+ANDAs?[^\n]{{0,40}}\bfiled\b",)),
        ("andas_pending", "US generic applications awaiting approval", "count", 1, 2000, (rf"{_N}\s+ANDAs?[^\n]{{0,70}}\bpending\b",)),
    )),
    ("Real estate", r"realty|residential|commercial projects|real estate", (
        ("sales_bookings", "Sales bookings", "INR crore", 10, 2e5, (rf"(?:new\s+)?(?:sales\s+bookings?|pre-?sales|booking\s+value)[^\n\d]{{0,60}}{_RUPEE}{_N}\s*{_SCALE}",)),
        ("collections", "Collections", "INR crore", 10, 2e5, (rf"collections?[^\n\d]{{0,50}}{_RUPEE}{_N}\s*{_SCALE}",)),
        ("net_debt", "Net debt", "INR crore", 1, 5e5, (rf"net\s+debt\s*[-–:]?\s*{_RUPEE}{_N}\s*{_SCALE}",)),
        ("rental_portfolio", "Rental portfolio", "million sq ft", 0.1, 500, (rf"{_N}\s*msf\s+(?:of\s+)?(?:rental|operational|annuity)",)),
    )),
    ("Consumer goods", r"fast moving consumer goods|fmcg|personal care|packaged foods|household products", (
        ("volume_growth", "Underlying volume growth", "%", -20, 40, (rf"(?:underlying\s+volume\s+growth|\bUVG\b)\s*(?:\(UVG\))?\s*(?:of|at|was|stood\s+at|:)\s*{_N}\s*%", rf"volume\s+growth\s+of\s+{_N}\s*%")),
    )),
    ("Non-bank lenders", r"non banking financial|nbfc|housing finance|microfinance|financial institution", (
        ("assets_under_management", "Assets under management", "INR crore", 1000, 5e6, (rf"\bAUM\b(?!\s+(?:addition|growth\s+of|crossed))[^₹`]{{0,45}}?{_RUPEE}{_N}\s*{_SCALE}",)),
        ("gross_bad_loans", "Gross bad loans", "%", 0.01, 30, (rf"\bGNPA\b[^\n\d]{{0,45}}{_N}\s*%",)),
        ("net_bad_loans", "Net bad loans", "%", 0.01, 20, (rf"\bGNPA\s*(?:and|&)\s*NNPA\b[^\n\d]{{0,45}}[\d.]+\s*%\s*(?:and|&)\s*{_N}\s*%", rf"\bNNPA\b(?!\s*(?:and|&))[^\n\d]{{0,45}}{_N}\s*%")),
        ("cost_of_funds", "Cost of funds", "%", 2, 20, (rf"cost\s+of\s+funds[^\n\d]{{0,30}}{_N}\s*%",)),
        ("customers", "Customers", "million", 0.05, 2000, (rf"customer\s+franchise[^\n\d]{{0,30}}{_N}\s*(?:MM\b|million|mn\b)",)),
    )),
    ("Asset managers", r"asset management", (
        ("assets_managed", "Quarterly average assets managed", "INR crore", 100, 2e7, (rf"\bQAAUM\s+of\s+{_RUPEE}{_N}\s*{_SCALE}",)),
        ("market_share", "Share of industry assets", "%", 0.05, 60, (rf"\bQAAUM\s+market\s+share\s+of\s+{_N}\s*%",)),
    )),
    ("Order book", r"capital goods|civil construction|aerospace|defen[cs]e|heavy electrical|engineering|shipbuilding|railway|water supply", (
        ("order_book", "Order book", "INR crore", 50, 2e6, (rf"order\s*book[^.\n]{{0,110}}?{_RUPEE}{_N}\s*{_SCALE}", rf"order\s+backlog[^.\n]{{0,110}}?{_RUPEE}{_N}\s*{_SCALE}")),
        ("order_inflow", "Order inflow", "INR crore", 10, 2e6, (rf"order\s+(?:inflows?|intake|booking)[^.\n]{{0,110}}?{_RUPEE}{_N}\s*{_SCALE}",)),
    )),
)
# Measures any kind of company may state. They are read for every company, alongside its sector's own, so that a sector
# with no patterns of its own (consumer durables, chemicals, media …) still shows what the company says about itself.
GENERAL = (
    ("market_share", "Market share", "%", 0.1, 100, (rf"{_N}\s*%\s+(?:secondary\s+|primary\s+|YTD\s+|value\s+|volume\s+|overall\s+)*market\s+share(?:\s+(?:in|for|of)\s+[^.\n,;]{{3,42}})?",
                                                     rf"market\s+share\s+(?:of|at|to|was|stood\s+at)\s+(?:about\s+|around\s+|~\s*|c\.\s*)?{_N}\s*%")),
    ("volume_growth", "Volume growth", "%", -60, 300, (rf"volumes?\s+(?:grew|growth\s+of|growth\s+at|increased|rose|were\s+up|up)\s+(?:by\s+)?{_N}\s*%",
                                                       rf"{_N}\s*%\s+(?:YoY\s+|year[- ]on[- ]year\s+)?volume\s+growth")),
    ("order_book", "Order book", "INR crore", 50, 2e6, (rf"order\s*book[^.\n]{{0,110}}?{_RUPEE}{_N}\s*{_SCALE}",)),
    ("network", "Sales and service network", "points", 20, 5e6, (rf"(?:over|more\s+than|about|around|~)\s*{_N}\+?\s+(?:touch\s?points|outlets|stores|dealers|distributors|branches|service\s+cent(?:re|er)s)",)),
    ("capacity_utilisation", "Capacity utilisation", "%", 10, 130, (rf"capacity\s+utili[sz]ation[^\n\d%]{{0,45}}{_N}\s*%",)),
)
# A figure introduced by one of these words is the earlier or the compared-against number, not the current one.
_PRIOR = re.compile(r"\b(?:from|versus|vs\.?|against|compared\s+(?:to|with)|up\s+from|down\s+from)\s*(?:₹|`|Rs\.?|INR|US\s*\$|\$)?\s*~?\s*$", re.I)
_KINDS = (("presentation", r"presentation"), ("press release", r"press\s+release|media\s+release"), ("transcript", r"transcript"),
          ("results filing", r"outcome\s+of\s+board\s+meeting.*financial\s+results"))
_PER_KIND = {"presentation": 2, "press release": 3, "transcript": 1, "results filing": 1}
# A transcript mixes management's statements with analysts' questions: only measures stated as a level in rupees are taken from one.
_FROM_TRANSCRIPT = {"order_book", "order_inflow"}
_RESULTS = re.compile(r"result|financial|quarter|performance|earnings|sales|production|business\s+update|volumes?|deliveries", re.I)
_OUTLOOK = re.compile(r"\b(?:guidance|we\s+(?:expect|are\s+targeting|aim|intend|plan)\s+to|target(?:ing)?\s+(?:of|to)|outlook\s+for|we\s+should\s+be\s+(?:able\s+to|at))\b", re.I)
_FIGURE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|per\s*cent|crores?|\bcr\b|billion|million|\bbps\b|x\b)|FY\s?\d{2}", re.I)


# Measures that are a level at a date; the rest are a flow over a period.
_LEVELS = {"market_share", "network", "order_book", "stores", "retail_area", "capacity", "under_construction", "beds", "fleet", "customers", "headcount", "andas_filed",
           "andas_pending", "net_debt", "rental_portfolio", "assets_under_management", "gross_bad_loans", "net_bad_loans"}
_DATE = r"(\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+,?\s+\d{4}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})"
_CUES = (
    ("quarter", r"\bQ[1-4]\s*'?\s*FY\s*'?\d{2,4}\b|\bQ[1-4]\b|quarter\s+ended[^.\n]{0,30}|(?:for|during|in)\s+the\s+quarter|\bquarterly\b|\bQE\b"),
    ("half year", r"\bH[12]\s*'?\s*FY\s*'?\d{2,4}\b|half[- ]year(?:\s+ended[^.\n]{0,30})?|six\s+months"),
    ("nine months", r"\b9M\s*'?\s*FY\s*'?\d{2,4}\b|nine\s+months"),
    ("year to date", r"year[- ]to[- ]date|\bYTD\b|April\s*(?:to|-|–)\s*[A-Z][a-z]+"),
    ("year", r"\bFY\s*'?\d{2,4}\b|(?:for|during|in)\s+the\s+(?:financial\s+|fiscal\s+|full\s+)?year|full[- ]year|year\s+ended[^.\n]{0,30}|\bfiscal\s+\d{4}\b"),
    ("month", r"(?:for|in|during)\s+(?:the\s+month\s+of\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*'?\d{2,4}|month\s+of\s+[A-Z][a-z]+"),
)


def period_of(page: str, start: int, end: int, key: str, title: str = "", filed: date | None = None) -> tuple[str, str]:
    """(kind, words) for the period a figure refers to: 'level' with its date for a balance, otherwise the period cue
    nearest the figure on the page ('quarter', 'year', 'month', …), then the filing's title, else 'not stated'."""
    before, after = page[max(0, start - 260):start], page[end:end + 140]
    if key in _LEVELS:
        m = re.search(r"as\s+(?:on|of|at)\s+" + _DATE, page[max(0, start - 200):end + 160])
        return "level", (f"as at {' '.join(m.group(1).split())}" if m else "level at the filing date")
    best: tuple[int, str, str] | None = None
    for kind, pattern in _CUES:
        for m in re.finditer(pattern, before, re.I):
            distance = len(before) - m.end()
            if best is None or distance < best[0]:
                best = (distance, kind, " ".join(m.group(0).split()))
        m = re.search(pattern, after, re.I)
        if m and (best is None or m.start() + 40 < best[0]):
            best = (m.start() + 40, kind, " ".join(m.group(0).split()))
    if best is not None:
        return best[1], best[2]
    # Nothing beside the figure. A filing made in the weeks after a June, September or December quarter is about that
    # quarter (a March filing covers both the quarter and the year, so it is left unlabelled); failing that, the title.
    after_a_quarter = filed is not None and filed.month in (7, 8, 10, 11, 1, 2)
    for kind, pattern in _CUES:
        m = re.search(pattern, title, re.I)
        if m and not (kind == "year" and after_a_quarter):
            return kind, " ".join(m.group(0).split())
    if after_a_quarter:
        return "quarter", f"quarter reported in {filed:%B %Y}"
    return "not stated", "period not stated beside the figure"


# Measures that mean nothing without knowing what they are a measure of ("8.5% market share" — of what?).
_NEEDS_SCOPE = {"market_share", "volume_growth"}
# Measures that may be for the whole company or for a part of it: the part is named where the sentence names it.
_MAY_HAVE_SCOPE = _NEEDS_SCOPE | {"network", "capacity_utilisation", "order_book", "order_inflow", "capacity", "sales_volume"}
_SCOPE = re.compile(r"(?:market\s+share|volumes?|capacity|order\s*book|touch\s?points|outlets|stores)(?:\s+of\s+[\d.,]+\s*%)?\s+(?:in|for|of|across)\s+(?:the\s+)?([A-Z][^.,;:\n()]{2,48})")
_SUBJECT = re.compile(r"([A-Z][A-Za-z&/-]+(?:\s+[A-Za-z&/-]+){0,2})\s+(?:sales\s+)?(?:volumes?|market\s+share|order\s*book|capacity)\b")
_NOT_A_SCOPE = re.compile(r"^(?:the|its|our|total|overall|strong|company|sales|higher|lower|ytd|secondary|primary|value|volume|fy\s?\d*|q[1-4])(?:\s|$)", re.I)


def scope_of(page: str, start: int, end: int) -> tuple[str | None, str]:
    """(what the figure is a measure of, the sentence it sits in). The scope is taken only from the sentence itself
    ("market share in Washing Machines", "RAC volumes grew"); it is never guessed from a page heading. The sentence
    is returned so the reader sees the figure in its own words."""
    left = max(page.rfind(". ", 0, start), page.rfind("\n\n", 0, start), page.rfind("•", 0, start), page.rfind("\u2022", 0, start), start - 240, -1) + 1
    stops = [x for x in (page.find(". ", end), page.find("\n\n", end), page.find("•", end)) if x != -1]
    right = min(stops + [end + 200, len(page)])
    sentence = " ".join(page[left:right].split()).strip(" .•-–")
    found = _SCOPE.search(sentence) or _SUBJECT.search(sentence)
    scope = None
    for pattern in (_SCOPE, _SUBJECT):
        for found in pattern.finditer(sentence):
            candidate = " ".join(found.group(1).split()).strip(" -–")
            candidate = re.split(r"\s+(?:and\s+\d|for\s+FY|for\s+Q[1-4]|till\b|upto\b|up\s+to\b|during\b|stood\b|was\b|were\b|grew\b|reached\b|rose\b|"
                                 r"increased\b|improved\b|remained\b|registering\b|with\b|which\b|as\s+(?:on|of|at)\b)", candidate)[0].strip()
            if len(candidate) >= 2 and not _NOT_A_SCOPE.match(candidate) and not re.search(r"\d", candidate):
                scope = candidate
                break
        if scope:
            break
    return scope, sentence[:220]


def group_for(stock: Stock) -> tuple[str, tuple] | None:
    text = " | ".join(x for x in (stock.sector, stock.industry, stock.basic_industry) if x)
    return next(((name, measures) for name, pattern, measures in GROUPS if re.search(pattern, text, re.I)), None)


def read_measures(pages: list[str], measures: tuple, title: str = "", filed: date | None = None) -> list[dict]:
    """The first plausible statement of each measure in one document: {key, label, unit, value, quote, page (0-based), period_kind, period}."""
    found = []
    for key, label, unit, lowest, highest, patterns in measures:
        hit = None
        for pattern in patterns:
            for page, text in enumerate(pages):
                for m in re.finditer(pattern, text, re.I):
                    try:
                        value = float(m.group(1).replace(",", ""))
                    except ValueError:
                        continue
                    if _PRIOR.search(text[max(0, m.start(1) - 40):m.start(1)]):
                        continue  # "grew from 314,015 to …": the first number is last period's
                    if unit in _SCALES and m.lastindex and m.lastindex >= 2 and m.group(2):
                        scale = re.sub(r"s$", "", re.sub(r"\s+", " ", m.group(2).lower()))
                        value *= _SCALES[unit].get(scale, 1.0)
                    if lowest <= value <= highest:
                        kind, words = period_of(text, m.start(), m.end(), key, title, filed)
                        scope, sentence = scope_of(text, m.start(), m.end()) if key in _MAY_HAVE_SCOPE else (None, "")
                        hit = {"key": key, "label": label, "unit": unit, "value": value, "quote": m.group(0), "page": page, "period_kind": kind, "period": words,
                               "scope": scope, "sentence": sentence}
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            found.append(hit)
    return found


def read_outlook(pages: list[str], limit: int = 6) -> list[dict]:
    """Forward-looking sentences from a call transcript that carry a figure: {text, page (0-based)}."""
    out, seen = [], set()
    for page, text in enumerate(pages):
        for sentence in re.split(r"(?<=[.?!])\s+", re.sub(r"\s+", " ", text)):
            # Management speaking about itself, not an analyst asking: "we" or "our", no question, no "you".
            if 60 <= len(sentence) <= 420 and _OUTLOOK.search(sentence) and _FIGURE.search(sentence) and sentence[:60] not in seen \
                    and re.search(r"\b(?:we|our)\b", sentence, re.I) and not re.search(r"\?|\byou\b|\bI'm\b|\bmy question\b|^\W*(?:sir|hi|hello|thanks|thank you)\b", sentence, re.I):
                seen.add(sentence[:60])
                out.append({"text": sentence.strip(), "page": page})
                if len(out) >= limit:
                    return out
    return out


def choose_filings(raw: bytes, today: date) -> list[tuple[str, dict, date]]:
    """(kind, feed row, filing date) for the recent filings worth reading, newest first within each kind."""
    from app.bie.nse_filings import _parse_datetime

    candidates: dict[str, list[tuple[dict, date]]] = {k: [] for k in _PER_KIND}
    seen: set[str] = set()
    for row in json.loads(raw):
        when = _parse_datetime(row.get("an_dt") or row.get("sort_date"))
        url = row.get("attchmntFile") or ""
        words = f"{row.get('desc') or ''} {row.get('attchmntText') or ''}"
        if when is None or today - when.date() > _WINDOW or not url.lower().endswith(".pdf") or url in seen:
            continue
        kind = next((k for k, pattern in _KINDS if re.search(pattern, words, re.I | re.S)), None)
        if kind is not None:
            seen.add(url)
            candidates[kind].append((row, when.date()))
    # A press release issued on the day results were filed is the results release: it comes first, then those about
    # sales or production, then the rest (an order win or an appointment says nothing here).
    results_days = {when for _, when in candidates["results filing"]}
    candidates["press release"].sort(key=lambda item: (item[1] not in results_days, not _RESULTS.search(item[0].get("attchmntText") or ""),
                                                       -item[1].toordinal()))
    chosen = [(kind, row, when) for kind, rows in candidates.items() for row, when in rows[:_PER_KIND[kind]]][:MAX_FILINGS]
    return chosen


def ingest_sector_measures(db: Session, nse, stock: Stock, touch=lambda d: d) -> dict:
    """Archive the company's latest presentations, results press releases and call transcript and read them."""
    feed = db.query(Document).filter(Document.company_id == stock.id, Document.document_type == "NSE_ANNOUNCEMENTS").order_by(
        Document.retrieved_at.desc()).first()
    raw = content_of(feed) if feed is not None else None
    if not raw:
        return {"skipped": "no announcements feed on file"}
    group = group_for(stock)
    today = date.today()
    from app.bie.nse_filings import _parse_datetime

    chosen = choose_filings(raw, today)

    had_guidance = db.query(BieFact.id).filter(BieFact.company_id == stock.id, BieFact.fact_type == "guidance").first() is not None
    db.query(BieFact).filter(BieFact.company_id == stock.id, BieFact.fact_type == "sector_kpi").delete(synchronize_session=False)
    summary = {"group": group[0] if group else None, "filings": 0, "measures": 0, "read_by_model": 0, "outlook": 0, "unreadable": 0}
    readable: list[tuple] = []
    for kind, row, when in chosen:
        url = row["attchmntFile"]
        try:
            content = nse.fetch(url, timeout=180)
            pages = page_texts(content)
        except Exception:  # noqa: BLE001 — a filing that cannot be fetched or opened is skipped, the others are still read
            summary["unreadable"] += 1
            continue
        title = re.sub(r"\s+", " ", row.get("attchmntText") or row.get("desc") or kind).strip()[:300]
        document = touch(archive(db, company_id=stock.id, source="NSE", document_type="COMPANY_FILING", url=url, content=content,
                                 content_type="application/pdf", title=title, period_end=when, published_at=_parse_datetime(row.get("an_dt"))))
        if document is None:
            continue
        clear_document_facts(db, document)
        summary["filings"] += 1
        if sum(len(p.strip()) for p in pages) < 400:
            summary["unreadable"] += 1  # a scanned filing: no text to read
            continue
        found_here = 0
        own = group[1] if group else ()
        wanted = own + tuple(m for m in GENERAL if m[0] not in {x[0] for x in own})
        for hit in read_measures(pages, wanted, title, when):
            if kind == "transcript" and hit["key"] not in _FROM_TRANSCRIPT:
                continue
            record_fact(
                db, scope="COMPANY", company_id=stock.id, fact_type="sector_kpi", key=hit["key"], dimension=f"{when:%Y-%m-%d} {url.rsplit('/', 1)[-1]}"[:300],
                period_type="INSTANT", period_end=when, value_num=hit["value"], unit=hit["unit"],
                attributes={"label": hit["label"], "group": group[0] if group else "General", "filing_kind": kind, "filing_title": title,
                            "period_kind": hit["period_kind"], "period": hit["period"], "read_by": "pattern",
                            "scope": hit.get("scope"), "sentence": hit.get("sentence")},
                nature="COMPANY_CLAIM", document=document, locator_type="PAGE", page=hit["page"] + 1, quote=hit["quote"],
                extraction_method="PDF_TEXT", source_tier=1, confidence="MEDIUM", replace=False)
            summary["measures"] += 1
            found_here += 1
        readable.append((kind, when, title, document, pages, url, found_here))
        if kind == "transcript" and not had_guidance:
            for n, item in enumerate(read_outlook(pages)):
                if not quote_on_page(item["text"], pages[item["page"]]):
                    continue
                record_fact(
                    db, scope="COMPANY", company_id=stock.id, fact_type="guidance", key="outlook", dimension=f"{when:%Y-%m-%d} {n}",
                    value_text=item["text"], attributes={"call_date": str(when), "quarter": f"call filed {when:%d %b %Y}", "speaker_role": "on the call",
                                                         "status": None, "for_period": None, "selected_by": "wording"},
                    nature="MANAGEMENT_GUIDANCE", document=document, locator_type="PAGE", page=item["page"] + 1, quote=item["text"],
                    extraction_method="PDF_TEXT", source_tier=1, confidence="LOW", replace=False)
                summary["outlook"] += 1
    # No fixed pattern covers this company, or the patterns found almost nothing: the language model reads the newest
    # presentation (failing that, press release or results filing). Each figure it reports is checked against the page.
    if summary["measures"] < 2:
        from app.bie.llm_assist import read_measures as model_read
        order = {"presentation": 0, "press release": 1, "results filing": 2}
        for kind, when, title, document, pages, url, _ in sorted((x for x in readable if x[0] in order), key=lambda x: (order[x[0]], -x[1].toordinal()))[:1]:
            from app.bie import llm_assist
            llm_assist.UNAVAILABLE = False
            hits = model_read(pages, stock.company_name)
            summary["model_unavailable"] = llm_assist.UNAVAILABLE
            for hit in hits:
                text = pages[hit["page"]]
                at = re.sub(r"\s+", " ", text).find(re.sub(r"\s+", " ", hit["quote"]))
                kind_of, words = period_of(text, max(at, 0), max(at, 0) + len(hit["quote"]), hit["key"], title, when)
                if kind_of == "not stated" and hit["period"]:
                    kind_of, words = "as stated", hit["period"]
                record_fact(
                    db, scope="COMPANY", company_id=stock.id, fact_type="sector_kpi", key=hit["key"], dimension=f"{when:%Y-%m-%d} {url.rsplit('/', 1)[-1]}"[:300],
                    period_type="INSTANT", period_end=when, value_num=hit["value"], unit=hit["unit"],
                    attributes={"label": hit["label"], "group": "Read by the language model", "filing_kind": kind, "filing_title": title,
                                "period_kind": kind_of, "period": words, "read_by": "language model, quote checked"},
                    nature="COMPANY_CLAIM", document=document, locator_type="PAGE", page=hit["page"] + 1, quote=hit["quote"],
                    extraction_method="LLM_TRANSCRIPTION", source_tier=1, confidence="LOW", replace=False)
                summary["measures"] += 1
                summary["read_by_model"] += 1
    return summary


def measures_for(db: Session, company_id: str) -> list[BieFact]:
    """The latest statement of each measure, with the one before it where an earlier filing also gives it."""
    facts = db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.fact_type == "sector_kpi").order_by(BieFact.period_end.desc()).all()
    return facts
