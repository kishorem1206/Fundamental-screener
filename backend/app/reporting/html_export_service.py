"""Builds the standalone "Download HTML" export — an interactive replica of
the live dashboard (same React app, same tab-switching, same Recharts
tooltips), not a re-implementation like the PDF/banking-report paths.

Mechanism: `frontend/export.html` is a second Vite build of the exact same
`frontend/src/` code (via `npm run build:export`, see package.json),
inlined into one offline-capable file by `vite-plugin-singlefile`, with two
placeholder tokens where the analysis data would normally come from a live
`fetch()`. This module fills those placeholders in for one specific
analysis: it calls, in-process, every backend function the dashboard's 11
data-fetching section components call over the network (confirmed by
reading api.ts + every section component), keyed by the exact request path
`api.ts`'s `req()` uses — see `frontend/src/api.ts` and
`app/routes/fundamental.py`'s `download_report`.

The pre-built template lives at
`app/reporting/templates/export_dashboard_template.html` and must be
regenerated (`npm run build:export` in `frontend/`) after any change to
`AnalysisDashboard.tsx` or its section/chart components — see HOW_TO_RUN.md.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import config
from app.logger import logger
from app.services.full_analysis_service import get_full_analysis_dict

_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "export_dashboard_template.html"
_ANALYSIS_TOKEN = '"__FUNDAMENTAL_SCREENER_EXPORT_ANALYSIS_JSON__"'
_BUNDLE_TOKEN = '"__FUNDAMENTAL_SCREENER_EXPORT_BUNDLE_JSON__"'


def _safe(fn, *args):
    """Best-effort call: on any exception, log and omit the key entirely —
    req()'s embedded-lookup then rejects for that path exactly like a failed
    fetch() would, and every section's own error/empty-state handling
    already covers that (same fallback as a live 404/500 today)."""
    try:
        return fn(*args)
    except Exception:
        logger.warning("html export: endpoint failed, omitting from bundle",
                        fn=getattr(fn, "__name__", str(fn)), args=args)
        return None


def build_export_bundle(analysis_id: str, db) -> tuple[dict, dict]:
    """Returns (full_analysis_dict, bundle_dict). Raises ValueError if the
    analysis doesn't exist."""
    full_analysis = get_full_analysis_dict(analysis_id, db)
    if full_analysis is None:
        raise ValueError(f"Analysis {analysis_id} not found")

    company_info = full_analysis.get("company_info") or {}
    cid = company_info.get("stock_id") or full_analysis["stock_id"]

    from app.routes.premium import get_premium_extras
    from app.routes.history_charts import get_history_charts
    from app.routes.company_summary import get_company_summary
    from app.routes.yfinance_extended import (
        get_insider_activity, get_company_news, get_earnings_calendar,
        get_corporate_actions, get_forward_estimates,
    )
    from app.routes.segments import get_business_segments
    from app.routes.brands import get_company_brands
    from app.routes.analyst_consensus import get_analyst_consensus
    from app.routes.broker_reports import get_broker_reports
    from app.routes.concall import get_concall_intelligence
    from app.routes.pl_intelligence import get_pl_intelligence
    from app.routes.balance_sheet_intelligence import get_balance_sheet_intelligence
    from app.routes.cash_flow_intelligence import get_cash_flow_intelligence
    from app.routes.bank_roe import get_bank_roe
    from app.routes.quarterly_intelligence import get_quarterly_intelligence

    bundle: dict = {
        f"/premium/{cid}": _safe(get_premium_extras, cid),
        f"/history-charts/{cid}": _safe(get_history_charts, cid),
        f"/company-summary/{cid}": _safe(get_company_summary, cid),
        f"/yfinance/{cid}/insider-activity": _safe(get_insider_activity, cid),
        f"/segments/{cid}": _safe(get_business_segments, cid),
        f"/brands/{cid}": _safe(get_company_brands, cid),
        f"/yfinance/{cid}/news": _safe(get_company_news, cid),
        f"/yfinance/{cid}/calendar": _safe(get_earnings_calendar, cid),
        f"/yfinance/{cid}/corporate-actions": _safe(get_corporate_actions, cid),
        f"/yfinance/{cid}/forward-estimates": _safe(get_forward_estimates, cid),
        f"/analyst-consensus/{cid}": _safe(get_analyst_consensus, cid),
        f"/broker-reports/{cid}": _safe(get_broker_reports, cid),
        f"/concall/{cid}": _safe(get_concall_intelligence, cid),
        f"/bank-roe/{cid}": _safe(get_bank_roe, cid),
    }

    # These 4 tabs have a Consolidated/Standalone toggle (statement_type
    # query param) — pre-fetch the no-param default plus both explicit
    # variants so the toggle works offline without a live re-fetch.
    for prefix, fn in (
        ("pl-intelligence", get_pl_intelligence),
        ("balance-sheet-intelligence", get_balance_sheet_intelligence),
        ("cash-flow-intelligence", get_cash_flow_intelligence),
        # Quarterly tab: generic quarterly financials + the sector KPI block
        ("quarterly-intelligence", get_quarterly_intelligence),
    ):
        bundle[f"/{prefix}/{cid}"] = _safe(fn, cid, None)
        bundle[f"/{prefix}/{cid}?statement_type=CONSOLIDATED"] = _safe(fn, cid, "CONSOLIDATED")
        bundle[f"/{prefix}/{cid}?statement_type=STANDALONE"] = _safe(fn, cid, "STANDALONE")

    bundle = {k: v for k, v in bundle.items() if v is not None}
    return full_analysis, bundle


def _inject(value) -> str:
    # Global `<`-escape (not just `</script`) since free-text fields —
    # broker names, headlines, AI narrative — could contain `<` anywhere.
    return json.dumps(value, default=str).replace("<", "\\u003c")


def generate_html_export(analysis_id: str, db) -> str:
    """Builds and writes the standalone HTML export, returns its path."""
    full_analysis, bundle = build_export_bundle(analysis_id, db)

    if not _TEMPLATE_PATH.exists():
        raise RuntimeError(
            f"Export template missing at {_TEMPLATE_PATH} — run "
            f"`npm run build:export` in frontend/ (see HOW_TO_RUN.md)."
        )
    html = _TEMPLATE_PATH.read_text(encoding="utf-8")
    if _ANALYSIS_TOKEN not in html or _BUNDLE_TOKEN not in html:
        raise RuntimeError(
            f"Export template at {_TEMPLATE_PATH} is missing the expected "
            f"placeholder tokens — rebuild it with `npm run build:export`."
        )
    html = html.replace(_ANALYSIS_TOKEN, _inject(full_analysis))
    html = html.replace(_BUNDLE_TOKEN, _inject(bundle))

    reports_dir = Path(config.reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / f"{analysis_id}.html"
    out_path.write_text(html, encoding="utf-8")

    logger.info("HTML export generated", analysis_id=analysis_id, path=str(out_path))
    return str(out_path)
