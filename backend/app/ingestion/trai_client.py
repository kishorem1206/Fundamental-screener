"""TRAI monthly telecom-subscription report -> operator market shares.

TRAI's press release (trai.gov.in, "Telecom Subscription Data as on <Month>") has an
Annexure-I table of wireless (mobile) subscribers by operator that is a rotated page:
pdfplumber reads it reversed, so the text is taken with poppler's `pdftotext -layout`
(skipped cleanly when it is not installed). Shares are subscribers / TRAI's own total
for the month; each is cross-checked against the shares TRAI prints in its text
(Vodafone Idea, BSNL) and dropped if they disagree by more than 0.05 points.

TRAI counts differ from company-reported customer bases (TRAI includes M2M/IoT), so the
share is stored as a separate `mth_/qtr_tel_market_share_mobile_pct` metric.
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

_LIST_URL = "https://www.trai.gov.in/release-publication/reports/telecom-subscriptions-reports"
_BASE = "https://www.trai.gov.in"
_SOURCE = "TRAI_REPORT"
_NUM = r"\d{1,3}(?:,\d{3})+"
# operator column order in Annexure-I after the service-area rows; only symbols listed on NSE are stored
_OPERATORS = ["airtel", "rcom", "vi", "bsnl", "mtnl", "jio"]
_SYMBOL_BY_OPERATOR = {"airtel": "BHARTIARTL", "vi": "IDEA", "mtnl": "MTNL"}


def parse_report(text: str) -> dict | None:
    """-> {"month_end", "total_mn", "shares": {operator: pct}} or None. Uses the Annexure-I
    total row (the one that ends in the all-operator total, then the monthly net addition) and
    passes only if the computed BSNL share agrees with the share TRAI prints in its text."""
    flat = re.sub(r"\s+", " ", text)
    m = re.search(r"Telecom Subscription Data at the end of ([A-Za-z]+) (\d{4})", flat)
    if not m:
        return None
    row_nums = None
    for line in text.splitlines():
        if not re.match(r"\s*total\s+" + _NUM, line, re.I):
            continue
        nums = [int(x.replace(",", "")) for x in re.findall(_NUM, line)]
        # operator Jun columns must add up to (almost) the all-operator total in position 11
        if len(nums) >= 12 and abs(sum(nums[i] for i in (1, 3, 5, 7, 9)) - nums[11]) / nums[11] < 0.002:
            row_nums = nums
            break
    if row_nums is None:
        return None
    total = float(row_nums[11])
    ops = {"airtel": row_nums[1], "vi": row_nums[3], "bsnl": row_nums[5], "mtnl": row_nums[7], "jio": row_nums[9]}
    shares = {k: round(v / total * 100, 2) for k, v in ops.items()}
    printed_bsnl = re.search(r"BSNL,\s*(\d{1,2}\.\d{2})\s*%", flat)
    if printed_bsnl and abs(float(printed_bsnl.group(1)) - shares["bsnl"]) > 0.05:
        return None
    if not 95 <= sum(shares.values()) <= 101:
        return None
    month = list(calendar.month_name).index(m.group(1).capitalize())
    year = int(m.group(2))
    return {"month_end": f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}",
            "total_mn": round(total / 1_000_000, 2), "shares": shares}


def _pdf_text(blob: bytes) -> str | None:
    if shutil.which("pdftotext") is None:
        return None
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(blob), f.flush()
        try:
            return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, timeout=60).stdout
        except Exception:
            return None


def ingest_trai_market_share(db: Session, symbol: str, company_id: str, n_reports: int = 3) -> list:
    """Stores the operator's mobile subscriber market share for the latest TRAI reports (monthly key
    `mth_tel_market_share_mobile_pct`, plus `qtr_...` for quarter-end months). Never raises."""
    operator = next((o for o, s in _SYMBOL_BY_OPERATOR.items() if s == symbol), None)
    if operator is None:
        return []
    inserted: list = []
    try:
        session = nse_client._session()
        html = session.get(_LIST_URL, timeout=30, headers={"Referer": _BASE}).text
        links = re.findall(r'href="(/sites/default/files/[^"]+PR_No[^"]+\.pdf)"', html)[:n_reports]
        now = datetime.now(timezone.utc)
        for link in links:
            url = _BASE + link
            text = _pdf_text(session.get(url, timeout=90).content)
            parsed = parse_report(text or "")
            if not parsed:
                continue
            keys = ["mth_tel_market_share_mobile_pct"]
            if int(parsed["month_end"][5:7]) % 3 == 0:
                keys.append("qtr_tel_market_share_mobile_pct")
            for key in keys:
                row = metric_store.insert_metric_value(
                    db, company_id=company_id, metric_key=key, period=parsed["month_end"],
                    value=parsed["shares"][operator], unit="%", statement_type="CONSOLIDATED", source=_SOURCE,
                    source_tier=1, reported_or_calculated="CALCULATED", confidence="HIGH",
                    calculation_formula="operator wireless (mobile) subscribers / TRAI total wireless (mobile) subscribers * 100",
                    source_url=url, source_document="TRAI monthly telecom subscription report, Annexure-I (TRAI counts include M2M; differs from company-reported base)",
                    source_date=now)
                if row is not None:
                    inserted.append(row)
    except Exception as e:
        logger.warning("trai_client: ingestion failed", symbol=symbol, error=str(e))
    return inserted
