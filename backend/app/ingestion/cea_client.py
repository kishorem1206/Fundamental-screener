"""CEA monthly Executive Summary -> all-India thermal PLF by ownership sector.

Industry benchmark, NOT the company's own PLF: the Central Electricity Authority publishes
thermal PLF for Central, State, Private IPP and Private utility plants each month (cea.nic.in
"Executive Summary" PDF, table 10). It lets a listed generator's own stated PLF be read against
its ownership peer group. Stored per month under `mth_pow_thermal_plf_sector_benchmark`; the
quarter-end month also becomes `qtr_pow_thermal_plf_sector_benchmark` (a single month, labelled so —
the May 2026 report sits under an unguessable file name, so a three-month average is not reliable). Text comes from poppler `pdftotext`
(skipped cleanly if missing). Which ownership group a company belongs to is a coarse mapping and
is recorded in the provenance text.
"""
from __future__ import annotations

import calendar
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.ingestion import nse_client
from app.logger import logger

_BASE = "https://cea.nic.in/wp-content/uploads/executive"
_SOURCE = "CEA_REPORT"
_ROW = re.compile(r"^\s*(Central|State|Private Sector IPP|Private Sector UTL\.?|ALL INDIA)\s+(\d{2}\.\d{2})\s+(\d{2}\.\d{2})\s*$", re.I)
# ownership group per NSE symbol (thermal generators / integrated utilities only)
_GROUP_BY_SYMBOL = {
    "NTPC": "central", "NLCINDIA": "central", "SJVN": "central",
    "ADANIPOWER": "private sector ipp", "JSWENERGY": "private sector ipp", "RPOWER": "private sector ipp", "JPPOWER": "private sector ipp",
    "TATAPOWER": "private sector utl", "CESC": "private sector utl", "TORNTPOWER": "private sector utl",
}


def parse_executive_summary(text: str) -> dict | None:
    """-> {"month_end", "plf": {group: pct}} for the report month, or None."""
    m = re.search(r"Thermal PLF Sector-wise[^\n]*for\s+([A-Za-z]{3})-(\d{4})", text)
    if not m:
        return None
    plf: dict[str, float] = {}
    for line in text.splitlines():
        r = _ROW.match(line)
        if r:
            plf[r.group(1).lower().rstrip(".")] = float(r.group(3))  # column 3 = the report month
    if not {"central", "state", "all india"} <= set(plf):
        return None
    try:
        month = list(calendar.month_abbr).index(m.group(1).capitalize())
    except ValueError:
        return None
    year = int(m.group(2))
    return {"month_end": f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}", "plf": plf}


def _pdf_text(blob: bytes) -> str | None:
    if shutil.which("pdftotext") is None:
        return None
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(blob), f.flush()
        try:
            return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, timeout=90).stdout
        except Exception:
            return None


def _candidate_urls(year: int, month: int) -> list[str]:
    name = calendar.month_name[month]
    return [f"{_BASE}/{year}/{month:02d}/Executive_Summary_{name}_{year}_Actual.pdf",
            f"{_BASE}/{year}/{month:02d}/Executive_Summary_{name}_{year}.pdf",
            f"{_BASE}/{year}/{month + 1 if month < 12 else 1:02d}/Executive_Summary_{name}_{year}_Actual.pdf"]


def ingest_cea_sector_plf(db: Session, symbol: str, company_id: str, months_back: int = 7) -> list:
    """Stores the CEA sector-benchmark thermal PLF for the ownership group of `symbol` for the
    latest months (monthly + quarter roll-up). [] for non-thermal symbols. Never raises."""
    group = _GROUP_BY_SYMBOL.get(symbol)
    if group is None:
        return []
    inserted: list = []
    try:
        session = nse_client._session()
        now = datetime.now(timezone.utc)
        y, mo = now.year, now.month
        last_url = None
        for _ in range(months_back):
            mo -= 1
            if mo == 0:
                y, mo = y - 1, 12
            for url in _candidate_urls(y, mo):
                r = session.get(url, timeout=60, headers={"Referer": "https://cea.nic.in/"})
                if r.status_code != 200 or not r.content.startswith(b"%PDF"):
                    continue
                parsed = parse_executive_summary(_pdf_text(r.content) or "")
                if parsed and group in parsed["plf"]:
                    last_url = url
                    row = metric_store.insert_metric_value(
                        db, company_id=company_id, metric_key="mth_pow_thermal_plf_sector_benchmark",
                        period=parsed["month_end"], value=parsed["plf"][group], unit="%", statement_type="CONSOLIDATED",
                        source=_SOURCE, source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
                        source_url=url, source_document=f"CEA Executive Summary table 10, all-India thermal PLF for the {group} sector (benchmark, not the company's own PLF)",
                        source_date=now, raw_reported_value=str(parsed["plf"][group]))
                    if row is not None:
                        inserted.append(row)
                    if int(parsed["month_end"][5:7]) % 3 == 0:  # quarter-end month stands in for the quarter on the KPI card
                        row = metric_store.insert_metric_value(
                            db, company_id=company_id, metric_key="qtr_pow_thermal_plf_sector_benchmark",
                            period=parsed["month_end"], value=parsed["plf"][group], unit="%", statement_type="CONSOLIDATED",
                            source=_SOURCE, source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
                            source_url=url, source_document=f"CEA Executive Summary table 10, all-India thermal PLF for the {group} sector, QUARTER-END MONTH only (benchmark, not the company's own PLF)",
                            source_date=now, raw_reported_value=str(parsed["plf"][group]))
                        if row is not None:
                            inserted.append(row)
                    break
    except Exception as e:
        logger.warning("cea_client: ingestion failed", symbol=symbol, error=str(e))
    return inserted
