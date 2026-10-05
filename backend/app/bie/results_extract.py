"""Facts from an NSE financial-results data file (Ind-AS, banking, NBFC and
insurance layouts all share the conventions used here).

Period identification relies on context ids, not context dates: "One…" is
the reporting quarter and "Four…" the financial year to date. Pre-2025 files
stamp the year-to-date context with the quarter's dates, so the dates are
read from the `DateOfStartOfReportingPeriod`/`DateOfEndOfReportingPeriod`
facts inside each context instead.

Every numeric fact in the three undimensioned contexts (quarter, year to
date, balance-sheet date) is kept under its element name, so nothing a
later phase needs has to be re-fetched. Dimensioned contexts that pair a
description with an amount (segments, itemised other expenses) become facts
whose `dimension` is that description.
"""
from __future__ import annotations

import html
import re
from datetime import date

from sqlalchemy.orm import Session

from app.bie import xbrl
from app.bie.evidence import clear_document_facts, record_fact
from app.infrastructure.database.models import Document

_SKIP_AXES = {"RelatedPartyTransactionAxis", "AuditorAxis"}
_TEXT_FACTS = {
    "IsCompanyReportingMultisegmentOrSingleSegment", "DescriptionOfSingleSegment",
    "DeclarationOfUnmodifiedOpinionOrStatementOnImpactOfAuditQualification",
    "WhetherResultsAreAuditedOrUnaudited", "ReportingQuarter",
}
_UNITS = {"INR": "INR", "pure": "ratio", "INRPerShare": "INR/share", "shares": "shares"}
_BALANCE_ELEMENTS = {"SegmentAssets", "SegmentLiabilities", "NetSegmentAssets", "NetSegmentLiabilities"}
# A reconciliation row in the segment table, not a business segment.
_NOT_A_SEGMENT = re.compile(
    r"^\s*(\(?(add|less)\b|total\b|inter[\s-]*segment|elimination|unallocat|un-allocat|net\s+segment)", re.I)


def is_business_segment(label: str) -> bool:
    return bool(label.strip()) and _NOT_A_SEGMENT.search(label) is None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


class _Periods:
    def __init__(self, inst: xbrl.Instance, period_end: date):
        def d(name: str, ctx: str) -> date | None:
            try:
                return date.fromisoformat((inst.lookup(name, ctx) or "")[:10])
            except ValueError:
                return None

        one, four = inst.contexts.get("OneD"), inst.contexts.get("FourD")
        self.q_end = d("DateOfEndOfReportingPeriod", "OneD") or (one.end if one else None) or period_end
        self.q_start = d("DateOfStartOfReportingPeriod", "OneD") or (one.start if one else None)
        self.ytd_end = d("DateOfEndOfReportingPeriod", "FourD") or self.q_end
        self.ytd_start = d("DateOfStartOfReportingPeriod", "FourD") or d("DateOfStartOfFinancialYear", "OneD")
        self.fy_start = d("DateOfStartOfFinancialYear", "OneD") or self.ytd_start
        self.fy_end = d("DateOfEndOfFinancialYear", "OneD")
        # A first-quarter file's year-to-date column repeats the quarter.
        self.ytd_is_quarter = self.ytd_start is not None and self.ytd_start == self.q_start
        # What the "One" column covers. Dates that form a clean quarter are taken as they are. Otherwise the dates as
        # typed are believed (a half-yearly statement really does cover six months), with one exception: dates that
        # cannot be right. A column said to run for about a year but ending on a date that is not the financial year
        # end is a mistyped quarter (2025-01-10 entered for 1 October 2025); it is read as the quarter if the file's own
        # numbers agree (its revenue is nearer a quarter's share of the year-to-date column than the whole of it).
        # A six-month first column is never read as a quarter, even where it may be a mistyped one: a figure that is
        # missing can be seen to be missing, a figure filed under the wrong period cannot.
        span = (self.q_end - self.q_start).days if self.q_start and self.q_end else None
        if span is None or 80 <= span <= 100:
            self.one_is_quarter, self.one_is_full_year = True, False
        else:
            impossible_year = span >= 350 and self.fy_end is not None and self.q_end != self.fy_end
            quarter_like = False
            if impossible_year:
                four_start = d("DateOfStartOfReportingPeriod", "FourD") or (four.start if four else None)
                four_end = d("DateOfEndOfReportingPeriod", "FourD") or (four.end if four else None)
                for name in ("RevenueFromOperations", "InterestEarned", "GrossPremiumIncome", "GrossPremiumsWritten", "Income"):
                    try:
                        first, second = float(inst.lookup(name, "OneD")), float(inst.lookup(name, "FourD"))
                    except (TypeError, ValueError):
                        continue
                    if second > 0 and first > 0 and four_start and four_end:
                        months = max(round((self.q_end - date(self.q_end.year - (1 if self.q_end.month < 4 else 0), 4, 1)).days / 30.4), 3)
                        quarter_like = abs(first / second - 3 / months) < abs(first / second - 1.0)
                        break
            if quarter_like:
                self.one_is_quarter, self.one_is_full_year = True, False
                month = (self.q_end.month - 3) % 12 + 1  # a quarter begins two months before its last month
                self.q_start = date(self.q_end.year - (1 if month > self.q_end.month else 0), month, 1)
            else:
                self.one_is_quarter, self.one_is_full_year = False, span >= 350 and not impossible_year
        self.ytd_is_quarter = self.ytd_start is not None and self.ytd_start == self.q_start

    def of(self, ctx: xbrl.Context) -> tuple[str, date | None, date | None] | None:
        """(period_type, start, end) for a context, or None to skip it."""
        cid = ctx.id
        if cid.startswith("PY"):
            return None  # prior-year comparative; that year's own filing is the source for it
        undefined = ctx.instant is None and ctx.start is None and ctx.end is None
        # Insurers' line-of-business contexts carry the period family at the end ("Fire_ContextFourD").
        one = cid.startswith("One") or cid.endswith(("OneD", "OneI"))
        four = cid.startswith("Four") or cid.endswith(("FourD", "FourI"))
        if ctx.instant is not None or (undefined and cid.endswith("I")):
            return ("INSTANT", None, self.q_end if one or four else ctx.instant)
        if one:
            if self.one_is_quarter:
                return ("Q", self.q_start, self.q_end)
            return ("FY" if self.one_is_full_year else "YTD", self.q_start, self.q_end)
        if four:
            if self.ytd_is_quarter:
                return None
            full_year = self.fy_end is not None and self.ytd_end == self.fy_end
            return ("FY" if full_year else "YTD", self.ytd_start, self.ytd_end)
        if ctx.start == self.q_start and ctx.end == self.q_end:
            return ("Q", ctx.start, ctx.end)
        return None


