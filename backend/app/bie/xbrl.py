"""Minimal XBRL instance reader for SEBI/NSE filings (financial results in
the Ind-AS, banking, NBFC and insurance layouts; BRSR). Namespace-agnostic:
facts are keyed by local element name, because the same element appears
under `in-bse-fin` in pre-2025 files and `in-capmkt` in integrated filings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from lxml import etree

_XBRLI = "http://www.xbrl.org/2003/instance"
_XBRLDI = "http://xbrl.org/2006/xbrldi"
_SKIP_NAMESPACES = (_XBRLI, "http://www.xbrl.org/2003/linkbase")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _date(text: str | None) -> date | None:
    try:
        return date.fromisoformat((text or "").strip()[:10])
    except ValueError:
        return None


@dataclass
class Context:
    id: str
    start: date | None = None
    end: date | None = None
    instant: date | None = None
    dims: dict[str, str] = field(default_factory=dict)  # axis local name -> member local name / typed value


@dataclass
class XFact:
    name: str
    context_id: str
    value: str
    unit: str | None
    decimals: str | None

    def number(self) -> float | None:
        try:
            return float(self.value)
        except (TypeError, ValueError):
            return None


class Instance:
    def __init__(self, contexts: dict[str, Context], facts: list[XFact]):
        self.contexts = contexts
        self.facts = facts
        self._by_context: dict[str, list[XFact]] = {}
        self._index: dict[tuple[str, str], XFact] = {}
        for f in facts:
            self._by_context.setdefault(f.context_id, []).append(f)
            self._index.setdefault((f.name, f.context_id), f)

    def in_context(self, context_id: str) -> list[XFact]:
        return self._by_context.get(context_id, [])

    def get(self, name: str, context_id: str) -> XFact | None:
        return self._index.get((name, context_id))

    def lookup(self, name: str, context_id: str) -> str | None:
        f = self.get(name, context_id)
        return f.value if f is not None else None

    def is_ambiguous(self, fact: XFact) -> bool:
        """True when the same element appears in the same context with a
        different value (e.g. opening and closing cash in pre-2025 files):
        the element-and-context locator cannot tell them apart."""
        return any(o.name == fact.name and o.value != fact.value for o in self._by_context.get(fact.context_id, []))

    def first(self, name: str) -> XFact | None:
        return next((f for f in self.facts if f.name == name), None)

    def text(self, name: str) -> str | None:
        f = self.first(name)
        return f.value.strip() if f is not None and f.value else None


def parse(content: bytes) -> Instance:
    root = etree.fromstring(content, parser=etree.XMLParser(recover=True, huge_tree=True))
    contexts: dict[str, Context] = {}
    for node in root.iter():
        # Matched by local name: some 2022-vintage files declare contexts
        # under a different instance-namespace prefix.
        if not isinstance(node.tag, str) or _local(node.tag) != "context" or node.get("id") is None:
            continue
        ctx = Context(id=node.get("id"))
        for el in node.iter():
            name = _local(el.tag)
            if name == "startDate":
                ctx.start = _date(el.text)
            elif name == "endDate":
                ctx.end = _date(el.text)
            elif name == "instant":
                ctx.instant = _date(el.text)
            elif name == "explicitMember":
                ctx.dims[_local(el.get("dimension", ""))] = _local(el.text or "")
            elif name == "typedMember":
                child = next(iter(el), None)
                ctx.dims[_local(el.get("dimension", ""))] = (child.text or "").strip() if child is not None else ""
        contexts[ctx.id] = ctx

    facts: list[XFact] = []
    for el in root:
        if not isinstance(el.tag, str):
            continue
        namespace = el.tag[1:].split("}", 1)[0] if el.tag.startswith("{") else ""
        context_id = el.get("contextRef")
        if namespace in _SKIP_NAMESPACES or context_id is None:
            continue
        facts.append(XFact(name=_local(el.tag), context_id=context_id, value=(el.text or "").strip(),
                           unit=el.get("unitRef"), decimals=el.get("decimals")))
        # Some 2022-vintage files reference the main period contexts
        # ("OneD", "FourD", "OneI") without defining them.
        contexts.setdefault(context_id, Context(id=context_id))
    return Instance(contexts, facts)
