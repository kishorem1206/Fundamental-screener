"""Peer selection for the report's sector section. A single-segment company
is compared with the screener's existing peer set (same basic industry). A
multi-segment company is compared segment by segment: each reported segment
is matched to an NSE basic industry by name, and the largest companies
classified there are its peers — a conglomerate's own label ("Diversified
FMCG") says little about who its cigarette or paper business competes with.
"""
from __future__ import annotations

import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.bie.facts import SEGMENT_REVENUE, FactBook
from app.infrastructure.database.models import Stock
from app.pipeline.peer_selection import select_peer_candidates

_STOP = {"and", "other", "others", "products", "product", "business", "businesses", "fmcg", "services", "service",
         "including", "such", "as", "the", "of", "for", "with", "its", "related", "activities", "segment", "general",
         "consumer", "digital", "industrial", "india", "indian", "world", "rest", "domestic", "international"}
_PER_SEGMENT = 2
_MAX_PEERS = 8


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words} - _STOP


_ALIASES = {"agri": "agricultural", "pharma": "pharmaceutical", "auto": "automobile", "infra": "infrastructure"}


def _hit(a: str, b: str) -> bool:
    """Same word, allowing a plural or inflected ending but not a different word that merely starts alike
    ("rest" is not "restaurant", "hospitality" is not "hospital")."""
    a, b = _ALIASES.get(a, a), _ALIASES.get(b, b)
    short, long = sorted((a, b), key=len)
    return len(short) >= 4 and long.startswith(short) and len(short) / len(long) >= 0.75


def match_basic_industry(text: str, industries: dict[str, int], *, whole_label: bool = False) -> str | None:
    """The basic industry whose name is best covered by `text`, or None when
    under half of any name's words appear. With `whole_label` the text's own
    words must also largely be in the name, so "Infrastructure Projects" is
    not matched to "Telecom - Infrastructure"."""
    ordered = [w[:-1] if w.endswith("s") and len(w) > 4 else w for w in re.findall(r"[a-z]{3,}", text.lower())]
    have = [w for w in ordered if w not in _STOP]
    best, best_rank = None, (0.0, 0, 0)
    for name, count in industries.items():
        want = _tokens(name)
        if not want:
            continue
        positions = [next((i for i, h in enumerate(have) if _hit(w, h)), None) for w in want]
        found = [i for i in positions if i is not None]
        score = len(found) / len(want)
        if whole_label:
            # Both sides must largely agree: the industry's words in the label and the label's words in the industry.
            mine = set(have)
            covered = sum(any(_hit(w, h) for w in want) for h in mine) / len(mine) if mine else 0.0
            if covered < 1 / 3 or score + covered < 1.3:
                continue
        # Among equally covered names, the one matching the earliest word of the label wins ("Paperboards, Paper & Packaging" is paper first).
        rank = (score, -min(found) if found else 0, count)
        if score >= 0.5 and rank > best_rank:
            best, best_rank = name, rank
    return best


def segment_peer_plan(db: Session, stock: Stock, book: FactBook | None = None) -> list[dict]:
    """[{segment, basic_industry, peers: [Stock]}] for a multi-segment
    company; empty when it reports one segment or no segment can be matched."""
    book = book or FactBook(db, stock.id)
    basis = next(iter(book.bases()), None)
    ends = book.period_ends("FY", basis) if basis else []
    if not ends:
        return []
    segments = {label: facts for label, facts in book.segments("FY", ends[0], basis).items()
                if SEGMENT_REVENUE in facts and (facts[SEGMENT_REVENUE].attributes or {}).get("is_business_segment", True)}
    # A lender's segments (retail, wholesale, treasury) are lines of one business, not separate industries.
    # An IT company's segments are the industries of its customers, not businesses it is in.
    if len(segments) < 2 or stock.sector in ("Financial Services", "Information Technology"):
        return []
    industries = dict(db.query(Stock.basic_industry, func.count()).filter(
        Stock.is_active.is_(True), Stock.basic_industry.isnot(None)).group_by(Stock.basic_industry).all())
    activities = [f.dimension for f in book.of_type("business_activity")]
    # Where the language model has matched the segments to the exchange's industry list (app.bie.llm_assist), that match is
    # used; matching by name is the fallback for a company it has not classified.
    from app.bie.llm_assist import stored_segment_industries
    stored = stored_segment_industries(db, stock.id)
    plan, used, matched = [], {stock.id}, set()
    for label in sorted(segments, key=lambda l: -float(segments[l][SEGMENT_REVENUE].value_num)):
        # A catch-all label ("FMCG - Others") is described by the matching line of the company's activity table.
        tail = label.split("-")[-1].strip().lower()
        described = [a for a in activities if a.lower().startswith(tail) or _tokens(a) & _tokens(label)]
        # The activity table is consulted only for a label that names nothing itself; a named segment is matched on its name alone.
        if stored is not None:
            industry = stored.get(label) if stored.get(label) in industries else None
        else:
            industry = match_basic_industry(label, industries, whole_label=True) if _tokens(label) \
                else match_basic_industry(" ".join([label, *described]), industries)
        # A segment in the company's own industry is still a match once classified (its peers are the rest of that industry).
        if industry is None or industry in matched or (stored is None and industry == stock.basic_industry) \
                or re.fullmatch(r"(all )?others?( segments?)?|unallocated", label.strip(), re.I):
            continue
        matched.add(industry)
        peers = (db.query(Stock).filter(Stock.is_active.is_(True), Stock.basic_industry == industry, Stock.id.notin_(used))
                 .order_by(Stock.market_cap.desc().nullslast()).limit(_PER_SEGMENT).all())
        if peers:
            used |= {p.id for p in peers}
            plan.append({"segment": label, "basic_industry": industry, "peers": peers})
    # Segment-by-segment comparison is only worth having when it covers most of the company; otherwise the
    # company is compared as a whole with its own industry.
    # Segments that all sit in the company's own industry need no segment-by-segment comparison: its ordinary peers are the comparison.
    if plan and all(row["basic_industry"] == stock.basic_industry for row in plan):
        return []
    total = sum(float(f[SEGMENT_REVENUE].value_num or 0) for f in segments.values())
    covered = sum(float(segments[row["segment"]][SEGMENT_REVENUE].value_num or 0) for row in plan)
    return plan if total > 0 and covered / total >= 0.6 else []


def select_peers(db: Session, stock: Stock) -> list[tuple[Stock, str | None]]:
    """(peer, the subject's segment it is a peer for — None for whole-company peers)."""
    plan = segment_peer_plan(db, stock)
    if plan:
        return [(p, row["segment"]) for row in plan for p in row["peers"]][:_MAX_PEERS]
    return [(p, None) for p in select_peer_candidates(db, stock.id, stock.sector)]
