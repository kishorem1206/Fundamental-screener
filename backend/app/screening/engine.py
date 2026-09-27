"""Declarative screening engine — Architecture v2 Stage 2.

Evaluates a named rule set (app/screening/rules.yaml) against every active
stock the app can resolve a sector and look up metrics for. Deliberately a
SEPARATE engine from the deep single-stock Analysis pipeline
(app/pipeline/orchestrator.py) — per Architecture v2 chatgpt.md section 22's
screening-vs-analysis distinction: screening answers "does this stock pass
my declared thresholds," fast and bulk; analysis answers "is this stock
fundamentally attractive," slow and narrative.

Sector filtering uses the SAME resolution the rest of the app already uses
(app.sectors.registry.get_framework() against the `stocks` table's own
sector/industry/basic_industry columns) — not fa_stock_classification's
Screener-sourced taxonomy, which uses different category names and exists
for a different feature (the taxonomy browser in this same routes module).

Each rule's metric value is resolved from two places, in order:
  1. fa_bulk_metrics (compute_metrics() output — generic yfinance-derived
     ratios: ROE, P/E, revenue CAGR, etc.)
  2. the provenance ledger (metric_store.get_latest_period_value) — for
     banking-specific/operational metrics that are never in fa_bulk_metrics
     because they don't come from yfinance at all (GNPA, CASA, CRAR, ...).
A metric found in neither source makes that rule — and the stock's overall
result — INSUFFICIENT_DATA, never a silent FAIL, per banking.md's own
missing-data policy.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import BulkMetrics, Stock
from app.metrics.registry import METRIC_REGISTRY
from app.sectors.base import _eval_condition
from app.sectors.registry import get_framework

_RULES_PATH = Path(__file__).resolve().parent / "rules.yaml"
_VALID_OPERATORS = {"<", ">", "<=", ">=", "==", "!="}


def _load_rule_sets() -> dict:
    with open(_RULES_PATH) as f:
        rule_sets = yaml.safe_load(f) or {}
    for name, spec in rule_sets.items():
        for rule in spec.get("rules", []):
            metric_id = rule["metric"]
            if metric_id not in METRIC_REGISTRY:
                raise ValueError(
                    f"Screening rule set '{name}' references unknown metric_id "
                    f"'{metric_id}' — not in app/metrics/registry.py"
                )
            if rule["operator"] not in _VALID_OPERATORS:
                raise ValueError(
                    f"Screening rule set '{name}' uses unsupported operator "
                    f"'{rule['operator']}' for metric '{metric_id}'"
                )
    return rule_sets


def list_rule_sets() -> dict:
    """{name: {label, description, sector, rule_count}} for every loaded rule set."""
    rule_sets = _load_rule_sets()
    return {
        name: {
            "label": spec.get("label", name),
            "description": (spec.get("description") or "").strip(),
            "sector": spec.get("sector"),
            "rules": spec.get("rules", []),
        }
        for name, spec in rule_sets.items()
    }


def _resolve_metric_value(db: Session, stock_id: str, metric_id: str, bulk_metrics: dict | None) -> float | None:
    if bulk_metrics and bulk_metrics.get(metric_id) is not None:
        return bulk_metrics[metric_id]
    row = metric_store.get_latest_period_value(db, stock_id, metric_id)
    return float(row.value) if row is not None else None


def evaluate_rule_set(db: Session, name: str, limit: int = 2000) -> dict:
    """Run one rule set against every stock it applies to. Returns
    {rule_set: {...}, results: [{symbol, company_name, sector, status,
    rule_results: [...]}]}, sorted PASS first, then FAIL, then
    INSUFFICIENT_DATA, each group by company_name."""
    rule_sets = _load_rule_sets()
    spec = rule_sets.get(name)
    if spec is None:
        return {"error": f"Unknown rule set '{name}'. Known: {sorted(rule_sets)}"}

    target_sector = spec.get("sector")
    rules = spec.get("rules", [])

    bulk_by_stock = {
        row.stock_id: row.metrics
        for row in db.query(BulkMetrics.stock_id, BulkMetrics.metrics).all()
    }

    stocks = db.query(Stock).filter(Stock.is_active == True).order_by(Stock.company_name).all()

    results = []
    for stock in stocks:
        framework = get_framework(stock.sector or "", industry=stock.industry, basic_industry=stock.basic_industry)
        sector_name = framework.sector_name
        if target_sector and sector_name != target_sector:
            continue

        bulk_metrics = bulk_by_stock.get(stock.id)
        rule_results = []
        for rule in rules:
            metric_id, operator, threshold = rule["metric"], rule["operator"], rule["value"]
            value = _resolve_metric_value(db, stock.id, metric_id, bulk_metrics)
            if value is None:
                passed = None
            else:
                passed = _eval_condition(f"__v {operator} {threshold}", {"__v": value})
            rule_results.append({
                "metric": metric_id, "operator": operator, "threshold": threshold,
                "value": value, "passed": passed,
            })

        if any(r["passed"] is None for r in rule_results):
            status = "INSUFFICIENT_DATA"
        elif all(r["passed"] for r in rule_results):
            status = "PASS"
        else:
            status = "FAIL"

        results.append({
            "stock_id": stock.id, "symbol": stock.symbol, "company_name": stock.company_name,
            "sector": sector_name, "status": status, "rule_results": rule_results,
        })
        if len(results) >= limit:
            break

    order = {"PASS": 0, "FAIL": 1, "INSUFFICIENT_DATA": 2}
    results.sort(key=lambda r: (order[r["status"]], r["company_name"]))

    counts = {"PASS": 0, "FAIL": 0, "INSUFFICIENT_DATA": 0}
    for r in results:
        counts[r["status"]] += 1

    return {
        "rule_set": name, "label": spec.get("label", name),
        "sector_filter": target_sector, "counts": counts, "results": results,
    }
