"""PPAC (Petroleum Planning & Analysis Cell) monthly "Snapshot of India's Oil & Gas data".

Regulator-side source for gas infrastructure companies whose own filings are thin:
 - Table 21 (existing LNG terminals): capacity and % utilisation FYTD per terminal -> Petronet LNG
   (Dahej + Kochi) capacity-weighted regas utilisation, stored as a monthly FYTD series
   `mth_oilgas_regas_utilization_fytd_ppac` (a cross-check against the utilisation Petronet states
   on its quarterly call, not a quarterly figure).
 - Table 20 (common-carrier gas pipeline network, PNGRB): operational length and authorised
   capacity for GAIL and GSPL as on the stated date -> `qtr_oilgas_pipeline_network_km` /
   `qtr_oilgas_pipeline_authorised_mmscmd` (fully commissioned pipelines only; GAIL's
   partially-commissioned 7,118 km is not counted).
Text comes from poppler `pdftotext -layout` (skipped cleanly if missing). Never raises.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.ingestion import nse_client
from app.logger import logger

_HOME = "https://www.ppac.gov.in/"
_SOURCE = "PPAC_REPORT"
_NUM = r"[\d,]+(?:\.\d+)?"


def _f(x: str) -> float:
    return float(x.replace(",", "").rstrip("*"))


def parse_terminals(text: str) -> dict | None:
    """-> {"period_end", "petronet_capacity_mmtpa", "petronet_utilization_pct"} from Table 21."""
    m = re.search(r"Capacity utili[sz]ation[^\n]*\(Apr'26\s*-\s*([A-Za-z]{3})'?\s*(\d{2,4})", text) or \
        re.search(r"\(Apr'(\d{2})\s*-\s*([A-Za-z]{3})", text)
    caps = {}
    for line in text.splitlines():
        r = re.match(r"^\s*(Dahej|Kochi)\s+Petronet LNG Ltd \(PLL\)\s+(" + _NUM + r")\s+(" + _NUM + r")\*?", line)
        if r:
            caps[r.group(1)] = (_f(r.group(2)), _f(r.group(3)))
    if set(caps) != {"Dahej", "Kochi"}:
        return None
    cap = sum(c for c, _ in caps.values())
    util = sum(c * u for c, u in caps.values()) / cap
    if not (0 < util <= 100):
        return None
    return {"petronet_capacity_mmtpa": cap, "petronet_utilization_pct": round(util, 2),
            "dahej_pct": caps["Dahej"][1], "kochi_pct": caps["Kochi"][1], "note": m.group(0) if m else "FYTD"}


def parse_pipelines(text: str) -> dict | None:
    """-> {"as_on": "YYYY-MM-DD", "GAIL": (km, mmscmd), "GSPL": (km, mmscmd)} from Table 20."""
    m = re.search(r"pipeline network as on (\d{2})\.(\d{2})\.(\d{4})", text, re.I)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^\s*Nature of pipeline\s+GAIL\s+GSPL\s+PIL", line):
            length = cap = None
            for nxt in lines[i + 1:i + 6]:
                a = re.match(r"^\s*Operational\s+Length\s+(" + _NUM + r")\s+(" + _NUM + r")", nxt)
                b = re.match(r"^\s*Capacity\s+(" + _NUM + r")\s+(" + _NUM + r")", nxt)
                if a and length is None:
                    length = (_f(a.group(1)), _f(a.group(2)))
                elif b and length is not None and cap is None:
                    cap = (_f(b.group(1)), _f(b.group(2)))
            if length and cap and m:
                return {"as_on": f"{m.group(3)}-{m.group(2)}-{m.group(1)}",
                        "GAIL": (length[0], cap[0]), "GSPL": (length[1], cap[1])}
    return None


def _snapshot_text(session) -> tuple[str | None, str | None]:
    if shutil.which("pdftotext") is None:
        return None, None
    html = session.get(_HOME, timeout=40, headers={"Referer": _HOME}).text
    link = re.search(r'href="(https://ppac\.gov\.in/download\.php\?file=rep_studies/[^"]*Snapshot[^"]*\.pdf)"', html)
    if not link:
        return None, None
    blob = session.get(link.group(1), timeout=90).content
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(blob), f.flush()
        out = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, timeout=90).stdout
    return out, link.group(1)


def ingest_ppac_gas_data(db: Session, symbol: str, company_id: str) -> list:
    """PETRONET -> regas utilisation FYTD; GAIL/GSPL -> pipeline network. [] otherwise."""
    if symbol not in ("PETRONET", "GAIL", "GSPL"):
        return []
    inserted: list = []
    try:
        session = nse_client._session()
        text, url = _snapshot_text(session)
        if not text:
            return []
        now = datetime.now(timezone.utc)
        month = re.search(r"Snapshot of India's Oil & Gas data\s*-\s*([A-Za-z]{3}),?\s*(\d{4})", text)

        def put(key, value, unit, period, doc, kind="REPORTED", conf="HIGH", formula=None):
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=key, period=period, value=round(value, 2), unit=unit,
                statement_type="CONSOLIDATED", source=_SOURCE, source_tier=1, reported_or_calculated=kind,
                confidence=conf, calculation_formula=formula, source_url=url, source_document=doc, source_date=now)
            if row is not None:
                inserted.append(row)

        if symbol == "PETRONET":
            t = parse_terminals(text)
            if t and month:
                import calendar
                mo = list(calendar.month_abbr).index(month.group(1).capitalize())
                period = f"{month.group(2)}-{mo:02d}-{calendar.monthrange(int(month.group(2)), mo)[1]:02d}"
                put("mth_oilgas_regas_utilization_fytd_ppac", t["petronet_utilization_pct"], "%", period,
                    f"PPAC Snapshot table 21: Dahej {t['dahej_pct']}% and Kochi {t['kochi_pct']}% FYTD, capacity-weighted over "
                    f"{t['petronet_capacity_mmtpa']} MMTPA (FYTD, not a quarterly figure; asterisked terminals cover Apr-Jul)",
                    kind="CALCULATED", conf="MEDIUM", formula="sum(capacity x utilisation) / sum(capacity) over Dahej and Kochi")
        else:
            p = parse_pipelines(text)
            if p:
                km, cap = p[symbol]
                put("qtr_oilgas_pipeline_network_km", km, "km", p["as_on"],
                    f"PPAC Snapshot table 20 (PNGRB): {symbol} fully-commissioned common-carrier gas pipeline length as on {p['as_on']}")
                put("qtr_oilgas_pipeline_authorised_mmscmd", cap, "MMSCMD", p["as_on"],
                    f"PPAC Snapshot table 20 (PNGRB): {symbol} authorised capacity of operational common-carrier pipelines")
    except Exception as e:
        logger.warning("ppac_client: ingestion failed", symbol=symbol, error=str(e))
    return inserted
