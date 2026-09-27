"""Bridges the DB-backed banking metric ledger (app/infrastructure/database/
metric_store.py) into the sector-framework `financial_data` dict, without
touching the SectorFramework base-class contract shared by all 34 sectors.
Only BankingSector reads the key this writes.
"""
from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store

BRIDGE_KEY = "_banking_authoritative_metrics"

_METRIC_KEYS = [
    "capital_adequacy_ratio", "gross_npa", "net_npa", "provision_coverage_ratio",
    "casa_ratio", "credit_cost", "cost_to_income_ratio", "slippage_ratio", "nim", "roa",
]

# LOW-confidence rows (single-quarter DERIVED/ESTIMATED approximations from OCR'd
# figures) stay visible via the provenance history endpoint but are excluded from
# the deterministic score — banking.md's missing-data policy says N/A never
# becomes 0, and an unreliable estimate shouldn't silently outrank a real N/A.
_SCORABLE_CONFIDENCE = {"HIGH", "MEDIUM"}


def _latest_quarterly_pat_cr(db: Session, company_id: str) -> float | None:
    """Latest quarter's net profit (INR cr) from the Screener-sourced quarterly
    ledger, STANDALONE first (a bank's own earnings), else CONSOLIDATED.
    Feeds the run-rate ROE the ROE-simulator method is built on."""
    for st in ("STANDALONE", "CONSOLIDATED"):
        hist = metric_store.get_metric_history(db, company_id, "qtr_net_profit", statement_type=st)
        periods = sorted({r.period for r in hist if r.period != "TTM"})
        if periods:
            winner, _ = metric_store.get_authoritative_value(db, company_id, "qtr_net_profit", periods[-1], statement_type=st)
            if winner is not None:
                return float(winner.value)
    return None


def build_banking_bridge(db: Session, company_id: str) -> dict[str, float]:
    values = {}
    qpat = _latest_quarterly_pat_cr(db, company_id)
    if qpat is not None:
        values["bank_latest_qtr_pat_cr"] = qpat
    for metric_key in _METRIC_KEYS:
        row = metric_store.get_latest_period_value(db, company_id, metric_key)
        if row is not None and row.confidence in _SCORABLE_CONFIDENCE:
            values[metric_key] = float(row.value)
    return values


def inject_banking_bridge(financial_data: dict, db: Session, company_id: str) -> dict:
    financial_data[BRIDGE_KEY] = build_banking_bridge(db, company_id)
    return financial_data
