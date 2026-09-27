"""Dual-writes a small screenable subset of the Quarterly Intelligence
result back into the `fa_metric_data_points` ledger — same convention as
`pl_intelligence/persistence.py::sync_to_metric_ledger()`.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store

_LEDGER_SOURCE = "CALCULATED"
_LEDGER_SOURCE_TIER = 1
_LEDGER_CONFIDENCE = "MEDIUM"


def sync_to_metric_ledger(db: Session, company_id: str, period: str, result: dict) -> None:
    """Skips any metric whose value is currently `None` rather than writing
    a misleading zero, same rule every other ledger dual-write in this app
    follows."""
    now = datetime.now(timezone.utc)
    statement_type = result.get("statement_type") or "CONSOLIDATED"

    qoq_sales = result.get("qoq", {}).get("sales", {}).get(period)
    yoy_sales = result.get("yoy", {}).get("sales", {}).get(period)
    flag_count = len(result.get("flags", []))

    entries = {
        "qtr_analysis_qoq_sales_growth": (qoq_sales, "%"),
        "qtr_analysis_yoy_sales_growth": (yoy_sales, "%"),
        "qtr_analysis_flag_count": (float(flag_count), "count"),
    }
    for metric_key, (value, unit) in entries.items():
        if value is None:
            continue
        metric_store.insert_metric_value(
            db,
            company_id=company_id,
            metric_key=metric_key,
            period=period,
            value=float(value),
            unit=unit,
            statement_type=statement_type,
            source=_LEDGER_SOURCE,
            source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED",
            confidence=_LEDGER_CONFIDENCE,
            calculation_formula=f"quarterly_intelligence.{metric_key}",
            source_date=now,
        )
