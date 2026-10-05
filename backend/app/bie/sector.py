"""Phase 3 — sector intelligence: industry benchmarks (Damodaran's India
datasets, refreshed each January), the revenue-driver framework for each
sector, and which sector-specific measures the filings carry.

The benchmark files are third-party aggregates, stored as THIRD_PARTY facts
under Damodaran's own industry names; `benchmark_industry` maps an NSE
classification onto one of them and the report always prints the name it
matched, so a poor match is visible rather than silent.
"""
from __future__ import annotations

import io
import re
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from app.bie.documents import archive, content_of
from app.bie.evidence import clear_document_facts, record_fact
from app.bie.macro import _BROWSER
from app.infrastructure.database.models import BieFact, Document

BASE = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"
# file -> {column header prefix: (fact key, unit)}
FILES = {
    "betaIndia.xls": {"Number of firms": ("firms", "count"), "Beta": ("beta", "x"), "D/E Ratio": ("debt_to_equity", "ratio"),
                      "Unlevered beta corrected for cash": ("unlevered_beta", "x")},
    "waccIndia.xls": {"Cost of Equity": ("cost_of_equity", "ratio"), "Cost of Capital (Local Currency)": ("cost_of_capital_inr", "ratio")},
    "marginIndia.xls": {"Gross Margin": ("gross_margin", "ratio"), "Net Margin": ("net_margin", "ratio"),
                        "EBITDA/Sales": ("ebitda_margin", "ratio")},
    "peIndia.xls": {"Trailing PE": ("trailing_pe", "x")},
    "vebitdaIndia.xls": {"EV/EBITDA": ("ev_ebitda", "x"), "EV/EBIT": ("ev_ebit", "x")},
}
_FRESH = timedelta(days=30)

# First match wins; tested against NSE industry / basic-industry names.
_MAP = [
    (r"cigarette|tobacco", "Tobacco"), (r"pharma", "Drugs (Pharmaceutical)"), (r"biotech", "Drugs (Biotechnology)"),
    (r"hospital|healthcare service", "Hospitals/Healthcare Facilities"), (r"private sector bank|public sector bank", "Bank (Money Center)"),
    (r"\bbank", "Banks (Regional)"), (r"life insurance", "Insurance (Life)"), (r"insurance", "Insurance (General)"),
    (r"asset management|capital market|stockbroking|exchange", "Investments & Asset Management"),
    (r"finance|nbfc|microfinance|housing finance|fintech|holding", "Financial Svcs. (Non-bank & Insurance)"),
    (r"software|it enabled|computers - software", "Software (System & Application)"), (r"it - services|consulting", "Computer Services"),
    (r"packaged food|food product|dairy|edible oil|sugar|tea|coffee|meat", "Food Processing"),
    (r"agricultural|agri|seed|fertili|pesticide", "Farming/Agriculture"), (r"breweries|distiller|alcohol", "Beverage (Alcoholic)"),
    (r"personal care|household|diversified fmcg", "Household Products"), (r"paper|forest|jute", "Paper/Forest Products"),
    (r"packaging", "Packaging & Container"), (r"cement|building product|ceramic|tiles|sanitary", "Building Materials"),
    (r"passenger car|commercial vehicle|2/3 wheeler|tractor|automobile", "Auto & Truck"), (r"tyre|rubber", "Rubber& Tires"),
    (r"auto component|auto ancillar", "Auto Parts"), (r"steel|iron", "Steel"), (r"aluminium|copper|zinc|mineral|mining", "Metals & Mining"),
    (r"refiner|oil exploration|integrated oil", "Oil/Gas (Integrated)"), (r"gas (transmission|distribution)|lpg|cng", "Oil/Gas Distribution"),
    (r"coal", "Coal & Related Energy"), (r"renewable|green energy", "Green & Renewable Energy"), (r"power|electric utilit", "Power"),
    (r"telecom - (cellular|services)|telecom.*service", "Telecom (Wireless)"), (r"telecom", "Telecom. Equipment"),
    (r"civil construction|infrastructure|engineering", "Engineering/Construction"), (r"residential|commercial project|realty|real estate", "Real Estate (Development)"),
    (r"aerospace|defen[cs]e", "Aerospace/Defense"), (r"electrical equipment|cables|transformer", "Electrical Equipment"),
    (r"industrial product|machin|compressor|pump|bearing|capital goods", "Machinery"), (r"specialty chemical", "Chemical (Specialty)"),
    (r"commodity chemical|petrochemical", "Chemical (Basic)"), (r"chemical|explosive|dyes|paint", "Chemical (Diversified)"),
    (r"garment|apparel|textile", "Apparel"), (r"footwear", "Shoe"), (r"jewel|gems|watch", "Retail (Special Lines)"),
    (r"e-retail|e-commerce|internet", "Software (Internet)"), (r"retail", "Retail (General)"), (r"hotel|resort|restaurant", "Hotel/Gaming"),
    (r"airline|airport", "Air Transport"), (r"port|shipping|logistics|transport", "Transportation"),
    (r"consumer electronics|household appliance|durable", "Electronics (Consumer & Office)"), (r"media|entertainment|broadcast|film", "Entertainment"),
    (r"education", "Education"), (r"water|waste", "Environmental & Waste Services"), (r"diversified", "Diversified"),
]

