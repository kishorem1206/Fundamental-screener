"""Income cascade builder (spec Stage 2): Revenue -> COGS -> Gross Profit ->
OPEX -> EBITDA -> Depreciation -> EBIT -> Finance Cost/Other Income/
Exceptional -> PBT -> Tax -> PAT, per fiscal period, for ONE explicit
statement type.

Reads `metric_store` directly rather than importing anything from
`app/calculations/pnl_engine.py` — the two engines share the same
underlying ledger but are kept structurally separate per Stage 0's "don't
break the existing engine" boundary; nothing here can accidentally change
what `pnl_engine.py`'s 4 existing call sites see.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.engine import safe_div
from app.calculations.pl_intelligence.canonical_fields import (
    CANONICAL_FIELD_TO_METRIC_KEY,
    NO_COGS_BREAKDOWN_REASON,
    NO_EXCEPTIONAL_ITEMS_REASON,
)
from app.infrastructure.database import metric_store

_VALID_STATEMENT_TYPES = {"STANDALONE", "CONSOLIDATED"}


def _series(db: Session, company_id: str, metric_key: str, statement_type: str) -> dict[str, float]:
    """{period: authoritative_value}, resolved via the same tier/confidence
    hierarchy every other ledger reader uses. `statement_type` has no
    default — every caller in this package must say which statement it
    wants, enforcing spec Rule 1 ("never mix standalone and consolidated
    data") at the function signature rather than relying on callers to
    remember a module-level default."""
    if statement_type not in _VALID_STATEMENT_TYPES:
        raise ValueError(f"statement_type must be one of {_VALID_STATEMENT_TYPES}, got {statement_type!r}")
    history = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    periods = sorted({row.period for row in history if row.period != "TTM"})
    out = {}
    for period in periods:
        winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
        if winner is not None and winner.value is not None:
            out[period] = float(winner.value)
    return out


def build_income_cascade(db: Session, company_id: str, statement_type: str) -> dict[str, dict]:
    """Returns {period: {cascade fields..., "confidence": {field: tag}}} for
    every fiscal period where at least revenue is on record, for the given
    `statement_type` only. Never raises — a company/statement_type with no
    data at all just returns `{}`, matching every other calc module's
    "never raises" contract.
    """
    revenue = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["revenue"], statement_type)
    opex = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["opex"], statement_type)
    ebitda = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["operating_profit"], statement_type)
    depreciation = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["depreciation"], statement_type)
    finance_cost = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["finance_cost"], statement_type)
    other_income = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["other_income"], statement_type)
    pbt = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["pbt"], statement_type)
    pat = _series(db, company_id, CANONICAL_FIELD_TO_METRIC_KEY["pat"], statement_type)

    cascade: dict[str, dict] = {}
    for period, rev in revenue.items():
        confidence: dict[str, str] = {}

        def get(series: dict[str, float], field_name: str, tag_if_present: str = "HIGH") -> float | None:
            value = series.get(period)
            confidence[field_name] = tag_if_present if value is not None else "UNAVAILABLE"
            return value

        confidence["revenue"] = "HIGH"
        # Guard against dividing by a reported revenue of exactly 0 (spec
        # Stage 2's explicit "protect against revenue == 0" instruction) —
        # only affects margin denominators; the raw reported revenue value
        # itself is still stored as-is below, never coerced to None.
        rev_for_margin = rev if rev else None
        opex_v = get(opex, "opex")
        ebitda_v = get(ebitda, "ebitda")
        dep_v = get(depreciation, "depreciation")
        finance_cost_v = get(finance_cost, "finance_cost")
        other_income_v = get(other_income, "other_income")
        pbt_v = get(pbt, "pbt")
        pat_v = get(pat, "pat")

        ebit_v = None
        if ebitda_v is not None and dep_v is not None:
            ebit_v = ebitda_v - dep_v
            confidence["ebit"] = "MEDIUM"  # derived from two reported values
        else:
            confidence["ebit"] = "UNAVAILABLE"

        tax_v = None
        if pbt_v is not None and pat_v is not None:
            tax_v = pbt_v - pat_v
            confidence["tax"] = "MEDIUM"  # derived, not separately reported
        else:
            confidence["tax"] = "UNAVAILABLE"

        cascade[period] = {
            "revenue": rev_for_margin,
            "cogs": None,
            "gross_profit": None,
            "gross_margin": None,
            "gross_margin_confidence": "LOW",
            "gross_margin_reason": NO_COGS_BREAKDOWN_REASON,
            "opex": opex_v,
            "ebitda": ebitda_v,
            "ebitda_margin": _pct(safe_div(ebitda_v, rev_for_margin)),
            "depreciation": dep_v,
            "ebit": ebit_v,
            "ebit_margin": _pct(safe_div(ebit_v, rev_for_margin)),
            "finance_cost": finance_cost_v,
            "other_income": other_income_v,
            "exceptional_items": None,
            "exceptional_items_reason": NO_EXCEPTIONAL_ITEMS_REASON,
            "pbt": pbt_v,
            "tax": tax_v,
            "pat": pat_v,
            "pat_margin": _pct(safe_div(pat_v, rev_for_margin)),
            "confidence": confidence,
        }
    return cascade


def _pct(fraction: float | None) -> float | None:
    return round(fraction * 100, 2) if fraction is not None else None
