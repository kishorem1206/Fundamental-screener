"""
Fundamental analysis API endpoints.
All heavy lifting runs in background tasks — HTTP responses are non-blocking.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import config
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis, AnalysisStage, Stock
from app.pipeline.orchestrator import run_analysis_pipeline, STAGES
from app.services.full_analysis_service import analysis_to_dict, get_full_analysis_dict
from app.logger import logger

router = APIRouter(prefix="/api/fundamental")


def _now():
    return datetime.now(timezone.utc)


class StartAnalysisRequest(BaseModel):
    stock_id: str


@router.post("/analyses")
def start_analysis(req: StartAnalysisRequest, background_tasks: BackgroundTasks):
    """Create a new fundamental analysis for the given stock_id."""
    db = get_db()
    try:
        # Verify stock exists
        stock = db.query(Stock).filter_by(id=req.stock_id).first()
        if stock is None:
            raise HTTPException(status_code=404, detail=f"Stock {req.stock_id} not found")

        # Check if there's already a completed analysis for this stock (return it)
        existing = (
            db.query(FundamentalAnalysis)
            .filter_by(stock_id=req.stock_id, status="COMPLETED")
            .order_by(FundamentalAnalysis.created_at.desc())
            .first()
        )

        # Generate analysis ID via PostgreSQL sequence (race-safe)
        year = datetime.now().year
        seq_val = db.execute(sa.text("SELECT nextval('fa_analysis_seq')")).scalar()
        analysis_id = f"FA-{year}-{seq_val:06d}"

        analysis = FundamentalAnalysis(
            id=analysis_id,
            stock_id=req.stock_id,
            status="QUEUED",
            overall_progress=0,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(analysis)
        db.commit()

        # Create stage records
        for stage_key, stage_label, _ in STAGES:
            db.add(AnalysisStage(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                stage_name=stage_key,
                status="PENDING",
                progress=0,
            ))
        db.commit()

        logger.info("Analysis created", analysis_id=analysis_id, stock_id=req.stock_id)

        # Start background pipeline
        background_tasks.add_task(run_analysis_pipeline, analysis_id, req.stock_id)

        return {"analysis_id": analysis_id, "status": "QUEUED"}
    finally:
        db.close()


@router.get("/analyses")
def list_analyses(limit: int = 20):
    """Return recent analyses."""
    db = get_db()
    try:
        analyses = (
            db.query(FundamentalAnalysis)
            .order_by(FundamentalAnalysis.created_at.desc())
            .limit(limit)
            .all()
        )
        return {"analyses": [analysis_to_dict(a) for a in analyses]}
    finally:
        db.close()


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    """Return full analysis data."""
    db = get_db()
    try:
        result = get_full_analysis_dict(analysis_id, db)
        if result is None:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return result
    finally:
        db.close()


@router.get("/analyses/{analysis_id}/status")
def get_status(analysis_id: str):
    """Lightweight status check for polling."""
    db = get_db()
    try:
        analysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
        if analysis is None:
            raise HTTPException(status_code=404, detail="Analysis not found")

        stock = db.query(Stock).filter_by(id=analysis.stock_id).first()
        company = None
        if stock is not None:
            company = {
                "company_name": stock.company_name, "symbol": stock.symbol, "exchange": stock.exchange,
                # Full classification hierarchy, available from the stocks table
                # immediately — before the pipeline's own identification stage runs.
                "macro_sector": stock.macro_sector, "sector": stock.sector,
                "industry": stock.industry, "basic_industry": stock.basic_industry,
            }

        stages = db.query(AnalysisStage).filter_by(analysis_id=analysis_id).all()
        stage_statuses = [
            {
                "stage_name": s.stage_name,
                "status": s.status,
                "progress": s.progress,
                "message": s.message,
                "error": s.error,
            }
            for s in stages
        ]

        return {
            "analysis_id": analysis_id,
            "company": company,
            "status": analysis.status,
            "current_stage": analysis.current_stage,
            "overall_progress": analysis.overall_progress,
            "stage_progress": analysis.stage_progress,
            "overall_score": float(analysis.overall_score) if analysis.overall_score else None,
            "confidence_score": float(analysis.confidence_score) if analysis.confidence_score else None,
            "ai_rating": analysis.ai_rating,
            "stages": stage_statuses,
            "error_message": analysis.error_message,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "report_available": analysis.report_path is not None and Path(analysis.report_path).exists(),
        }
    finally:
        db.close()


@router.post("/analyses/{analysis_id}/generate-report")
def generate_report(analysis_id: str):
    """Trigger PDF report generation (if not already done)."""
    db = get_db()
    try:
        analysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
        if analysis is None:
            raise HTTPException(status_code=404, detail="Analysis not found")
        if analysis.status != "COMPLETED":
            raise HTTPException(status_code=400, detail="Analysis not yet completed")

        if analysis.report_path and Path(analysis.report_path).exists():
            return {"report_path": analysis.report_path, "already_generated": True}

        from app.reporting.editorial_pdf_service import generate_editorial_pdf
        path = generate_editorial_pdf(analysis_id, db)
        analysis.report_path = path
        analysis.updated_at = _now()
        db.commit()

        return {"report_path": path, "generated": True}
    finally:
        db.close()


@router.get("/analyses/{analysis_id}/report")
def download_report(analysis_id: str, format: str = "pdf"):
    """Download the report. `format=pdf` (default) fetches the pre-generated
    PDF (see generate_report above — must be triggered first): a headless-
    Chromium snapshot of the Editorial Report tab itself (see
    app/reporting/editorial_pdf_service.py), so it's pixel-identical to that
    tab's colours/fonts/layout, not a separately-designed renderer.
    `format=html` is a standalone, interactive replica of the live
    dashboard (see app/reporting/html_export_service.py) — generated on
    first request (sub-second, pure DB reads + template injection, no
    subprocess) and cached at reports_dir/{analysis_id}.html thereafter, so
    unlike the PDF it needs no separate "generate" step."""
    if format not in ("pdf", "html"):
        raise HTTPException(status_code=400, detail="format must be 'pdf' or 'html'")
    db = get_db()
    try:
        analysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
        if analysis is None:
            raise HTTPException(status_code=404, detail="Analysis not found")

        company = analysis.company_info or {}

        if format == "html":
            html_path = Path(config.reports_dir).resolve() / f"{analysis_id}.html"
            if not html_path.exists():
                if analysis.status != "COMPLETED":
                    raise HTTPException(status_code=400, detail="Analysis not yet completed")
                from app.reporting.html_export_service import generate_html_export
                generate_html_export(analysis_id, db)
            filename = f"FA_{company.get('symbol', 'report')}_{analysis_id}.html"
            return FileResponse(str(html_path), media_type="text/html",
                                headers={"Content-Disposition": f'attachment; filename="{filename}"'})

        if not analysis.report_path:
            raise HTTPException(status_code=404, detail="Report not yet generated")
        path = Path(analysis.report_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        filename = f"FA_{company.get('symbol', 'report')}_{analysis_id}.pdf"
        return FileResponse(str(path), media_type="application/pdf",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    finally:
        db.close()