# How revenue is built, by screener sector. Shown as a framework, not a forecast.
DRIVERS = {
    # Keyed by NSE basic industry where the sector-wide formula would mislead (an insurer is not a lender).
    "Life Insurance": ("New business value = annualised premium on new policies × new business margin", ["First-year premium growth and market share", "Product mix (protection, savings, unit-linked)", "New business margin", "Persistency (policies renewed)", "Solvency ratio"]),
    "General Insurance": ("Underwriting result = net earned premium × (1 − combined ratio); profit adds investment income on the float", ["Gross premium growth and market share", "Mix of motor, health and commercial lines", "Claims ratio", "Combined ratio", "Investment yield and solvency"]),
    "Financial Services": ("Net interest income = average earning assets × net interest margin", ["Loan and deposit growth", "Yield on advances and cost of funds", "Fee income", "Credit cost (provisions ÷ advances)", "Cost-to-income"]),
    "Fast Moving Consumer Goods": ("Revenue = volume × price × product mix", ["Volume growth", "Price and mix", "Distribution reach", "Input-cost pass-through", "Advertising intensity"]),
    "Healthcare": ("Revenue = Σ market (India, US, others) × products × price", ["India prescription growth and market share", "US launches and price erosion", "Regulatory approvals and plant status", "R&D spend"]),
    "Information Technology": ("Revenue = billed headcount × utilisation × realisation per person", ["Deal wins and order book", "Constant-currency growth", "Utilisation and attrition", "Pricing and offshore mix"]),
    "Automobile and Auto Components": ("Revenue = units sold × average realisation", ["Industry volumes and market share", "Product mix and realisation", "Capacity utilisation", "Commodity costs"]),
    "Capital Goods": ("Revenue = opening order book × execution rate + new orders executed in year", ["Order inflow", "Order book ÷ revenue", "Execution and working capital", "Margin on orders"]),
    "Construction": ("Revenue = order book × execution rate", ["Order inflow", "Execution pace", "Working capital and collections"]),
    "Construction Materials": ("Revenue = capacity × utilisation × realisation per tonne", ["Volume", "Realisation per tonne", "Power, fuel and freight cost per tonne", "EBITDA per tonne"]),
    "Metals & Mining": ("Revenue = volume × realisation per tonne", ["Production and sales volume", "Commodity price", "Cost per tonne", "Net debt"]),
    "Oil, Gas & Consumable Fuels": ("Revenue = throughput × (product price); profit = throughput × margin per barrel", ["Refining margin", "Throughput and utilisation", "Crude and gas prices", "Marketing margin"]),
    "Power": ("Revenue = capacity × plant load factor × tariff", ["Capacity additions", "Plant load factor", "Tariff and fuel cost", "Receivables"]),
    "Telecommunication": ("Revenue = subscribers × average revenue per user", ["Subscriber additions and churn", "Average revenue per user", "Data usage", "Capex intensity"]),
    "Realty": ("Revenue recognised = completed area × realisation; cash = bookings × collections", ["Pre-sales (booking value)", "Collections", "Launch pipeline", "Net debt"]),
    "Consumer Durables": ("Revenue = units × price × mix", ["Volume growth", "Channel reach", "Commodity costs", "Market share"]),
    "Consumer Services": ("Revenue = customers or orders × value per order × take rate", ["Order growth", "Average order value", "Contribution margin", "Store or room additions"]),
    "Chemicals": ("Revenue = volume × realisation", ["Capacity and utilisation", "Spread over raw material", "Export mix", "Capex cycle"]),
    "Textiles": ("Revenue = volume × realisation", ["Capacity utilisation", "Cotton and yarn prices", "Export demand"]),
    "Services": ("Revenue = volume handled × realisation per unit", ["Volume (cargo, passengers, shipments)", "Realisation", "Utilisation"]),
}
DEFAULT_DRIVER = ("Revenue = volume × price", ["Volume growth", "Price and mix", "Capacity and utilisation", "Input costs"])