def extract_results(db: Session, *, company_id: str, document: Document, content: bytes,
                    period_end: date, basis: str, audited: bool) -> int:
    """Write the facts in one results data file. Returns how many."""
    inst = xbrl.parse(content)
    periods = _Periods(inst, period_end)
    nature_text = (inst.text("NatureOfReportStandaloneConsolidated") or "").upper()
    statement_type = nature_text if nature_text in ("STANDALONE", "CONSOLIDATED") else basis
    confidence = "HIGH" if audited else "MEDIUM"

    clear_document_facts(db, document)
    written = 0

    def write(fact: xbrl.XFact, *, fact_type: str, dimension: str, period: tuple, attributes: dict | None = None) -> None:
        nonlocal written
        number = fact.number() if fact.unit is not None else None
        record_fact(
            db, scope="COMPANY", company_id=company_id, fact_type=fact_type, key=fact.name, dimension=dimension,
            period_type=period[0], period_start=period[1], period_end=period[2], statement_type=statement_type,
            value_num=number, value_text=None if number is not None else _clean(fact.value),
            unit=_UNITS.get(fact.unit, fact.unit) if number is not None else None, attributes=attributes,
            nature="REPORTED", document=document, locator_type="XBRL", locator=f"{fact.name}@{fact.context_id}",
            quote=fact.value, extraction_method="XBRL_PARSE", source_tier=1, confidence=confidence, replace=False,
        )
        written += 1

    # Labels for dimensioned contexts: (period family, axis, member) -> description.
    labels: dict[tuple[str, str, str], str] = {}
    for ctx in inst.contexts.values():
        if len(ctx.dims) != 1:
            continue
        (axis, member), = ctx.dims.items()
        description = next((f for f in inst.in_context(ctx.id) if f.name.startswith("DescriptionOf") and f.value), None)
        if description is not None:
            labels[(ctx.id[:3], axis, member)] = _clean(description.value)

    for ctx in inst.contexts.values():
        period = periods.of(ctx)
        if period is None:
            continue
        facts = inst.in_context(ctx.id)
        if not ctx.dims:
            for fact in facts:
                if inst.is_ambiguous(fact):
                    continue
                if fact.unit is not None and fact.number() is not None:
                    write(fact, fact_type="financial", dimension="", period=period)
                elif fact.name in _TEXT_FACTS and fact.value:
                    write(fact, fact_type="filing_statement", dimension="", period=period)
            continue
        if len(ctx.dims) != 1:
            continue
        (axis, member), = ctx.dims.items()
        if axis in _SKIP_AXES:
            continue
        is_segment = "Segment" in axis
        label = labels.get((ctx.id[:3], axis, member))
        if not label and is_segment and member.endswith("Member") and not re.search(r"\d+Member$", member):
            # Insurers' lines of business are fixed members with no description: the member name is the label.
            label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", member[:-len("Member")])
        if not label:
            continue
        for fact in facts:
            if fact.unit is None or fact.number() is None:
                continue
            # Pre-2025 files put segment assets in a duration context; they are a balance at period end.
            fact_period = ("INSTANT", None, period[2]) if fact.name in _BALANCE_ELEMENTS else period
            write(fact, fact_type="segment" if is_segment else "line_detail", dimension=label, period=fact_period,
                  attributes={"axis": axis, "member": member,
                              **({"is_business_segment": is_business_segment(label)} if is_segment else {})})
    return written
