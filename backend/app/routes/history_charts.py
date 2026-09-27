"""Long-history trend data — read-only, frontend-facing (2026-09-15).

User feedback on the single-year P&L bridge chart: "What are you trying to
convey here? I need something meaningful insights like these" (referencing
Screener.in's own long-history Sales+Margin%, P/E+EPS overlay charts,
spanning up to 20 years with a time-range selector). The bridge chart
itself wasn't actually broken (verified: its floating delta bars are
computed and rendered correctly, confirmed against the live SVG's own
coordinates) — a one-year snapshot just isn't the same kind of insight as a
long trend, and this app already has the underlying data for two of
Screener's own reference charts:

- Sales & Margins: `pnl_engine.py`'s 12-year+TTM consolidated table
  (already computed for the PDF's P&L Analysis section, never exposed to
  the frontend as JSON until now).
- P/E & EPS: `ValuationHistory` (Architecture v2 Stage 4 — real historical
  price/EPS-derived P/E per fiscal year, also PDF-only until now).
"""
from __future__ import annotations

from fastapi import APIRouter

from app.calculations.pnl_engine import compute_pnl_analysis
from app.infrastructure.database import metric_store
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis, ValuationHistory

router = APIRouter(prefix="/api/history-charts")


def _screener_ratio_series(db, company_id: str, metric_key: str) -> dict[str, float]:
    """{period: value} for a bs_ratio_* metric, across every fiscal year
    on record — not just the latest. Prefers CONSOLIDATED, falls back to
    STANDALONE when a company genuinely has only one (matching this
    codebase's now-standard convention). Added 2026-09-22 alongside
    `ingest_ratios()`'s fix to stop discarding every year but the latest —
    see that function's docstring (screener_client.py) for the full story."""
    out: dict[str, float] = {}
    for statement_type in ("CONSOLIDATED", "STANDALONE"):
        history = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
        periods = sorted({row.period for row in history if row.period != "TTM"})
        for period in periods:
            winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
            if winner is not None and winner.value is not None:
                out[period] = float(winner.value)
        if out:
            return out
    return out


@router.get("/{company_id:path}")
def get_history_charts(company_id: str):
    db = get_db()
    try:
        analysis = (
            db.query(FundamentalAnalysis)
            .filter_by(stock_id=company_id, status="COMPLETED")
            .order_by(FundamentalAnalysis.completed_at.desc())
            .first()
        )
        sector_name = (analysis.sector_analysis or {}).get("sector_name") if analysis else None
        pnl = compute_pnl_analysis(db, company_id, sector_name=sector_name)
        table = pnl.get("table") or {}
        fiscal_years = pnl.get("fiscal_years") or []

        def _npm(y: str) -> float | None:
            # Net Profit Margin = net_profit / sales — both already on the
            # same 12-year consolidated table, so this is a real ratio, not
            # an estimate. Gross Profit Margin is NOT included here: Screener's
            # P&L view (openscreener's profit_loss()) only exposes one
            # aggregate "expenses" line — no material-cost/COGS breakdown —
            # confirmed 2026-09-15 checking the raw scraped fields directly.
            # Faking a GPM from aggregate expenses would silently misreport
            # it as gross margin when it's actually closer to operating
            # margin's complement; left out rather than shown wrong.
            sales, net_profit = (table.get("sales") or {}).get(y), (table.get("net_profit") or {}).get(y)
            if sales is None or net_profit is None or sales == 0:
                return None
            return round(net_profit / sales * 100, 2)

        sales_and_margins = [
            {
                "period": y,
                "sales": (table.get("sales") or {}).get(y),
                "opm": (table.get("opm") or {}).get(y),
                "npm": _npm(y),
                "net_profit": (table.get("net_profit") or {}).get(y),
            }
            for y in fiscal_years
        ]

        val_rows = (
            db.query(ValuationHistory)
            .filter_by(company_id=company_id)
            .order_by(ValuationHistory.period_end.asc())
            .all()
        )
        valuation = [
            {
                "period": r.period_end,
                "eps": float(r.eps) if r.eps is not None else None,
                "pe": float(r.pe) if r.pe is not None else None,
                "pb": float(r.pb) if r.pb is not None else None,
            }
            for r in val_rows
        ]

        roce_series = _screener_ratio_series(db, company_id, "bs_ratio_roce_percent")
        roce_history = [{"period": p, "roce": v} for p, v in sorted(roce_series.items())]

        return {
            "company_id": company_id,
            "sales_and_margins": sales_and_margins,
            "valuation": valuation,
            "roce_history": roce_history,
        }
    finally:
        db.close()
