"""Generates the PDF report via the Node/PDFKit renderer at `pdf-renderer/`
(ported from the user's Replit "equity-pdf-renderer" project, 2026-09-15),
replacing both of this app's previous PDF paths — the ReportLab "Mindful
Finance" renderer (`report_service.py`) and the banking Jinja/Playwright
path (`html_report_service.py` + `pdf_report_service.py`). One renderer for
every sector now; those older files are left on disk, unused, rather than
deleted (~2,600 lines of previously-verified work, not asked to be removed).

The renderer itself is real TypeScript run via a Node subprocess (`tsx
cli.ts`), not reimplemented in Python — that's what guarantees the output is
provably the same code that produced the user's reference sample, not a
close approximation in a different rendering engine.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from app.config import config
from app.logger import logger

_PDF_RENDERER_DIR = Path(__file__).resolve().parent.parent.parent.parent / "pdf-renderer"


def generate_pdf_report(analysis_id: str, db) -> str:
    """Build the EquityReport JSON for this analysis and render it via the
    Node subprocess. Returns the output PDF's file path."""
    from app.infrastructure.database.models import FundamentalAnalysis

    analysis: FundamentalAnalysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
    if analysis is None:
        raise ValueError(f"Analysis {analysis_id} not found")

    company_info = analysis.company_info or {}
    company_id = company_info.get("stock_id") or analysis.stock_id
    sector_analysis = analysis.sector_analysis or {}

    from app.reporting.premium_report_data import build_premium_extras
    extras = build_premium_extras(db, company_id, analysis) if company_id else {}

    from app.calculations.pnl_engine import compute_pnl_analysis
    pnl = compute_pnl_analysis(
        db, company_id, sector_name=sector_analysis.get("sector_name")
    ) if company_id else {}

    # P&L Analysis Engine ("P&L Intelligence") — a separate, additive
    # computation alongside the older `pnl` above (Stage 0 boundary; see
    # app/calculations/pl_intelligence/'s package docstring). Folded into
    # this SAME combined PDF as new pages, per the user's own choice, not a
    # second standalone document.
    from app.calculations.pl_intelligence import compute_pl_intelligence
    pl_intelligence = compute_pl_intelligence(
        db, company_id, sector_name=sector_analysis.get("sector_name")
    ) if company_id else {}

    # Balance Sheet Analysis Engine — a separate, additive computation
    # alongside pnl/pl_intelligence above (see app/calculations/
    # balance_sheet_intelligence/'s package docstring). Blends Screener.in
    # with the yfinance-sourced `analysis.metrics` (already computed by the
    # pipeline's ratio_calculations stage) for working-capital ratios.
    from app.calculations.balance_sheet_intelligence import compute_balance_sheet_intelligence
    balance_sheet_intelligence = compute_balance_sheet_intelligence(
        db, company_id, sector_name=sector_analysis.get("sector_name"), yfinance_metrics=analysis.metrics or {},
    ) if company_id else {}

    # Cash Flow Analysis Engine — a separate, additive computation alongside
    # the three above (see app/calculations/cash_flow_intelligence/'s
    # package docstring). Primary-sourced from Screener.in's undocumented
    # "schedules" API; reuses balance_sheet_intelligence's own
    # working_capital DSO/DIO/DPO series (just computed above) rather than
    # recomputing.
    from app.calculations.cash_flow_intelligence import compute_cash_flow_intelligence
    cash_flow_intelligence = compute_cash_flow_intelligence(
        db, company_id, sector_name=sector_analysis.get("sector_name"), yfinance_metrics=analysis.metrics or {},
        balance_sheet_intelligence_result=balance_sheet_intelligence,
    ) if company_id else {}

    # Sector-specific operating KPIs (NSE filings) and, for lenders, the ROE/P-B
    # analysis — additive sections; both are None when not applicable.
    from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
    from app.routes.bank_roe import bank_roe_for_stock
    from app.infrastructure.database.models import Stock
    sector_kpis = compute_quarterly_sector_kpis(db, company_id, sector_analysis.get("sector_name")) if company_id else None
    stock_row = db.query(Stock).filter_by(id=company_id).first() if company_id else None
    bank_roe = bank_roe_for_stock(db, stock_row) if stock_row is not None else None

    from app.reporting.equity_report_mapper import build_equity_report
    report = build_equity_report(db, analysis, extras, pnl, pl_intelligence, balance_sheet_intelligence, cash_flow_intelligence,
                                 sector_kpis=sector_kpis, bank_roe=bank_roe)

    # Absolute paths: the subprocess below runs with cwd=pdf-renderer/, so a
    # relative reports_dir (this app's default is "./reports") would resolve
    # against the wrong directory and silently write into pdf-renderer/reports/.
    reports_dir = Path(config.reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / f"{analysis_id}.pdf"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=reports_dir
    ) as f:
        json.dump(report, f, default=str)
        input_path = Path(f.name)

    try:
        result = subprocess.run(
            ["npx", "tsx", "cli.ts", str(input_path), str(pdf_path)],
            cwd=str(_PDF_RENDERER_DIR),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            logger.error(
                "equity PDF render failed", analysis_id=analysis_id,
                stderr=result.stderr, stdout=result.stdout,
            )
            raise RuntimeError(f"PDF render failed for {analysis_id}: {result.stderr.strip()}")
    finally:
        input_path.unlink(missing_ok=True)

    logger.info("Equity PDF report generated", analysis_id=analysis_id, path=str(pdf_path))
    return str(pdf_path)
