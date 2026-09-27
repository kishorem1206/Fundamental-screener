"""Research change log — Premium PDF System, Stage B7. "What changed since
the last report" (pdf generation.md §47), built by diffing the current
FundamentalAnalysis row against the company's own immediately-prior
COMPLETED one — no new storage: every re-analysis already creates a new
row (confirmed live, 2026-09-14: Jyothy Labs already had 4 real timestamped
snapshots before this module was written), this just compares two that
already exist. Absent/None on a company's first-ever analysis — nothing to
diff against, not an error.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import FundamentalAnalysis

_SCORE_LABELS = {
    "growth": "Growth", "profitability": "Profitability", "cash_flow": "Cash Flow",
    "balance_sheet": "Balance Sheet", "efficiency": "Efficiency", "valuation": "Valuation",
}
_METRIC_WATCHLIST = (
    ("revenue_cagr_3y", "Revenue CAGR (3Y)", "%"), ("pat_margin", "PAT Margin", "%"),
    ("roce", "ROCE", "%"), ("roe", "ROE", "%"), ("debt_to_equity", "Debt/Equity", "x"),
    ("pe_ratio", "P/E", "x"),
)
_MATERIAL_SCORE_DELTA = 1.0  # points, out of 100 — below this is noise, not a real change
_MATERIAL_METRIC_DELTA_PCT = 3.0  # relative %, avoids flagging rounding-level drift


def _risk_key(risk: dict) -> str:
    return (risk.get("title") or risk.get("description") or "")[:80].strip().lower()


def build_change_log(db: Session, current: FundamentalAnalysis) -> dict | None:
    previous = (
        db.query(FundamentalAnalysis)
        .filter(
            FundamentalAnalysis.stock_id == current.stock_id,
            FundamentalAnalysis.status == "COMPLETED",
            FundamentalAnalysis.id != current.id,
            FundamentalAnalysis.completed_at.isnot(None),
        )
        .filter(FundamentalAnalysis.completed_at < (current.completed_at or current.created_at))
        .order_by(FundamentalAnalysis.completed_at.desc())
        .first()
    )
    if previous is None:
        return None

    changes: list[str] = []

    if current.overall_score is not None and previous.overall_score is not None:
        delta = float(current.overall_score) - float(previous.overall_score)
        if abs(delta) >= _MATERIAL_SCORE_DELTA:
            changes.append(f"Overall score {'improved' if delta > 0 else 'declined'} "
                            f"{previous.overall_score:.0f} → {current.overall_score:.0f}")

    cur_scores, prev_scores = current.scores or {}, previous.scores or {}
    for key, label in _SCORE_LABELS.items():
        c, p = cur_scores.get(key), prev_scores.get(key)
        if c is None or p is None:
            continue
        delta = float(c) - float(p)
        if abs(delta) >= _MATERIAL_SCORE_DELTA:
            changes.append(f"{label} score {'improved' if delta > 0 else 'declined'} {p:.0f} → {c:.0f}")

    if current.ai_rating and previous.ai_rating and current.ai_rating != previous.ai_rating:
        changes.append(f"AI rating changed: {previous.ai_rating} → {current.ai_rating}")
    if current.valuation_rating and previous.valuation_rating and current.valuation_rating != previous.valuation_rating:
        changes.append(f"Valuation view changed: {previous.valuation_rating} → {current.valuation_rating}")

    cur_metrics, prev_metrics = current.metrics or {}, previous.metrics or {}
    for key, label, unit in _METRIC_WATCHLIST:
        c, p = cur_metrics.get(key), prev_metrics.get(key)
        if c is None or p is None or p == 0:
            continue
        rel_delta_pct = abs(c - p) / abs(p) * 100
        if rel_delta_pct >= _MATERIAL_METRIC_DELTA_PCT:
            changes.append(f"{label}: {p:.1f}{unit} → {c:.1f}{unit}")

    cur_risks = {_risk_key(r): r for r in (current.risks or []) if _risk_key(r)}
    prev_risks = {_risk_key(r): r for r in (previous.risks or []) if _risk_key(r)}
    new_risks = [r.get("title") or r.get("description", "")[:80] for k, r in cur_risks.items() if k not in prev_risks]
    resolved_risks = [r.get("title") or r.get("description", "")[:80] for k, r in prev_risks.items() if k not in cur_risks]

    return {
        "previous_analysis_id": previous.id,
        "previous_completed_at": previous.completed_at.isoformat() if previous.completed_at else None,
        "changes": changes,
        "new_risks": new_risks,
        "resolved_risks": resolved_risks,
        "has_material_change": bool(changes or new_risks or resolved_risks),
    }
