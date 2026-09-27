"""Data Availability / Coverage Audit (spec §43-45) — explicitly mandatory.
Direct structural copy of `balance_sheet_intelligence/coverage.py`'s
dependency-graph pattern, this engine's own metric list. Given how much of
the spec's taxonomy turned out to be genuinely available from Screener's
schedules, this engine's coverage % should read meaningfully higher than
the Balance Sheet engine's own ~30-50%.
"""
from __future__ import annotations

from app.calculations.cash_flow_intelligence.canonical_fields import STRUCTURALLY_ABSENT

_VALID_STATUSES = {"AVAILABLE", "CALCULABLE", "PARTIAL", "MISSING_INPUT", "SOURCE_REQUIRED", "NOT_APPLICABLE", "INVALID"}

# metric -> (dependencies, present-status, missing-status)
_DEPENDENCY_GRAPH: dict[str, tuple[tuple[str, ...], str, str]] = {
    "cfo": (("cfo",), "AVAILABLE", "MISSING_INPUT"),
    "cfi": (("cfi",), "AVAILABLE", "MISSING_INPUT"),
    "cff": (("cff",), "AVAILABLE", "MISSING_INPUT"),
    "net_cash_flow": (("net_cash_flow",), "AVAILABLE", "MISSING_INPUT"),
    "free_cash_flow": (("free_cash_flow",), "AVAILABLE", "MISSING_INPUT"),
    "cfo_operating_profit_ratio": (("cfo", "operating_profit"), "CALCULABLE", "MISSING_INPUT"),
    "cfo_pat_ratio": (("cfo", "pat"), "CALCULABLE", "MISSING_INPUT"),
    "receivables_cash_impact": (("receivables_change",), "AVAILABLE", "MISSING_INPUT"),
    "inventory_cash_impact": (("inventory_change",), "AVAILABLE", "MISSING_INPUT"),
    "payables_cash_impact": (("payables_change",), "AVAILABLE", "MISSING_INPUT"),
    "taxes_paid": (("taxes_paid",), "AVAILABLE", "MISSING_INPUT"),
    "capex": (("fixed_assets_purchased",), "AVAILABLE", "MISSING_INPUT"),
    "asset_sales": (("fixed_assets_sold",), "AVAILABLE", "MISSING_INPUT"),
    "investment_purchases_sales": (("investments_purchased", "investments_sold"), "AVAILABLE", "MISSING_INPUT"),
    "interest_received": (("interest_received",), "AVAILABLE", "MISSING_INPUT"),
    "debt_raised": (("borrowings_raised",), "AVAILABLE", "MISSING_INPUT"),
    "debt_repaid": (("borrowings_repaid",), "AVAILABLE", "MISSING_INPUT"),
    "interest_paid": (("interest_paid",), "AVAILABLE", "MISSING_INPUT"),
    "dividends_paid": (("dividends_paid",), "AVAILABLE", "MISSING_INPUT"),
    "capex_to_cfo": (("fixed_assets_purchased", "cfo"), "CALCULABLE", "MISSING_INPUT"),
    "fcf_to_pat": (("free_cash_flow", "pat"), "CALCULABLE", "MISSING_INPUT"),
    "cash_bridge": (("opening_cash", "cfo", "cfi", "cff", "closing_cash"), "CALCULABLE", "PARTIAL"),
    # Always-absent items — status values below are never actually read
    # (see `_ALWAYS_ABSENT`), documented here only so the metric appears
    # in the graph at all.
    "buybacks": ((), "PARTIAL", "PARTIAL"),
    "fx_adjustment": ((), "MISSING_INPUT", "MISSING_INPUT"),
    "credit_sales_dso": ((), "MISSING_INPUT", "MISSING_INPUT"),
}

_ALWAYS_ABSENT = {
    "buybacks": "true_buyback_line",
    "fx_adjustment": "fx_adjustment",
    "credit_sales_dso": "credit_sales",
}
_ALWAYS_ABSENT_STATUS = {
    "buybacks": "PARTIAL",  # a real proxy exists (share redemption), just not a clean buyback line
    "fx_adjustment": "MISSING_INPUT",
    "credit_sales_dso": "MISSING_INPUT",
}


def compute_coverage_audit(facts: dict) -> dict:
    """`facts` is a flat {field: value_or_None} dict the orchestrator
    assembles from every source this package reads."""
    results: dict[str, dict] = {}
    for metric, (deps, present_status, missing_status) in _DEPENDENCY_GRAPH.items():
        if metric in _ALWAYS_ABSENT:
            results[metric] = {
                "status": _ALWAYS_ABSENT_STATUS[metric],
                "reason": STRUCTURALLY_ABSENT[_ALWAYS_ABSENT[metric]],
                "dependencies": list(deps),
            }
            continue

        present = [d for d in deps if facts.get(d) is not None]
        missing = [d for d in deps if facts.get(d) is None]

        if not missing:
            status, reason = present_status, None
        elif present:
            status, reason = "PARTIAL", f"Missing: {', '.join(missing)}"
        else:
            status, reason = missing_status, f"Missing: {', '.join(missing)}"

        results[metric] = {"status": status, "reason": reason, "dependencies": list(deps)}

    summary = {status: 0 for status in _VALID_STATUSES}
    for r in results.values():
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    total = len(results)
    available_like = summary.get("AVAILABLE", 0) + summary.get("CALCULABLE", 0)
    coverage_pct = round(available_like / total * 100, 1) if total else 0.0

    return {"metrics": results, "summary": summary, "coverage_pct": coverage_pct, "total_metrics": total}


_GAP_PRIORITY = {"fx_adjustment": "HIGH", "credit_sales_dso": "MEDIUM", "buybacks": "MEDIUM"}


def top_source_gaps(coverage: dict) -> list[dict]:
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    gaps = [
        {"metric": metric, "status": r["status"], "reason": r["reason"], "priority": _GAP_PRIORITY.get(metric, "LOW")}
        for metric, r in coverage["metrics"].items()
        if r["status"] in ("MISSING_INPUT", "SOURCE_REQUIRED", "PARTIAL")
    ]
    return sorted(gaps, key=lambda g: order.get(g["priority"], 3))