def benchmark_industry(*names: str | None) -> str | None:
    """Damodaran's industry name for an NSE basic industry / industry, most specific name first."""
    for name in names:
        for pattern, target in _MAP if name else []:
            if re.search(pattern, name, re.I):
                return target
    return None


def ingest_benchmarks(db: Session, force: bool = False) -> dict:
    import pandas as pd

    latest = (db.query(Document).filter(Document.document_type == "DAMODARAN_betaIndia.xls").order_by(Document.retrieved_at.desc()).first())
    if latest is not None and not force and datetime.now(timezone.utc) - latest.retrieved_at < _FRESH:
        return {"status": "fresh"}
    out = {}
    for filename, columns in FILES.items():
        url = BASE + filename
        response = requests.get(url, headers=_BROWSER, timeout=90)
        response.raise_for_status()

        def table(content: bytes):
            sheet = pd.ExcelFile(io.BytesIO(content)).parse("Industry Averages", header=None)
            head = next(i for i in range(len(sheet)) if str(sheet.iloc[i, 0]).strip().lower().startswith("industry name"))
            updated = next((str(v)[:10] for v in sheet.head(head).values.flatten() if re.match(r"20\d\d-\d\d-\d\d", str(v))), None)
            return sheet, head, updated

        sheet, head, updated = table(response.content)
        as_of = datetime.fromisoformat(updated).replace(tzinfo=timezone.utc) if updated else datetime.now(timezone.utc)
        document = archive(db, company_id=None, source="Damodaran, NYU Stern", document_type=f"DAMODARAN_{filename}", url=url,
                           content=response.content, content_type="application/vnd.ms-excel", period_end=as_of.date(),
                           title=f"Damodaran India industry averages — {filename}, updated {as_of:%d %b %Y}", published_at=as_of)
        if document is None:
            continue
        clear_document_facts(db, document)
        # Re-read from the archived copy, so what is stored is what the archive holds.
        archived, a_head, _ = table(content_of(document) or response.content)
        headers = [str(h).strip() for h in sheet.iloc[head].tolist()]
        written = 0
        for header, (key, unit) in columns.items():
            col = next((j for j, h in enumerate(headers) if h == header), None)
            if col is None:
                continue
            for i in range(head + 1, len(sheet)):
                industry, value = str(sheet.iloc[i, 0]).strip(), sheet.iloc[i, col]
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    continue
                if not industry or industry == "nan" or number != number:
                    continue
                fact = record_fact(
                    db, scope="SECTOR", sector=industry, fact_type="industry_benchmark", key=key, period_type="INSTANT",
                    period_end=as_of.date(), value_num=number, unit=unit, nature="THIRD_PARTY", document=document,
                    locator_type="TABLE", locator=f"sheet 'Industry Averages', row '{industry}', column '{header}'",
                    quote=str(value), extraction_method="SPREADSHEET", source_tier=2, confidence="MEDIUM", replace=False,
                )
                same = str(archived.iloc[a_head + (i - head), col]) == str(value)
                fact.verification_status, fact.verified_at = ("VERIFIED" if same else "FAILED"), datetime.now(timezone.utc)
                written += 1
        try:
            status = requests.get(url, headers=_BROWSER, timeout=30, stream=True).status_code
        except Exception:  # noqa: BLE001
            status = None
        document.link_status, document.link_checked_at = status, datetime.now(timezone.utc)
        db.commit()
        out[filename] = written
    return out


