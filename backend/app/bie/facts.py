"""Read side of `bie_facts`: one in-memory index per company, so the
calculations and the report ask for a figure by name and period and get the
fact (with its source) back.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import BieFact, Document

# Element names differ by filing layout (general / bank / NBFC / insurer).
REVENUE_KEYS = ("RevenueFromOperations", "InterestEarned", "GrossPremiumIncome", "GrossPremiumsWritten", "SegmentRevenueFromOperations")
# Profit after tax for the period. Layouts name it differently and, worse, reuse one name for different things:
# "ProfitLossForThePeriod" is before minority interests in the bank layout and after them in the layout some
# conglomerates file. The order below therefore takes the unambiguous names first:
#   general companies -> profit for the period, which includes the minority's share (it is deducted separately);
#   banks             -> the group's net profit after minority interests and associates, the figure banks headline.
PROFIT_KEYS = ("ProfitLossForPeriod", "ProfitLossForPeriodBeforeMinorityInterest",
               "ProfitLossAfterTaxesMinorityInterestAndShareOfProfitLossOfAssociates", "ProfitLossForThePeriod",
               "ProfitLossFromOrdinaryActivitiesAfterTax", "NetProfitLossForThePeriod",
               "ProfitLossAfterTaxAndExtraordinaryItems", "ProfitLossAfterTax")
PBT_KEYS = ("ProfitBeforeTax", "ProfitLossFromOrdinaryActivitiesBeforeTax", "ProfitBeforeExtraordinaryItemsAndTax",
            "ProfitLossBeforeTax", "ProfitOrLossBeforeTax")
# An insurer's lines of business carry premium and a result, not the general segment elements.
LINE_PREMIUM = "NetPremium"
LINE_RESULTS = ("UnderwritingProfitOrLoss", "SurplusDeficit")
EXCEPTIONAL_KEYS = ("ExceptionalItemsBeforeTax", "ExceptionalItems")
SEGMENT_REVENUE = "SegmentRevenue"
SEGMENT_RESULT = "SegmentProfitLossBeforeTaxAndFinanceCosts"
SEGMENT_ASSETS = "SegmentAssets"
SEGMENT_LIABILITIES = "SegmentLiabilities"

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class FactBook:
    def __init__(self, db: Session, company_id: str):
        self.company_id = company_id
        self.facts: list[BieFact] = db.query(BieFact).filter(BieFact.company_id == company_id).all()
        doc_ids = {f.document_id for f in self.facts if f.document_id}
        self.documents: dict[str, Document] = (
            {d.id: d for d in db.query(Document).filter(Document.id.in_(doc_ids)).all()} if doc_ids else {}
        )
        self._index: dict[tuple, list[BieFact]] = defaultdict(list)
        for f in self.facts:
            self._index[(f.fact_type, f.key, f.dimension, f.period_type, f.period_end, f.statement_type)].append(f)

    def _newest(self, facts: list[BieFact]) -> BieFact | None:
        """A revised filing supersedes the original: latest publication wins."""
        if not facts:
            return None

        def published(f: BieFact) -> datetime:
            doc = self.documents.get(f.document_id)
            return (doc.published_at if doc and doc.published_at else None) or f.created_at or _EPOCH

        return max(facts, key=published)

    def get(self, key: str, period_type: str, period_end: date | None, basis: str = "NA", *,
            fact_type: str = "financial", dimension: str = "") -> BieFact | None:
        return self._newest(self._index.get((fact_type, key, dimension, period_type, period_end, basis), []))

    def first(self, keys: tuple[str, ...], period_type: str, period_end: date | None, basis: str, **kw) -> BieFact | None:
        for key in keys:
            fact = self.get(key, period_type, period_end, basis, **kw)
            if fact is not None:
                return fact
        return None

    def of_type(self, fact_type: str) -> list[BieFact]:
        return [f for f in self.facts if f.fact_type == fact_type]

    def period_ends(self, period_type: str, basis: str) -> list[date]:
        """Period ends, newest first, for which a headline revenue figure exists."""
        ends = {f.period_end for f in self.facts
                if f.fact_type == "financial" and f.period_type == period_type and f.statement_type == basis
                and f.key in REVENUE_KEYS and f.period_end is not None}
        return sorted(ends, reverse=True)

    def bases(self) -> list[str]:
        present = {f.statement_type for f in self.facts if f.fact_type == "financial"}
        return [b for b in ("CONSOLIDATED", "STANDALONE") if b in present]

    def segments(self, period_type: str, period_end: date, basis: str) -> dict[str, dict[str, BieFact]]:
        """{segment label: {element name: fact}} for one period. Flow items
        use `period_type`; assets and liabilities are balances at period end."""
        out: dict[str, dict[str, BieFact]] = defaultdict(dict)
        grouped: dict[tuple[str, str], list[BieFact]] = defaultdict(list)
        for f in self.facts:
            if f.fact_type != "segment" or f.statement_type != basis or f.period_end != period_end:
                continue
            if f.period_type not in (period_type, "INSTANT"):
                continue
            grouped[(f.dimension, f.key)].append(f)
        for (label, key), facts in grouped.items():
            out[label][key] = self._newest(facts)
        return dict(out)
