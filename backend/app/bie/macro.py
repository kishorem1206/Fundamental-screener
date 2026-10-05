"""Economy-level facts shown ahead of the sector and company sections:
government bond yields (CCIL's daily tenor-wise table) and the IMF's growth
and inflation projections for India. Both sources were tested live on
2026-10-04; each response is archived like any company document.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from app.bie.documents import archive
from app.bie.evidence import clear_document_facts, record_fact
from app.infrastructure.database.models import Document
from app.logger import logger

CCIL_URL = "https://www.ccilindia.com/web/ccil/tenorwise-indicative-yields"
IMF_URL = "https://www.imf.org/external/datamapper/api/v1/{indicator}/IND"
IMF_INDICATORS = {
    "NGDP_RPCH": ("real_gdp_growth_pct", "Real GDP growth, annual % change"),
    "PCPIPCH": ("cpi_inflation_pct", "Consumer price inflation, average, annual % change"),
}
_BROWSER = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
# The IMF endpoint rejects browser-like agents and answers a plain client.
_PLAIN = {"User-Agent": "curl/8.4.0", "Accept": "application/json"}
_FRESH = timedelta(hours=20)


def _recent(db: Session, document_type: str) -> bool:
    latest = (db.query(Document).filter(Document.document_type == document_type, Document.company_id.is_(None))
              .order_by(Document.retrieved_at.desc()).first())
    return latest is not None and datetime.now(timezone.utc) - latest.retrieved_at < _FRESH


def ingest_gsec_yields(db: Session) -> int:
    import pandas as pd

    response = requests.get(CCIL_URL, headers=_BROWSER, timeout=45)
    response.raise_for_status()
    html = response.text
    table = max(pd.read_html(io.StringIO(html)), key=lambda t: t.size)
    table.columns = [str(c).strip() for c in table.columns]
    if not {"Date", "Tenor Bucket", "Security", "YTM (%)"} <= set(table.columns):
        raise ValueError(f"CCIL table layout changed: {list(table.columns)}")
    as_of = pd.to_datetime(table["Date"].iloc[0]).date()
    document = archive(
        db, company_id=None, source="CCIL", document_type="CCIL_GSEC_YIELDS", url=CCIL_URL,
        content=response.content, content_type="text/html", period_end=as_of,
        title=f"CCIL tenor-wise indicative yields, {as_of:%d %b %Y}",
        published_at=datetime(as_of.year, as_of.month, as_of.day, tzinfo=timezone.utc),
    )
    if document is None:
        return 0
    clear_document_facts(db, document)
    written = 0
    for _, row in table.iterrows():
        security, bucket = str(row["Security"]).strip(), str(row["Tenor Bucket"]).strip()
        raw = re.search(rf"{re.escape(security)}</td>\s*<td[^>]*>\s*([\d.]+)\s*<", html)
        if raw is None:
            continue
        record_fact(
            db, scope="MACRO", fact_type="rates", key="gsec_yield_pct", dimension=f"{bucket} | {security}",
            period_type="INSTANT", period_end=as_of, value_num=float(raw.group(1)), unit="%",
            attributes={"tenor_bucket": bucket, "security": security, "is_central_government": " GS " in f" {security} "},
            nature="THIRD_PARTY", document=document, locator_type="TABLE", locator=f"Tenor Bucket = {bucket}; Security = {security}",
            quote=raw.group(1), extraction_method="HTML_TABLE", source_tier=1, confidence="HIGH", replace=False,
        )
        written += 1
    return written


def ingest_imf_projections(db: Session, years_back: int = 2, years_ahead: int = 4) -> int:
    written = 0
    this_year = date.today().year
    for indicator, (key, label) in IMF_INDICATORS.items():
        url = IMF_URL.format(indicator=indicator)
        response = requests.get(url, headers=_PLAIN, timeout=60)
        response.raise_for_status()
        raw = response.text
        block = re.search(r'"IND":\{([^}]*)\}', raw)
        if block is None:
            raise ValueError(f"IMF response for {indicator} has no India series")
        document = archive(
            db, company_id=None, source="IMF", document_type=f"IMF_{indicator}", url=url, content=response.content,
            content_type="application/json", title=f"IMF DataMapper — {label}, India",
            published_at=datetime.now(timezone.utc),
        )
        if document is None:
            continue
        clear_document_facts(db, document)
        for year in range(this_year - years_back, this_year + years_ahead + 1):
            point = re.search(rf'"{year}":(-?[\d.]+)', block.group(1))
            if point is None:
                continue
            record_fact(
                db, scope="MACRO", fact_type="macro", key=key, dimension=str(year), period_type="YEAR",
                period_end=date(year, 12, 31), value_num=float(point.group(1)), unit="%",
                attributes={"label": label, "is_projection": year >= this_year,
                            "basis": "IMF reports India by fiscal year: year t runs April t to March t+1"},
                nature="THIRD_PARTY", document=document, locator_type="JSON", locator=f"values.{indicator}.IND.{year}",
                quote=point.group(0), extraction_method="API_JSON", source_tier=1, confidence="HIGH", replace=False,
            )
            written += 1
    return written


def ingest_macro(db: Session, force: bool = False) -> dict:
    """Refresh both sources unless fetched within the last 20 hours. A source
    that fails is reported and skipped; the build carries on without it."""
    out: dict = {}
    for name, document_type, run in (("gsec_yields", "CCIL_GSEC_YIELDS", ingest_gsec_yields),
                                     ("imf_projections", "IMF_NGDP_RPCH", ingest_imf_projections)):
        if not force and _recent(db, document_type):
            out[name] = "fresh"
            continue
        try:
            out[name] = run(db)
            db.commit()
        except Exception as e:  # noqa: BLE001
            db.rollback()
            logger.warning("bie: macro source failed", source=name, error=str(e))
            out[name] = f"failed: {type(e).__name__}: {e}"
    return out
