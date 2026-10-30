"""Find listed companies named in free text (SEBI order titles).

Each active stock is known by two names: ours (`stocks.company_name`, often
shortened — "SMC Global Sec.", "Omaxe") and NSE's official one from
EQUITY_L.csv ("SMC Global Securities Limited", "Omaxe Limited"). Both are
normalised (lower case, "&" → "and", punctuation dropped, a trailing
"limited"/"ltd" removed) and looked for as whole words.

Precision rules, because a false match puts a SEBI order against the wrong
company:
  - a name of one or two words must be followed in the text by "limited",
    "ltd", "group" or the end of the text ("ITC Limited", not "itc" inside
    another phrase); three or more words may stand alone
  - a name of one or two words must also follow a joining word ("of",
    "in", "against", "the", …) — "Taurian MPS Ltd" is not "MPS Ltd"
  - a name that follows "at", "on" or "through" is the venue ("options at
    BSE"), role SCRIP
  - "in respect of / against <others> in the matter of <company>" is role
    MATTER: the order is against the others (often individuals trading in
    the company's shares); a company named in the "in respect of" part is
    NAMED
  - where one match lies inside a longer one ("Bank of India" inside
    "Central Bank of India"), only the longer one counts
  - "in the matter of X Group (companies)" names every stock whose name
    starts with X — only when X is at least four letters and not a generic
    word — as role GROUP
  - a name that follows "scrip of", "shares of", "trading in", or anywhere
    after "insider trading", "front running", "market manipulation" is role
    SCRIP: the company's shares were traded (or, for front running, its
    trades were the target), the company is not the party
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.infrastructure.database.models import Stock

_TAIL = re.compile(r"(?:\s+(?:limited|ltd|ltd\s*\.?))+$")
_FOLLOW = re.compile(r"\s*(?:limited|ltd|group|\(|$)")
_SCRIP = re.compile(r"(?:scrip|shares|securities|units|stock|gdrs?)\s+of(?:\s+the)?\s*$|trading\s+(?:activities\s+)?in(?:\s+the)?\s*$|"
                    r"dealings?\s+in(?:\s+the)?\s*$|insider\s+trading\s+(?:in|of)(?:\s+the)?\s*$|front[\s-]+running\s+(?:in|of)?\s*$|"
                    r"price\s+manipulation\s+in\s*$")
# the company's shares or trades are the setting, however far back in the title the phrase sits
_SCRIP_ANY = re.compile(r"front[\s-]*running|insider\s+trading|market\s+manipulation|price\s+manipulation|trading\s+activit")
_VENUE = re.compile(r"(?:\bat|\bon|\bthrough|\bvia)(?:\s+the)?\s*$")
_RESPECT = re.compile(r"\b(?:in\s*respect\s+(?:of|to)|against)\b(.*?)(?=\bin\s+the\s+matter\s+of\b|$)")
_JOIN = {"of", "in", "against", "the", "to", "and", "by", "for", "with", "re", "v", "vs"}
_GROUP = re.compile(r"matter\s+of\s+(?:the\s+)?([a-z0-9 ]+?)\s+group\b")
_GENERIC = {"certain", "various", "the", "india", "indian", "national", "shares", "stock", "capital", "global", "bao ltd"}


def normalise(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def alias(name: str) -> str:
    n = normalise(name)
    n = re.sub(r"^the\s+", "", n)
    return _TAIL.sub("", n).strip()


_NEWS_CUE = re.compile(r"\s*(?:s\s+)?(?:shares?|stocks?|scrip|q[1-4]|results?|ipo|block deal|board|dividend|bonus)\b")


@dataclass
class Match:
    stock_id: str
    name: str
    role: str  # NAMED | GROUP | SCRIP


class Matcher:
    def __init__(self, names: dict[str, set[str]]):
        """`names`: {stock_id: {name, ...}}."""
        self.entries: list[tuple[str, str]] = []
        for sid, ns in names.items():
            for n in {alias(x) for x in ns if x}:
                if len(n) >= 3 and n not in _GENERIC:
                    self.entries.append((sid, n))

    @classmethod
    def from_db(cls, db: Session, official: dict[str, str] | None = None) -> Matcher:
        """`official`: {symbol: NSE official name}; fetched from EQUITY_L.csv when not given."""
        if official is None:
            from app.ingestion.nse_equity_list_client import fetch_equity_list

            official = {r.get("SYMBOL", "").upper(): r.get("NAME OF COMPANY", "") for r in fetch_equity_list()}
        names: dict[str, set[str]] = {}
        for s in db.query(Stock).filter(Stock.is_active.is_(True)):
            names[s.id] = {s.company_name, official.get(s.symbol, "")}
        return cls(names)

    def find_news(self, title: str) -> list[Match]:
        """Companies named in a news headline, which rarely says "Limited": a
        name of two or more words stands alone; a single word counts only just
        before "shares", "Q2", "results" and the like."""
        text = normalise(title)
        hits = []
        for sid, n in self.entries:
            if n not in text:
                continue
            words = len(n.split())
            for m in re.finditer(rf"\b{re.escape(n)}\b", text):
                if words >= 2 or (len(n) >= 5 and _NEWS_CUE.match(text, m.end())):
                    hits.append((m.start(), m.end(), sid, n))
        kept = [h for h in hits if not any(o[0] <= h[0] and h[1] <= o[1] and (o[1] - o[0]) > (h[1] - h[0]) for o in hits)]
        return list({sid: Match(sid, n, "NAMED") for _, _, sid, n in kept}.values())

    def find(self, title: str) -> list[Match]:
        text = normalise(title)
        hits = []  # (start, end, sid, name)
        for sid, n in self.entries:
            if n not in text:
                continue
            for m in re.finditer(rf"\b{re.escape(n)}\b", text):
                if len(n.split()) < 3:
                    before = text[:m.start()].split()
                    if not _FOLLOW.match(text, m.end()) or (before and before[-1] not in _JOIN):
                        continue
                hits.append((m.start(), m.end(), sid, n))
        # drop a match that sits inside a longer one
        kept = [h for h in hits if not any(o[0] <= h[0] and h[1] <= o[1] and (o[1] - o[0]) > (h[1] - h[0]) for o in hits)]
        out: dict[str, Match] = {}
        respect = _RESPECT.search(text)
        for start, _end, sid, n in kept:
            if _SCRIP.search(text[:start]) or _SCRIP_ANY.search(text[:start]) or _VENUE.search(text[:start]):
                role = "SCRIP"
            elif respect and "matter of" in text[respect.end():] and not (respect.start(1) <= start < respect.end(1)):
                role = "MATTER"
            else:
                role = "NAMED"
            if sid not in out or out[sid].role == "SCRIP":
                out[sid] = Match(sid, n, role)
        g = _GROUP.search(text)
        if g:
            prefix = re.sub(r"^the\s+", "", g.group(1)).strip()
            if len(prefix) >= 4 and prefix not in _GENERIC:
                members = {sid: n for sid, n in self.entries if n == prefix or n.startswith(prefix + " ")}
                if len(members) <= 25:
                    for sid, n in members.items():
                        out.setdefault(sid, Match(sid, n, "GROUP"))
        return list(out.values())
