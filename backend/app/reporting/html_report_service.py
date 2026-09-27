"""Renders the banking HTML report (primary artifact) and its JSON companion
(section 43/45 reproducibility). See banking_stock_analysis_report.md.
"""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import config
from app.reporting import charts
from app.reporting.data_builder import build_report_context, fmt
from app.logger import logger

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "jinja"]),
)
_env.globals["charts"] = charts
_env.globals["fmt"] = fmt


def generate_html_report(analysis_id: str, db) -> str:
    """Build the report context, render the template, write
    {analysis_id}.html and {analysis_id}.json. Returns the HTML file path."""
    reports_dir = Path(config.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    context = build_report_context(analysis_id, db)

    template = _env.get_template("banking_report.html.jinja")
    html = template.render(**context)

    html_path = reports_dir / f"{analysis_id}.html"
    html_path.write_text(html, encoding="utf-8")

    json_path = reports_dir / f"{analysis_id}.json"
    json_path.write_text(json.dumps(context, indent=2, default=str), encoding="utf-8")

    logger.info("HTML report generated", path=str(html_path), analysis_id=analysis_id)
    return str(html_path)
