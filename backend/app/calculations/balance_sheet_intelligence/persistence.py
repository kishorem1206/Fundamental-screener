"""Dual-writes the screenable Balance Sheet Intelligence metrics into the
existing `fa_metric_data_points` ledger — gets full screener-filter support
for free through the existing declarative `rules.yaml`/
`app/screening/engine.py` mechanism, mirroring
`pl_intelligence/persistence.py::sync_to_metric_ledger()` exactly (this
package has no equivalent of that module's `save_pl_score()` half — see
this package's `__init__.py` docstring for why no new tables exist here).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store

_LEDGER_SOURCE = "CALCULATED"
_LEDGER_SOURCE_TIER = 1
_LEDGER_CONFIDENCE = "MEDIUM"
# Same rationale as pl_intelligence/persistence.py: `_resolve_metric_value()`
# reads `statement_type=DEFAULT_STATEMENT_TYPE` ("STANDALONE") unless a
# screener rule overrides it, and none do — writing here under STANDALONE
# is the only way these metrics are actually discoverable through the
# existing screener mechanism, regardless of which statement_type this
# engine's own computation used for `result`.
_LEDGER_STATEMENT_TYPE = "STANDALONE"

# metric_key -> path into `result` (dot-separated) for the screener-filter
# dual-write. Registered in app/metrics/registry.py under the same ids.
_LEDGER_METRICS: dict[str, tuple[str, ...]] = {
    "bs_debt_to_equity": ("derived_metrics", "debt_to_equity"),
    "bs_liabilities_to_equity": ("derived_metrics", "liabilities_to_equity"),
    "bs_net_debt_to_ebitda": ("derived_metrics", "net_debt_to_ebitda"),
    "bs_roce": ("derived_metrics", "roce"),
    "bs_ccc": ("working_capital", "ccc_latest"),
    "bs_current_ratio": ("working_capital", "current_ratio_latest"),
    "bs_quick_ratio": ("working_capital", "quick_ratio_latest"),
    "bs_cash_ratio": ("working_capital", "cash_ratio_latest"),
    "bs_coverage_pct": ("coverage", "coverage_pct"),
}

_LEDGER_UNITS: dict[str, str] = {
    "bs_debt_to_equity": "x", "bs_liabilities_to_equity": "x", "bs_net_debt_to_ebitda": "x",
    "bs_roce": "%", "bs_ccc": "days", "bs_current_ratio": "x", "bs_quick_ratio": "x",
    "bs_cash_ratio": "x", "bs_coverage_pct": "%",
}

# STRONG/TRANSFORMING/MIDDLE/WEAK as a numeric proxy so `>=`/`<=` screener
# filters work on it — the categorical label itself stays in the JSON
# output (`result["archetype"]["classification"]`), never only the number.
_ARCHETYPE_SCORE = {"STRONG": 3, "TRANSFORMING": 2, "MIDDLE": 1, "WEAK": 0}


def _dig(d: dict, path: tuple[str, ...]):
    for key in path:
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d


def sync_to_metric_ledger(db: Session, company_id: str, period: str, result: dict) -> None:
    """Skips any metric whose value is currently `None` rather than writing
    a misleading zero — same discipline as `pl_intelligence`'s equivalent."""
    now = datetime.now(timezone.utc)
    for metric_key, path in _LEDGER_METRICS.items():
        value = _dig(result, path)
        if value is None:
            continue
        metric_store.insert_metric_value(
            db, company_id=company_id, metric_key=metric_key, period=period,
            value=float(value), unit=_LEDGER_UNITS[metric_key], statement_type=_LEDGER_STATEMENT_TYPE,
            source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
            calculation_formula=f"balance_sheet_intelligence.{'.'.join(path)}, ruleset={(result.get('archetype') or {}).get('ruleset_version')}",
            source_date=now,
        )

    archetype_classification = (result.get("archetype") or {}).get("classification")
    archetype_score = _ARCHETYPE_SCORE.get(archetype_classification)
    if archetype_score is not None:
        metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="bs_archetype_score", period=period,
            value=float(archetype_score), unit="score", statement_type=_LEDGER_STATEMENT_TYPE,
            source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
            calculation_formula=f"balance_sheet_intelligence.archetype.classification={archetype_classification}",
            source_date=now,
        )

    triggered_count = sum(1 for f in (result.get("risk_flags") or []) if f.get("status") == "TRIGGERED")
    metric_store.insert_metric_value(
        db, company_id=company_id, metric_key="bs_red_flag_count", period=period,
        value=float(triggered_count), unit="count", statement_type=_LEDGER_STATEMENT_TYPE,
        source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
        reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
        calculation_formula="balance_sheet_intelligence.risk_flags, count of status==TRIGGERED",
        source_date=now,
    )
