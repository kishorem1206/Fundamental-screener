"""Dual-writes the screenable Cash Flow Intelligence metrics into the
existing `fa_metric_data_points` ledger — full screener-filter support for
free through the existing declarative `rules.yaml`/`app/screening/engine.py`
mechanism, mirroring `balance_sheet_intelligence/persistence.py::sync_to_metric_ledger()`
exactly (no equivalent of `pl_intelligence`'s `save_pl_score()` half here —
this package has no persisted score table either, same reasoning as
`balance_sheet_intelligence`'s own docstring).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store

_LEDGER_SOURCE = "CALCULATED"
_LEDGER_SOURCE_TIER = 1
_LEDGER_CONFIDENCE = "MEDIUM"
# Same rationale as balance_sheet_intelligence/persistence.py: writing under
# STANDALONE is the only way these are discoverable through the existing
# screener mechanism, regardless of which statement_type this engine's own
# computation actually used for `result`.
_LEDGER_STATEMENT_TYPE = "STANDALONE"

_LEDGER_METRICS: dict[str, tuple[str, ...]] = {
    "cf_conversion_ratio_pct": ("conversion", "latest", "ratio_pct"),
    "cf_cumulative_3y_conversion_pct": ("conversion", "cumulative_3y", "cumulative_cfo_to_operating_profit_pct"),
    "cf_capex_to_cfo_pct": ("investing", "breakdown", "fixed_assets_purchased"),  # overwritten below with the real ratio
    "cf_dividend_to_cfo_pct": ("financing", "dividend_analysis", "dividend_to_cfo_pct"),
    "cf_dividend_to_fcf_pct": ("financing", "dividend_analysis", "dividend_to_fcf_pct"),
    "cf_coverage_pct": ("coverage", "coverage_pct"),
}

_LEDGER_UNITS: dict[str, str] = {
    "cf_conversion_ratio_pct": "%", "cf_cumulative_3y_conversion_pct": "%",
    "cf_capex_to_cfo_pct": "%", "cf_dividend_to_cfo_pct": "%", "cf_dividend_to_fcf_pct": "%",
    "cf_coverage_pct": "%",
}

_VOLATILITY_SCORE = {"STABLE_CFO": 3, "DECLINING_CFO": 1, "VOLATILE_CFO": 1, "NEGATIVE_CFO_PATTERN": 0, "INSUFFICIENT_DATA": None}
_ARCHETYPE_SCORE = {
    "CASH_COMPOUNDER": 3, "CASH_HARVEST": 3, "GROWTH_REINVESTMENT": 2,
    "ASSET_LIQUIDATION_SUPPORTED": 1, "WORKING_CAPITAL_TRAP": 1, "DEBT_FUNDED_BUSINESS": 0, "MIXED": None,
}
# Debt financing classification (spec §25, GROSS raised vs. repaid — the
# whole reason this engine's schedules API beats yfinance for financing
# analysis) as a numeric proxy for >=/<= screener filters.
_DEBT_CLASSIFICATION_SCORE = {"NET_DELEVERAGING": 2, "NEUTRAL": 1, "NET_BORROWING": 0}


def _dig(d: dict, path: tuple[str, ...]):
    for key in path:
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d


def sync_to_metric_ledger(db: Session, company_id: str, period: str, result: dict) -> None:
    """Skips any metric whose value is currently `None` rather than writing
    a misleading zero — same discipline as every other `sync_to_metric_ledger`
    in this codebase."""
    now = datetime.now(timezone.utc)

    for metric_key, path in _LEDGER_METRICS.items():
        formula = f"cash_flow_intelligence.{'.'.join(path)}"
        if metric_key == "cf_capex_to_cfo_pct":
            capex = _dig(result, ("investing", "breakdown", "fixed_assets_purchased"))
            cfo = _dig(result, ("reconciliation", "cfo_bridge", "computed_cfo"))
            value = round(abs(capex) / cfo * 100, 2) if capex is not None and cfo else None
            formula = "cash_flow_intelligence.investing.breakdown.fixed_assets_purchased / reconciliation.cfo_bridge.computed_cfo"
        else:
            value = _dig(result, path)
        if value is None:
            continue
        metric_store.insert_metric_value(
            db, company_id=company_id, metric_key=metric_key, period=period,
            value=float(value), unit=_LEDGER_UNITS[metric_key], statement_type=_LEDGER_STATEMENT_TYPE,
            source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
            calculation_formula=formula,
            source_date=now,
        )

    volatility_classification = (result.get("volatility") or {}).get("classification")
    volatility_score = _VOLATILITY_SCORE.get(volatility_classification)
    if volatility_score is not None:
        metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="cf_volatility_score", period=period,
            value=float(volatility_score), unit="score", statement_type=_LEDGER_STATEMENT_TYPE,
            source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
            calculation_formula=f"cash_flow_intelligence.volatility.classification={volatility_classification}",
            source_date=now,
        )

    archetype_classification = (result.get("archetype") or {}).get("classification")
    archetype_score = _ARCHETYPE_SCORE.get(archetype_classification)
    if archetype_score is not None:
        metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="cf_archetype_score", period=period,
            value=float(archetype_score), unit="score", statement_type=_LEDGER_STATEMENT_TYPE,
            source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
            calculation_formula=f"cash_flow_intelligence.archetype.classification={archetype_classification}",
            source_date=now,
        )

    debt_classification = (_dig(result, ("financing", "debt_financing")) or {}).get("classification")
    debt_classification_score = _DEBT_CLASSIFICATION_SCORE.get(debt_classification)
    if debt_classification_score is not None:
        metric_store.insert_metric_value(
            db, company_id=company_id, metric_key="cf_debt_classification_score", period=period,
            value=float(debt_classification_score), unit="score", statement_type=_LEDGER_STATEMENT_TYPE,
            source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
            reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
            calculation_formula=f"cash_flow_intelligence.financing.debt_financing.classification={debt_classification} "
                                 f"(from GROSS borrowings_raised/borrowings_repaid, Screener schedules)",
            source_date=now,
        )

    triggered_count = sum(1 for f in (result.get("risk_flags") or []) if f.get("status") == "TRIGGERED")
    metric_store.insert_metric_value(
        db, company_id=company_id, metric_key="cf_red_flag_count", period=period,
        value=float(triggered_count), unit="count", statement_type=_LEDGER_STATEMENT_TYPE,
        source=_LEDGER_SOURCE, source_tier=_LEDGER_SOURCE_TIER,
        reported_or_calculated="CALCULATED", confidence=_LEDGER_CONFIDENCE,
        calculation_formula="cash_flow_intelligence.risk_flags, count of status==TRIGGERED",
        source_date=now,
    )