def benchmarks_for(db: Session, industry: str) -> dict[str, BieFact]:
    facts = db.query(BieFact).filter(BieFact.scope == "SECTOR", BieFact.sector == industry,
                                     BieFact.fact_type == "industry_benchmark").order_by(BieFact.created_at).all()
    return {f.key: f for f in facts}


ERP_URL = BASE + "ctryprem.xlsx"


def ingest_equity_risk_premium(db: Session, force: bool = False) -> dict:
    """India's equity risk premium and country risk premium from Damodaran's country file."""
    import pandas as pd

    latest = db.query(Document).filter(Document.document_type == "DAMODARAN_ctryprem.xlsx").order_by(Document.retrieved_at.desc()).first()
    if latest is not None and not force and datetime.now(timezone.utc) - latest.retrieved_at < _FRESH:
        return {"status": "fresh"}
    response = requests.get(ERP_URL, headers=_BROWSER, timeout=90)
    response.raise_for_status()
    document = archive(db, company_id=None, source="Damodaran, NYU Stern", document_type="DAMODARAN_ctryprem.xlsx", url=ERP_URL,
                       content=response.content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       title="Damodaran country default spreads and risk premiums", published_at=datetime.now(timezone.utc))
    if document is None:
        return {"status": "not archived"}
    clear_document_facts(db, document)
    sheet = pd.ExcelFile(io.BytesIO(content_of(document) or response.content)).parse("ERPs by country", header=None)
    head = next(i for i in range(len(sheet)) if str(sheet.iloc[i, 0]).strip() == "Country")
    headers = [str(h).strip() for h in sheet.iloc[head].tolist()]
    row = next(i for i in range(head + 1, len(sheet)) if str(sheet.iloc[i, 0]).strip() == "India")
    written = 0
    for header, key in (("Total Equity Risk Premium", "equity_risk_premium_india"), ("Country Risk Premium", "country_risk_premium_india")):
        col = headers.index(header)
        fact = record_fact(
            db, scope="MACRO", fact_type="rates", key=key, period_type="INSTANT", period_end=document.retrieved_at.date(),
            value_num=float(sheet.iloc[row, col]), unit="ratio", nature="THIRD_PARTY", document=document, locator_type="TABLE",
            locator=f"sheet 'ERPs by country', row 'India', column '{header}'", quote=str(sheet.iloc[row, col]),
            extraction_method="SPREADSHEET", source_tier=2, confidence="MEDIUM",
        )
        fact.verification_status, fact.verified_at = "VERIFIED", datetime.now(timezone.utc)
        written += 1
    try:
        document.link_status = requests.get(ERP_URL, headers=_BROWSER, timeout=30, stream=True).status_code
    except Exception:  # noqa: BLE001
        document.link_status = None
    document.link_checked_at = datetime.now(timezone.utc)
    db.commit()
    return {"facts": written}
