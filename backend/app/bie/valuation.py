"""Phase 4 — forecast and valuation. Everything here is arithmetic in
Python on facts already on file; nothing is asked of an LLM.

Method, kept deliberately mechanical so every number can be traced:
  * Assumptions are derived by stated rules from history and stored as
    ANALYST_ASSUMPTION facts with their rationale. They are this app's
    choices, not company guidance.
  * Three scenarios (Bear / Base / Bull) flex growth and margin together.
  * Three lenses: discounted cash flow, sum of the parts on segment results,
    and peer price-to-earnings. They are reported side by side; when they
    disagree the disagreement is the finding.
Lenders get the forecast and the peer lens only: free cash flow to the firm
is not meaningful for a business whose raw material is borrowed money.
"""
from __future__ import annotations

import re
from datetime import date
from statistics import median

from sqlalchemy.orm import Session

from app.bie.evidence import record_fact
from app.bie.facts import PBT_KEYS, PROFIT_KEYS, REVENUE_KEYS, SEGMENT_RESULT, SEGMENT_REVENUE, FactBook
from app.bie.peers import segment_peer_plan, select_peers
from app.bie.sector import benchmark_industry, benchmarks_for
from app.infrastructure.database.models import BieFact, Stock

YEARS = 5
SCENARIOS = {"Bear": -1, "Base": 0, "Bull": 1}  # the direction in which each unit's own growth and margin shifts are applied


def _spread(values: list[float], lo: float, hi: float, default: float) -> float:
    """How much a series has varied (its standard deviation), limited to [lo, hi]; `default` when there are under three points."""
    if len(values) < 3:
        return default
    mean = sum(values) / len(values)
    return _clamp((sum((x - mean) ** 2 for x in values) / (len(values) - 1)) ** 0.5, lo, hi)
BETA_FLOOR = 0.70
DEBT_SPREAD = 0.015
_FACT_TYPES = ("assumption", "forecast", "valuation")
# A break from history: in the quarters reported since the last full year, revenue growth is this far (in points) from
# what the record implies AND the margin on it has moved by this much (relative) against the same quarters a year
# earlier. Both together mark a change in the business itself (a tax, a merger, a new plant), not a noisy quarter.
# How the three lenses are combined into one reference value (renormalised over the lenses available).
BLEND = {"dcf": 0.40, "sotp": 0.45, "relative": 0.15}
# Operating working capital, line by line: (label, balance-sheet elements, +1 asset / −1 liability).
WC_LINES = (("Trade receivables", ("TradeReceivablesCurrent",), 1), ("Inventories", ("Inventories",), 1),
            ("Other current assets", ("OtherCurrentAssets",), 1),
            ("Trade payables", ("TradePayablesCurrent",), -1),
            ("Other current liabilities", ("OtherCurrentLiabilities", "OtherCurrentFinancialLiabilities", "ProvisionsCurrent"), -1))
BREAK_GROWTH_GAP = 0.15
BREAK_MARGIN_MOVE = 0.20


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _v(fact: BieFact | None) -> float | None:
    return float(fact.value_num) if fact is not None and fact.value_num is not None else None


def _add_years(d: date, n: int) -> date:
    return date(d.year + n, d.month, min(d.day, 28) if d.month == 2 else d.day)


def _cagr(series: list[float]) -> float | None:
    """Compound growth across up to three steps of a newest-first series."""
    usable = [x for x in series[:4] if x and x > 0]
    if len(usable) < 2:
        return None
    return (usable[0] / usable[-1]) ** (1 / (len(usable) - 1)) - 1


def _entity_key(name: str | None) -> str:
    return " ".join(re.sub(r"\b(ltd|limited|the|private|pvt|company|co)\b|[^a-z0-9 ]", "", (name or "").lower()).split())


def listed_stakes(db: Session, company_id: str) -> list[tuple[Stock, BieFact]]:
    """The company's associates and joint ventures that are themselves listed, each with the fact that states the holding.
    Subsidiaries are left out: their results are already inside the consolidated figures."""
    facts = db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.fact_type == "group_entity").all()
    held = {}
    for f in facts:
        if re.match(r"\s*(associate|joint\s+venture)", f.value_text or "", re.I) and (f.attributes or {}).get("shares_held_ratio"):
            held.setdefault(_entity_key(f.dimension), f)
    if not held:
        return []
    by_name = {_entity_key(st.company_name): st for st in db.query(Stock).filter(Stock.is_active.is_(True)).all()}
    return [(by_name[k], f) for k, f in held.items() if k in by_name and by_name[k].id != company_id]


SCALAR_METRICS = {"tax_rate", "capex_to_revenue", "depreciation_to_revenue", "working_capital_to_revenue", "beta",
                  "terminal_growth", "cost_of_debt_spread", "peer_price_to_earnings", "excise_to_revenue",
                  "holding_discount", "investment_haircut", "minority_share", "acquisition_cash_paid",
                  "dividend_payout", "terminal_return_on_capital", "current_investment_haircut", "bank_deposit_haircut"}
PATH_METRICS = {"revenue_growth", "margin"}  # per unit, per forecast year, per scenario
UNIT_METRICS = {"ev_ebit_multiple"}  # per segment


def value_company(db: Session, company_id: str, *, use_overrides: bool = True, extra_overrides: list | None = None) -> dict:
    """Build the forecast and valuation and store them. Analyst overrides
    (`bie_assumption_overrides`, plus any `extra_overrides` for a what-if)
    replace the system's estimate for the assumption they name; the system
    value is still computed and reported beside each one."""
    from app.infrastructure.database.models import BieAssumptionOverride

    stock = db.get(Stock, company_id)
    rules = list(extra_overrides or [])
    if use_overrides:
        rules += db.query(BieAssumptionOverride).filter(BieAssumptionOverride.company_id == company_id,
                                                        BieAssumptionOverride.superseded_at.is_(None)).all()
    applied: list[dict] = []

    def find(metric: str, unit: str, scenario: str, year: int | None):
        """The most specific rule: a named scenario beats All, a named year beats every-year; what-ifs beat stored rules."""
        best, best_rank = None, None
        for i, o in enumerate(rules):
            if o.metric != metric or o.unit != unit or o.scenario not in (scenario, "All") or o.fiscal_year not in (year, None):
                continue
            rank = (o.scenario == scenario, o.fiscal_year is not None, -i)
            if best_rank is None or rank > best_rank:
                best, best_rank = o, rank
        return best

    def note(o, system: float, active: float, scenario: str, year: int | None) -> None:
        applied.append({"metric": o.metric, "unit": o.unit, "scenario": scenario, "year": year, "system": system, "value": active,
                        "reason": o.reason, "id": getattr(o, "id", None), "confidence": getattr(o, "confidence", None),
                        "evidence_url": getattr(o, "evidence_url", None)})

    scalars: list[dict] = []
    paths: list[dict] = []

    def scalar(metric: str, system: float, unit: str = "Company") -> float:
        o = find(metric, unit, "All", None)
        scalars.append({"metric": metric, "unit": unit, "system": system, "active": float(o.value) if o is not None else system,
                        "override_id": getattr(o, "id", None) if o is not None else None})
        if o is None:
            return system
        note(o, system, float(o.value), "All", None)
        return float(o.value)

    def path(metric: str, unit: str, scenario: str, year: int, base: float, shift: float, mult: float) -> float:
        """A scenario-specific override is used as given; an All-scenario one replaces the Base value and the
        scenario's own shift still applies around it."""
        system = (base + shift) * mult if metric == "revenue_growth" else base * mult
        o = find(metric, unit, scenario, year)
        value = system
        if o is not None:
            value = float(o.value) if o.scenario == scenario else ((float(o.value) + shift) if metric == "revenue_growth" else float(o.value) * mult)
            note(o, system, value, scenario, year)
        paths.append({"metric": metric, "unit": unit, "scenario": scenario, "year": year, "system": system, "active": value,
                     "override_id": getattr(o, "id", None) if o is not None else None})
        return value

    db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.fact_type.in_(_FACT_TYPES)).delete(synchronize_session=False)
    db.flush()
    book = FactBook(db, company_id)
    basis = next(iter(book.bases()), None)
    ends = book.period_ends("FY", basis) if basis else []
    if not ends:
        return {"skipped": "no full-year results on file"}
    fy, today = ends[0], date.today()
    is_lender = stock.sector == "Financial Services"

    def get(key, period_type="FY", end=fy):
        return book.get(key, period_type, end, basis)

    def year_back(d: date) -> date:
        return date(d.year - 1, d.month, 28 if d.month == 2 else d.day)

    quarter_ends = book.period_ends("Q", basis)
    # Quarters reported since the last full year that have the same quarter a year earlier on file.
    new_quarters = [q for q in quarter_ends if q > fy and year_back(q) in quarter_ends]

    def momentum(pairs: list[tuple]) -> dict | None:
        """Year-to-date change from (revenue now, result now, revenue then, result then) facts, one tuple a quarter."""
        if not pairs or any(f is None or f.value_num is None for row in pairs for f in row):
            return None
        rev_now, res_now, rev_then, res_then = (sum(_v(row[i]) for row in pairs) for i in range(4))
        if rev_now <= 0 or rev_then <= 0 or res_then <= 0:
            return None
        return {"quarters": len(pairs), "growth": rev_now / rev_then - 1, "margin_now": res_now / rev_now, "margin_then": res_then / rev_then,
                "margin_move": (res_now / rev_now) / (res_then / rev_then) - 1, "facts": [f for row in pairs for f in row]}

    def excise_of(period_type: str, end: date) -> BieFact | None:
        return next((f for f in book.facts if f.fact_type == "line_detail" and f.key == "OtherExpenses" and re.search("excise", f.dimension, re.I)
                     and f.period_type == period_type and f.period_end == end and f.statement_type == basis), None)

    revenue_f = book.first(REVENUE_KEYS, "FY", fy, basis)
    pbt_f = get("ProfitBeforeExceptionalItemsAndTax") or book.first(PBT_KEYS, "FY", fy, basis)
    tax_f, profit_f = get("TaxExpense"), book.first(PROFIT_KEYS, "FY", fy, basis)
    shares_f = max((f for f in book.of_type("identity") if f.key == "shares_outstanding"), key=lambda f: f.created_at, default=None)
    price_f = max((f for f in book.of_type("identity") if f.key == "last_price"), key=lambda f: f.created_at, default=None)
    mcap_f = max((f for f in book.of_type("identity") if f.key == "market_cap"), key=lambda f: f.created_at, default=None)
    if not all((revenue_f, pbt_f, shares_f, price_f)) or not _v(revenue_f):
        return {"skipped": "revenue, profit before tax, share count or price missing"}
    revenue0, shares, price = _v(revenue_f), _v(shares_f), _v(price_f)

    macro = db.query(BieFact).filter(BieFact.scope == "MACRO").order_by(BieFact.created_at).all()
    latest = {}
    for f in macro:
        latest[(f.key, f.dimension)] = f
    rf_f = next((f for (k, d), f in latest.items() if k == "gsec_yield_pct" and d.startswith("9Y")), None)
    erp_f = latest.get(("equity_risk_premium_india", ""))
    far = str(today.year + 4)
    cpi_f, gdp_f = latest.get(("cpi_inflation_pct", far)), latest.get(("real_gdp_growth_pct", far))
    inflation = (_v(cpi_f) or 4.0) / 100
    nominal = inflation + (_v(gdp_f) or 6.5) / 100

    assumptions: dict[str, BieFact] = {}

    def assume(key: str, value: float, unit: str, rationale: str, dimension: str = "", inputs: list | None = None) -> BieFact:
        fact = record_fact(
            db, scope="COMPANY", company_id=company_id, fact_type="assumption", key=key, dimension=dimension,
            period_type="NA", statement_type=basis, value_num=value, unit=unit, nature="ANALYST_ASSUMPTION",
            extraction_method="RULE", source_tier=3, confidence="LOW", formula=rationale,
            inputs=[f.id for f in (inputs or []) if f is not None] or None, replace=False,
        )
        fact.verification_status = "ASSUMPTION"
        assumptions[f"{key}|{dimension}"] = fact
        return fact

    def calc(fact_type: str, key: str, value: float, unit: str, formula: str, *, dimension: str = "", end: date | None = None,
             inputs: list[BieFact] | None = None, attributes: dict | None = None) -> BieFact:
        fact = record_fact(
            db, scope="COMPANY", company_id=company_id, fact_type=fact_type, key=key, dimension=dimension,
            period_type="FY" if end else "NA", period_end=end, statement_type=basis, value_num=value, unit=unit,
            attributes=attributes, nature="CALCULATED", extraction_method="CALCULATION", source_tier=3, confidence="LOW",
            inputs=[f.id for f in (inputs or list(assumptions.values()))], formula=formula, replace=False,
        )
        fact.verification_status = "VERIFIED" if all(
            i.verification_status in ("VERIFIED", "ASSUMPTION") for i in (inputs or list(assumptions.values()))) else "FAILED"
        return fact

    # ── units being forecast: reported business segments, or the company as one ──
    segments = {l: f for l, f in book.segments("FY", fy, basis).items()
                if SEGMENT_REVENUE in f and SEGMENT_RESULT in f and (f[SEGMENT_REVENUE].attributes or {}).get("is_business_segment", True)
                and (_v(f[SEGMENT_REVENUE]) or 0) > 0}  # a segment reported with no revenue has nothing to forecast
    by_segment = len(segments) >= 2 and not is_lender
    company_growth = _cagr([_v(book.first(REVENUE_KEYS, "FY", e, basis)) or 0 for e in ends])
    units = []
    if by_segment:
        for label, facts in sorted(segments.items(), key=lambda kv: -_v(kv[1][SEGMENT_REVENUE])):
            history = [book.segments("FY", e, basis).get(label, {}) for e in ends]
            revs = [_v(h.get(SEGMENT_REVENUE)) or 0 for h in history]
            margins = [_v(h[SEGMENT_RESULT]) / _v(h[SEGMENT_REVENUE]) for h in history[:3]
                       if h.get(SEGMENT_REVENUE) is not None and h.get(SEGMENT_RESULT) is not None and _v(h[SEGMENT_REVENUE])]
            now_then = [(n.get(SEGMENT_REVENUE), n.get(SEGMENT_RESULT), t.get(SEGMENT_REVENUE), t.get(SEGMENT_RESULT))
                        for n, t in ((book.segments("Q", q, basis).get(label, {}), book.segments("Q", year_back(q), basis).get(label, {})) for q in new_quarters)]
            all_margins = [_v(h[SEGMENT_RESULT]) / _v(h[SEGMENT_REVENUE]) for h in history
                           if h.get(SEGMENT_REVENUE) is not None and h.get(SEGMENT_RESULT) is not None and _v(h[SEGMENT_REVENUE])]
            units.append({"name": label, "revenue0": _v(facts[SEGMENT_REVENUE]), "growth": _cagr(revs), "margin": sum(margins) / len(margins),
                          "revenue_history": revs, "margin_history": all_margins,
                          "margin0": _v(facts[SEGMENT_RESULT]) / _v(facts[SEGMENT_REVENUE]), "ytd": momentum(now_then),
                          "sources": [facts[SEGMENT_REVENUE], facts[SEGMENT_RESULT]], "years": len([r for r in revs[:4] if r])})
        bridge = _v(pbt_f) / sum(_v(f[SEGMENT_RESULT]) for f in segments.values())
        assume("segment_result_to_pbt", bridge, "ratio",
               f"Profit before exceptional items and tax ÷ sum of segment results in FY{fy.year}; held constant, so unallocated "
               "income and costs move in line with the segments.", inputs=[pbt_f])
    else:
        margins = []
        for e in ends[:3]:
            r = _v(book.first(REVENUE_KEYS, "FY", e, basis))
            p = _v(book.get("ProfitBeforeExceptionalItemsAndTax", "FY", e, basis) or book.first(PBT_KEYS, "FY", e, basis))
            if r and p is not None:
                margins.append(p / r)
        q_pbt = lambda q: book.get("ProfitBeforeExceptionalItemsAndTax", "Q", q, basis) or book.first(PBT_KEYS, "Q", q, basis)  # noqa: E731
        now_then = [(book.first(REVENUE_KEYS, "Q", q, basis), q_pbt(q), book.first(REVENUE_KEYS, "Q", year_back(q), basis), q_pbt(year_back(q)))
                    for q in new_quarters]
        all_revenue = [_v(book.first(REVENUE_KEYS, "FY", e, basis)) or 0 for e in ends]
        all_pbt = [_v(book.get("ProfitBeforeExceptionalItemsAndTax", "FY", e, basis) or book.first(PBT_KEYS, "FY", e, basis)) for e in ends]
        units.append({"name": "Company", "revenue0": revenue0, "growth": company_growth, "margin": sum(margins) / len(margins),
                      "revenue_history": all_revenue, "margin_history": [p / r for p, r in zip(all_pbt, all_revenue) if r and p is not None],
                      "margin0": _v(pbt_f) / revenue0, "ytd": momentum(now_then), "sources": [revenue_f, pbt_f], "years": len(ends)})
        bridge = 1.0

    breaks: list[dict] = []
    for unit in units:
        raw = unit["growth"] if unit["growth"] is not None else (company_growth if company_growth is not None else nominal)
        start = _clamp(raw, -0.05, 0.20)
        end_growth = _clamp(start, inflation, nominal)
        unit["start"], unit["end"], unit["break"] = start, end_growth, False
        ytd = unit["ytd"]
        # Lenders are left on the record: provisions make a single quarter's profit too noisy to rebase on.
        if not is_lender and ytd is not None and abs(ytd["growth"] - start) > BREAK_GROWTH_GAP and abs(ytd["margin_move"]) > BREAK_MARGIN_MOVE:
            # The quarters since the last full year do not look like the record: rebase on them.
            span = f"the {ytd['quarters']} quarter(s) of FY{fy.year + 1} reported so far"
            breaks.append({"name": unit["name"], "quarters": ytd["quarters"], "growth": ytd["growth"], "history_growth": start,
                           "margin_now": ytd["margin_now"], "margin_then": ytd["margin_then"], "history_margin": unit["margin"],
                           "margin": unit["margin0"] * (1 + ytd["margin_move"])})
            unit["start"], unit["margin"], unit["break"] = _clamp(ytd["growth"], -0.5, 1.0), unit["margin0"] * (1 + ytd["margin_move"]), True
            assume("revenue_growth_year_1", unit["start"], "ratio",
                   f"Break from history. Revenue in {span} against the same quarter(s) a year earlier ({ytd['growth']:+.1%}), "
                   f"used in place of the {start:+.1%} the record implies because the margin on that revenue also moved "
                   f"{ytd['margin_move']:+.0%}. Assumes the rest of the year looks like the quarters reported.", unit["name"], ytd["facts"])
            assume("revenue_growth_year_5", end_growth, "ratio",
                   f"From year 2 the rebased revenue grows at the pre-break record's rate ({raw:+.1%}), held between long-run inflation "
                   f"({inflation:.1%}) and nominal GDP growth ({nominal:.1%}) as the IMF projects them.", unit["name"], [cpi_f, gdp_f])
            assume("margin", unit["margin"], "ratio",
                   f"Break from history. FY{fy.year} margin ({unit['margin0']:.1%}) moved by the change seen in {span} against the same "
                   f"quarter(s) a year earlier ({ytd['margin_then']:.1%} to {ytd['margin_now']:.1%}), held at that level.", unit["name"], ytd["facts"])
            continue
        assume("revenue_growth_year_1", start, "ratio",
               f"Compound growth of reported revenue over the last {max(unit['years'] - 1, 1)} year(s) on file "
               f"({raw:+.1%}), limited to between −5% and +20%.", unit["name"], unit["sources"])
        assume("revenue_growth_year_5", end_growth, "ratio",
               f"Year-1 growth moved in equal steps to a year-5 rate held between long-run inflation ({inflation:.1%}) and "
               f"nominal GDP growth ({nominal:.1%}) as the IMF projects them.", unit["name"], [cpi_f, gdp_f])
        assume("margin", unit["margin"], "ratio",
               "Average of the last three reported years' " + ("segment result ÷ segment revenue." if by_segment else
                                                                "profit before exceptional items and tax ÷ revenue."), unit["name"], unit["sources"])

    pbt0 = _v(book.first(PBT_KEYS, "FY", fy, basis)) or _v(pbt_f)
    tax_rate = _clamp((_v(tax_f) / pbt0) if tax_f is not None and pbt0 and pbt0 > 0 else 0.252, 0.15, 0.35)
    assume("tax_rate", tax_rate, "ratio", f"Tax expense ÷ profit before tax in FY{fy.year}, limited to between 15% and 35%.", inputs=[tax_f])
    tax_rate = scalar("tax_rate", tax_rate)
    # Bull and Bear move each unit by how much that unit's own record has moved: a volatile business gets a wider range.
    for u in units:
        r = u["revenue_history"]
        growths = [r[i] / r[i + 1] - 1 for i in range(len(r) - 1) if r[i] and r[i + 1] and r[i + 1] > 0]
        u["g_shift"] = _spread(growths, 0.01, 0.08, 0.02)
        level = abs(u["margin"]) or 0.01
        u["m_shift"] = _clamp(_spread(u["margin_history"], 0.0, 1.0, 0.08 * level) / level, 0.03, 0.25)
        assume("scenario_growth_shift", u["g_shift"], "ratio",
               f"Standard deviation of this unit's annual revenue growth over the {len(growths)} year(s) on file, limited to between 1 and 8 points "
               "(2 points where there are too few years). Added in the Bull case and subtracted in the Bear case, every year.", u["name"], u["sources"])
        assume("scenario_margin_shift", u["m_shift"], "ratio",
               f"Standard deviation of this unit's margin over the {len(u['margin_history'])} year(s) on file as a share of the margin, limited to "
               "between 3% and 25% (8% where there are too few years). The margin is raised by this proportion in Bull and cut by it in Bear.",
               u["name"], u["sources"])

    # Excise the company collects and passes on is forecast as its own line; costs and capital scale with revenue net of it.
    excise0_f = excise_of("FY", fy)
    excise_ratio, has_excise = 0.0, excise0_f is not None and (_v(excise0_f) or 0) > 0
    if has_excise:
        recent = [(excise_of("Q", q), book.first(REVENUE_KEYS, "Q", q, basis)) for q in new_quarters]
        recent = [(e, r) for e, r in recent if e is not None and r is not None and _v(r)]
        if recent:
            excise_ratio = sum(_v(e) for e, _ in recent) / sum(_v(r) for _, r in recent)
            assume("excise_to_revenue", excise_ratio, "ratio",
                   f"Excise duty ÷ reported revenue in the {len(recent)} quarter(s) of FY{fy.year + 1} reported so far "
                   f"(it was {_v(excise0_f) / revenue0:.1%} in FY{fy.year}), held constant.", inputs=[f for pair in recent for f in pair])
        else:
            excise_ratio = _v(excise0_f) / revenue0
            assume("excise_to_revenue", excise_ratio, "ratio", f"Excise duty ÷ reported revenue in FY{fy.year}, held constant.", inputs=[excise0_f, revenue_f])
        excise_ratio = scalar("excise_to_revenue", excise_ratio)
    net0 = revenue0 - (_v(excise0_f) if has_excise else 0.0)
    net_label = "revenue net of excise" if has_excise else "revenue"

    def net_of(e: date) -> float | None:
        return _v(book.get("revenue_net_of_excise", "FY", e, basis) or book.first(REVENUE_KEYS, "FY", e, basis))

    ratio = lambda key: (abs(_v(get(key)) or 0) / net0)  # noqa: E731
    finance_ratio, other_income_ratio = ratio("FinanceCosts"), ratio("OtherIncome")
    da_ratio = ratio("DepreciationDepletionAndAmortisationExpense")
    capex_hist = [(_v(book.get("capital_expenditure", "FY", e, basis)), net_of(e)) for e in ends[:3]]
    capex_hist = [c / r for c, r in capex_hist if c is not None and r]
    capex_ratio = sum(capex_hist) / len(capex_hist) if capex_hist else da_ratio
    wc_lines = []
    for label, keys, sign in WC_LINES:
        found = [f for f in (get(k, "INSTANT") for k in keys) if f is not None and f.value_num is not None]
        wc_lines.append({"label": label, "sign": sign, "balance": sum(_v(f) for f in found), "ratio": sum(_v(f) for f in found) / net0, "facts": found})
    wc = sum(l["sign"] * l["balance"] for l in wc_lines)
    wc_ratio = _clamp(wc / net0, -1.0, 1.0)
    if not is_lender:
        assume("capex_to_revenue", capex_ratio, "ratio", f"Average capital expenditure ÷ {net_label} over the last three years on file.")
        assume("depreciation_to_revenue", da_ratio, "ratio", f"Depreciation and amortisation ÷ {net_label} in FY{fy.year}, held constant.")
        assume("working_capital_to_revenue", wc_ratio, "ratio",
               f"Operating working capital ÷ {net_label} at FY{fy.year}: receivables, inventories and other (non-financial) current assets, less trade payables, "
               "other current liabilities (which include customer advances) and current provisions. Each line is held at its own share of "
               f"{net_label}.", inputs=[f for l in wc_lines for f in l["facts"]])
        paid_f, pat0 = get("DividendsPaidClassifiedAsFinancingActivities"), _v(profit_f)
        payout = _clamp(abs(_v(paid_f)) / pat0, 0.0, 1.0) if paid_f is not None and pat0 and pat0 > 0 else 0.0
        assume("dividend_payout", payout, "ratio", f"Dividends paid in cash ÷ profit after tax in FY{fy.year}, limited to 100%; held constant.",
               inputs=[f for f in (paid_f, profit_f) if f is not None])

    capex_ratio, da_ratio = scalar("capex_to_revenue", capex_ratio), scalar("depreciation_to_revenue", da_ratio)
    wc_system = wc_ratio
    wc_ratio = scalar("working_capital_to_revenue", wc_ratio)
    payout = scalar("dividend_payout", payout) if not is_lender else 0.0
    liquid0 = sum((_v(get(k, "INSTANT")) or 0.0) for k in ("CashAndCashEquivalents", "BankBalanceOtherThanCashAndCashEquivalents", "CurrentInvestments"))

    minority = 0.0
    if not is_lender:
        minority_f = get("ProfitOrLossAttributableToNonControllingInterests")
        if minority_f is not None and profit_f is not None and (_v(profit_f) or 0) > 0 and (_v(minority_f) or 0) > 0:
            minority = _clamp(_v(minority_f) / _v(profit_f), 0.0, 0.5)
            assume("minority_share", minority, "ratio", f"Profit belonging to minority shareholders of subsidiaries ÷ profit after tax in FY{fy.year}; "
                   "the same share of the business value and of forecast profit is treated as theirs.", inputs=[minority_f, profit_f])
            minority = scalar("minority_share", minority)

    # Profit from associates and joint ventures is not in the segments: it is carried at last year's figure and belongs to the owners.
    associates_f = None if is_lender else get("ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod")
    associates = _v(associates_f) or 0.0
    if associates:
        assume("associate_income", associates, "INR", f"Share of profit of associates and joint ventures in FY{fy.year}, held at that figure each year.",
               inputs=[associates_f])

    # Cash paid for deals that closed after the balance sheet has left the cash figure; deals not yet closed are in neither
    # the forecast nor the bridge.
    from app.bie.acquisitions import since_balance_sheet
    deals = since_balance_sheet(db, company_id, fy) if not is_lender else {"paid": [], "pending": []}
    paid_total, deal_facts = 0.0, []
    if deals["paid"]:
        system_paid = sum(d["cost"] for d in deals["paid"])
        deal_facts = [f for d in deals["paid"] for f in d["facts"]]
        assume("acquisition_cash_paid", system_paid, "INR", f"Sum of the stated cost of the {len(deals['paid'])} cash acquisition(s) the company "
               f"reported as completed after {fy:%d %b %Y}; where a completion notice gives no price, the price in the agreement it completes.",
               inputs=deal_facts)
        paid_total = scalar("acquisition_cash_paid", system_paid)

    # Opening balance sheet for the forecast, grouped the way the forecast moves it. The two "other" lines are whatever
    # the named lines do not explain, held flat; with them the opening sheet balances by construction.
    assets_f, liabilities_f = get("Assets", "INSTANT"), get("Liabilities", "INSTANT")
    sheet0 = None
    if not is_lender and assets_f is not None and liabilities_f is not None:
        wc_assets0 = sum(l["balance"] for l in wc_lines if l["sign"] > 0)
        wc_liabilities0 = sum(l["balance"] for l in wc_lines if l["sign"] < 0)
        held0 = sum((_v(get(k, "INSTANT")) or 0.0) for k in ("NoncurrentInvestments", "InvestmentsAccountedForUsingEquityMethod"))
        debt0 = sum((_v(get(k, "INSTANT")) or 0.0) for k in ("BorrowingsNoncurrent", "BorrowingsCurrent"))
        sheet0 = {"liquid": liquid0, "wc_assets": wc_assets0, "investments": held0,
                  "fixed": _v(assets_f) - liquid0 - wc_assets0 - held0, "assets": _v(assets_f),
                  "wc_liabilities": wc_liabilities0, "borrowings": debt0, "other_liabilities": _v(liabilities_f) - wc_liabilities0 - debt0,
                  "equity": _v(assets_f) - _v(liabilities_f)}

    # ── forecast ─────────────────────────────────────────────────────────
    forecast: dict[str, list[dict]] = {}
    for name, sign in SCENARIOS.items():
        rows, prev = [], {u["name"]: u["revenue0"] for u in units}
        prev_total, prev_net, liquid, prev_nwc = revenue0, net0, liquid0, wc
        sheet = dict(sheet0) if sheet0 else None
        for k in range(1, YEARS + 1):
            end = _add_years(fy, k)
            unit_rows, result_total = [], 0.0
            for u in units:
                # After a break, year 1 carries the step and later years grow at the long-run rate; otherwise growth glides to it.
                glide = (u["start"] if k == 1 else u["end"]) if u["break"] else u["start"] + (u["end"] - u["start"]) * (k - 1) / (YEARS - 1)
                growth = path("revenue_growth", u["name"], name, end.year, glide, sign * u["g_shift"], 1.0)
                rev = prev[u["name"]] * (1 + growth)
                result = rev * path("margin", u["name"], name, end.year, u["margin"], 0.0, 1 + sign * u["m_shift"])
                prev[u["name"]] = rev
                result_total += result
                unit_rows.append({"name": u["name"], "revenue": rev, "result": result, "growth": growth})
            # Company revenue grows at the revenue-weighted growth of its units (segment revenue is before eliminations).
            unit_now, unit_before = sum(x["revenue"] for x in unit_rows), sum(x["revenue"] / (1 + x["growth"]) for x in unit_rows)
            total = prev_total * unit_now / unit_before
            pbt = result_total * bridge
            pat = pbt * (1 - tax_rate)
            net = total * (1 - excise_ratio)
            ebit = pbt + (finance_ratio - other_income_ratio) * net
            nwc_change = wc_ratio * net - prev_nwc
            fcff = None if is_lender else ebit * (1 - tax_rate) + da_ratio * net - capex_ratio * net - nwc_change
            owners = pat * (1 - minority) + associates
            row = {"end": end, "revenue": total, "excise": total - net, "net_revenue": net, "pbt": pbt, "pat": pat, "eps": owners / shares,
                   "ebit": ebit, "fcff": fcff, "units": unit_rows, "nopat": ebit * (1 - tax_rate),
                   "associates": associates, "minority_profit": pat * minority, "owners": owners}
            if not is_lender:
                # The integrated schedule: profit to operating cash, then capex and dividends, with what is left swept into liquid assets.
                scale = wc_ratio / wc_system if wc_system else 1.0
                row["working_capital"] = [{"label": l["label"], "value": l["ratio"] * scale * net, "sign": l["sign"]} for l in wc_lines]
                row["nwc"], row["nwc_change"] = wc_ratio * net, nwc_change
                row["da"], row["capex"] = da_ratio * net, capex_ratio * net
                row["cfo"] = pat + row["da"] - row["nwc_change"]
                row["dividends"] = max(pat, 0.0) * payout
                row["dps"] = row["dividends"] * (1 - minority) / shares
                row["acquisitions"] = paid_total if k == 1 else 0.0
                row["cash_after"] = row["cfo"] - row["capex"] - row["dividends"] - row["acquisitions"]
                liquid += row["cash_after"]
                row["liquid_close"] = liquid
                row["dividend_uncovered"] = row["dividends"] > row["cfo"] - row["capex"]
                if sheet is not None:
                    # Every line of the balance sheet moves with the schedule above; the residual must be zero.
                    wc_assets = sum(x["value"] for x in row["working_capital"] if x["sign"] > 0)
                    wc_liabilities = sum(x["value"] for x in row["working_capital"] if x["sign"] < 0)
                    sheet = {**sheet, "liquid": liquid, "wc_assets": wc_assets, "wc_liabilities": wc_liabilities,
                             "fixed": sheet["fixed"] + row["capex"] - row["da"] + row["acquisitions"],
                             "equity": sheet["equity"] + pat - row["dividends"]}
                    sheet["assets"] = sheet["liquid"] + sheet["wc_assets"] + sheet["investments"] + sheet["fixed"]
                    sheet["residual"] = sheet["assets"] - (sheet["wc_liabilities"] + sheet["borrowings"] + sheet["other_liabilities"] + sheet["equity"])
                    row["sheet"] = dict(sheet)
            rows.append(row)
            prev_total, prev_net, prev_nwc = total, net, wc_ratio * net
            if has_excise:
                calc("forecast", "revenue_net_of_excise", net, "INR", "forecast revenue × (1 − excise ÷ revenue)", dimension=name, end=end)
            for key, value, unit_name in (("revenue", total, "INR"), ("profit_before_tax", pbt, "INR"), ("profit_after_tax", pat, "INR"),
                                          ("earnings_per_share", owners / shares, "INR/share")) + ((("free_cash_flow_to_firm", fcff, "INR"),) if fcff is not None else ()):
                calc("forecast", key, value, unit_name, "see the stated assumptions; revenue × margin, less tax", dimension=name, end=end)
            if name == "Base" and by_segment:
                for x in unit_rows:
                    calc("forecast", "segment_revenue", x["revenue"], "INR", "prior-year segment revenue × (1 + growth)", dimension=x["name"], end=end)
                    calc("forecast", "segment_result", x["result"], "INR", "segment revenue × margin", dimension=x["name"], end=end)
        forecast[name] = rows

    # ── cost of capital ──────────────────────────────────────────────────
    for u in units:  # the Base growth path, year by year, before overrides
        u["path"] = [(u["start"] if k == 1 else u["end"]) if u["break"] else u["start"] + (u["end"] - u["start"]) * (k - 1) / (YEARS - 1)
                     for k in range(1, YEARS + 1)]
        u["path_years"] = [_add_years(fy, k).year for k in range(1, YEARS + 1)]
    out: dict = {"scenarios": {}, "by_segment": by_segment, "is_lender": is_lender, "breaks": breaks, "has_excise": has_excise,
                 "break_quarters": len(new_quarters), "current_year": f"FY{str(fy.year + 1)[-2:]}"}
    net_liquid_f = book.get("net_liquid_assets", "INSTANT", fy, basis)
    net_liquid = _v(net_liquid_f) or 0.0

    # ── from the value of the business to the value of the shares ────────
    # The forecast covers what the segments earn. Assets that sit outside it are added once, at a stated basis,
    # and the part of the business that belongs to minority shareholders is taken out.
    bridge_items: list[dict] = []
    bridge_facts: list[BieFact] = []
    if not is_lender:
        cash_f, bank_f, invest_f = (get(k, "INSTANT") for k in ("CashAndCashEquivalents", "BankBalanceOtherThanCashAndCashEquivalents", "CurrentInvestments"))
        if any(f is not None for f in (cash_f, bank_f, invest_f)):
            assume("current_investment_haircut", 0.15, "ratio", "Taken off current investments: a reserve against what could not be realised at the "
                   "balance-sheet figure or is needed in the business.", inputs=[f for f in (invest_f,) if f is not None] or None)
            assume("bank_deposit_haircut", 0.10, "ratio", "Taken off bank balances other than cash: some are earmarked or restricted.",
                   inputs=[f for f in (bank_f,) if f is not None] or None)
            cut_invest, cut_bank = scalar("current_investment_haircut", 0.15), scalar("bank_deposit_haircut", 0.10)
            for label, f, keep in (("Cash and cash equivalents", cash_f, 1.0), ("Other bank balances", bank_f, 1 - cut_bank),
                                   ("Current investments", invest_f, 1 - cut_invest)):
                if f is not None and (_v(f) or 0) > 0:
                    bridge_items.append({"label": label, "value": _v(f) * keep,
                                         "basis": f"Balance sheet, FY{fy.year}" + (f", less {1 - keep:.0%}" if keep < 1 else "")})
                    bridge_facts.append(f)
        owed = [f for f in (get(k, "INSTANT") for k in ("BorrowingsNoncurrent", "BorrowingsCurrent")) if f is not None and (_v(f) or 0) > 0]
        if owed:
            bridge_items.append({"label": "Less borrowings", "value": -sum(_v(f) for f in owed), "basis": f"Balance sheet, FY{fy.year}"})
            bridge_facts += owed
        leases = [f for f in (get(k, "INSTANT") for k in ("LeaseLiabilitiesNoncurrent", "LeaseLiabilitiesCurrent", "NoncurrentLeaseLiabilities",
                                                           "CurrentLeaseLiabilities")) if f is not None and (_v(f) or 0) > 0]
        if leases:
            bridge_items.append({"label": "Less lease liabilities", "value": -sum(_v(f) for f in leases), "basis": f"Balance sheet, FY{fy.year}"})
            bridge_facts += leases
        other_f = get("NoncurrentInvestments", "INSTANT")
        if other_f is not None and (_v(other_f) or 0) > 0:
            assume("investment_haircut", 0.10, "ratio", "Taken off non-current financial investments: they are carried at balance-sheet "
                   "value and not all could be turned into cash at that figure.", inputs=[other_f])
            haircut = scalar("investment_haircut", 0.10)
            bridge_items.append({"label": "Other non-current investments", "value": _v(other_f) * (1 - haircut),
                                 "basis": f"Balance sheet, FY{fy.year}, less {haircut:.0%}"})
            bridge_facts.append(other_f)
        stakes, carried = [], 0.0
        for held, fact in listed_stakes(db, company_id):
            cap = db.query(BieFact).filter(BieFact.company_id == held.id, BieFact.fact_type == "identity", BieFact.key == "market_cap",
                                           BieFact.value_num.isnot(None)).order_by(BieFact.created_at.desc()).first()
            if cap is not None:
                stakes.append((held, fact, cap))
                carried += float((fact.attributes or {}).get("carrying_amount") or 0.0)
        equity_method_f = get("InvestmentsAccountedForUsingEquityMethod", "INSTANT")
        book_value = _v(equity_method_f) or 0.0
        if stakes and any((f.attributes or {}).get("carrying_amount") is None for _, f, _ in stakes):
            # The filing does not say what the listed stakes are carried at, so they cannot be separated from the rest
            # of the balance-sheet figure: use whichever of the two is larger, never both.
            market = sum(float(f.attributes["shares_held_ratio"]) * _v(c) for _, f, c in stakes)
            if market >= book_value:
                equity_method_f, book_value = None, 0.0
            else:
                stakes = []
        if stakes:
            assume("holding_discount", 0.05, "ratio", "Taken off the market value of listed stakes: a large holding could not be sold at the "
                   "quoted price in one piece.", inputs=[c for _, _, c in stakes])
            discount = scalar("holding_discount", 0.05)
            for held, fact, cap in stakes:
                share = float(fact.attributes["shares_held_ratio"])
                bridge_items.append({"label": f"{held.company_name} ({share:.2%} held)", "value": share * _v(cap) * (1 - discount),
                                     "basis": f"Market value on {cap.period_end:%d %b %Y}, less {discount:.0%}"})
                bridge_facts += [fact, cap]
        if equity_method_f is not None and book_value - carried > 0:
            bridge_items.append({"label": "Other associates and joint ventures" if stakes else "Associates and joint ventures",
                                 "value": book_value - carried,
                                 "basis": f"Balance sheet, FY{fy.year}" + (", after the carrying amount of the listed stakes above" if carried else "")})
            bridge_facts.append(equity_method_f)
    if deals["paid"]:
        bridge_items.append({"label": "Less cash paid for acquisitions since the balance sheet", "value": -paid_total,
                             "basis": f"{len(deals['paid'])} completed deal(s), as disclosed to the exchange"})
        bridge_facts += deal_facts
    added = sum(item["value"] for item in bridge_items)

    def to_equity(business_value: float) -> float:
        return business_value * (1 - minority) + added
    wacc = terminal = None
    plan = {row["segment"]: row["basic_industry"] for row in segment_peer_plan(db, stock, book)} if by_segment else {}
    company_group = benchmark_industry(stock.basic_industry, stock.industry)
    if not is_lender and rf_f is not None and erp_f is not None:
        weights, betas, beta_inputs = [], [], []
        for u in units:
            group = benchmark_industry(plan.get(u["name"])) or company_group
            beta_f = benchmarks_for(db, group).get("beta") if group else None
            if beta_f is not None:
                weights.append(max(u["revenue0"] * u["margin"], 0.0))
                betas.append(_v(beta_f))
                beta_inputs.append(beta_f)
        raw_beta = sum(w * b for w, b in zip(weights, betas)) / sum(weights) if weights and sum(weights) > 0 else 1.0
        beta = max(raw_beta, BETA_FLOOR)
        system_beta = beta
        assume("beta", beta, "x",
               f"Industry betas (Damodaran, India) weighted by each unit's profit: {raw_beta:.2f}"
               + (f", raised to a floor of {BETA_FLOOR:.2f} because a lower figure is more likely estimation noise than low risk." if raw_beta < BETA_FLOOR else "."),
               inputs=beta_inputs)
        beta = scalar("beta", system_beta)
        rf, erp = _v(rf_f) / 100, _v(erp_f)
        cost_of_equity = rf + beta * erp
        debt = sum((_v(get(k, "INSTANT")) or 0) for k in ("BorrowingsNoncurrent", "BorrowingsCurrent"))
        equity_value = _v(mcap_f) or price * shares
        debt_weight = debt / (debt + equity_value)
        assume("cost_of_debt_spread", DEBT_SPREAD, "ratio", "Added to the ten-year government yield for the pre-tax cost of debt.")
        spread = scalar("cost_of_debt_spread", DEBT_SPREAD)
        wacc = cost_of_equity * (1 - debt_weight) + (rf + spread) * (1 - tax_rate) * debt_weight
        terminal = inflation
        assume("terminal_growth", terminal, "ratio", "Long-run consumer price inflation as the IMF projects it: no real growth after year 5.", inputs=[cpi_f])
        terminal = scalar("terminal_growth", terminal)
        # In the terminal year the business reinvests only what its long-run growth needs: growth ÷ return on capital.
        # (Carrying an expansion-phase capex ratio into perpetuity would value a growing company at nothing.)
        equity_f = get("Equity", "INSTANT")
        outside = liquid0 + sum((_v(get(k, "INSTANT")) or 0.0) for k in ("NoncurrentInvestments", "InvestmentsAccountedForUsingEquityMethod"))
        capital0 = (_v(equity_f) or 0.0) + debt - outside
        ebit0 = _v(pbt_f) + (finance_ratio - other_income_ratio) * net0
        raw_roc = ebit0 * (1 - tax_rate) / capital0 if capital0 > 0 else None
        roc = _clamp(raw_roc, 0.08, 1.0) if raw_roc is not None and raw_roc > 0 else (1.0 if capital0 <= 0 else 0.08)
        assume("terminal_return_on_capital", roc, "ratio",
               f"Operating profit after tax ÷ capital employed in the business at FY{fy.year} (equity + borrowings − cash and investments)"
               + (f": {raw_roc:.1%}" if raw_roc is not None else ": capital employed is not positive") + ", limited to between 8% and 100%. "
               "The terminal year reinvests long-run growth ÷ this return; the five forecast years keep the capex the record shows.",
               inputs=[f for f in (equity_f, pbt_f) if f is not None])
        roc = scalar("terminal_return_on_capital", roc)
        wacc_f = calc("valuation", "cost_of_capital", wacc, "ratio",
                      "cost of equity × equity weight + after-tax cost of debt × debt weight; cost of equity = ten-year government yield + beta × equity risk premium",
                      inputs=[rf_f, erp_f, assumptions["beta|"], assumptions["cost_of_debt_spread|"], assumptions["tax_rate|"]] + ([mcap_f] if mcap_f else []),
                      attributes={"risk_free": rf, "equity_risk_premium": erp, "beta": beta, "cost_of_equity": cost_of_equity,
                                  "debt_weight": debt_weight, "cost_of_debt": rf + spread})
        out["cost_of_capital"] = wacc_f.attributes | {"wacc": wacc, "terminal_growth": terminal}

    def dcf_per_share(rows: list[dict], rate: float, growth: float) -> tuple[float, float, float]:
        first = _clamp((rows[0]["end"] - today).days / 365, 0.0, 1.0)
        ev = 0.0
        for i, row in enumerate(rows):
            fraction = first if i == 0 else 1.0
            t = max((row["end"] - today).days / 365 - 0.5 * fraction, 0.05)
            ev += row["fcff"] * fraction / (1 + rate) ** t
        horizon = (rows[-1]["end"] - today).days / 365
        terminal_fcff = rows[-1]["nopat"] * (1 + growth) * (1 - max(growth, 0.0) / roc)
        tv = terminal_fcff / (rate - growth) / (1 + rate) ** horizon
        return to_equity(ev + tv) / shares, ev + tv, tv / (ev + tv) if ev + tv else 0.0

    # ── peer multiple ────────────────────────────────────────────────────
    peer_pes, peer_inputs = [], []
    pe_by_segment: dict[str, list[float]] = {}
    for peer, peer_segment in select_peers(db, stock):
        pb = FactBook(db, peer.id)
        pbasis = next(iter(pb.bases()), None)
        pends = pb.period_ends("FY", pbasis) if pbasis else []
        cap = max((f for f in pb.of_type("identity") if f.key == "market_cap"), key=lambda f: f.created_at, default=None)
        earn = pb.first(PROFIT_KEYS, "FY", pends[0], pbasis) if pends else None
        # A multiple above 60 reflects depressed earnings, not a price the market pays for a rupee of profit.
        if cap is not None and earn is not None and (_v(earn) or 0) > 0 and _v(cap) / _v(earn) <= 60:
            peer_pes.append(_v(cap) / _v(earn))
            peer_inputs += [cap, earn]
            if peer_segment:
                pe_by_segment.setdefault(peer_segment, []).append(_v(cap) / _v(earn))
    peer_pe = median(peer_pes) if len(peer_pes) >= 2 else None
    pe_parts: list[dict] = []
    if peer_pe and by_segment and pe_by_segment:
        # Each segment's peers are priced differently: weight their multiples by what each segment contributes to profit.
        weights = {u["name"]: max(u["revenue0"] * u["margin"], 0.0) for u in units}
        total_weight = sum(weights.values())
        if total_weight > 0:
            for u in units:
                own = pe_by_segment.get(u["name"])
                pe_parts.append({"name": u["name"], "weight": weights[u["name"]] / total_weight,
                                 "multiple": sum(own) / len(own) if own else peer_pe, "peers": len(own or []),
                                 "basis": f"Mean of {len(own)} listed peer(s)" if own else "Median of all peers: none matched to this segment"})
            peer_pe = sum(part["weight"] * part["multiple"] for part in pe_parts)
    if peer_pe:
        peer_pe = scalar("peer_price_to_earnings", peer_pe)
    pe_f = calc("valuation", "peer_price_to_earnings_median", peer_pe, "x", "peers' market value ÷ latest full-year profit after tax: the median, or where segments have their own peers the "
                "profit-weighted mean of each segment's multiple",
                inputs=peer_inputs, attributes={"peers": len(peer_pes)}) if peer_pe else None

    # ── sum of the parts ─────────────────────────────────────────────────
    # Each segment is valued at what the market pays for a rupee of operating profit in that line of business:
    # the median of its listed peers where at least two are usable, the industry average otherwise. A segment with
    # neither takes the profit-weighted average of the rest. Peers above 60× are left out, as for the earnings multiple.
    multiples: dict[str, dict] = {}
    unallocated = 1.0
    if by_segment:
        def peer_multiple(peer: Stock) -> tuple[float, list[BieFact]] | None:
            pb = FactBook(db, peer.id)
            pbasis = next(iter(pb.bases()), None)
            pends = pb.period_ends("FY", pbasis) if pbasis else []
            if not pends:
                return None
            cap = max((f for f in pb.of_type("identity") if f.key == "market_cap"), key=lambda f: f.created_at, default=None)
            pbt = pb.get("ProfitBeforeExceptionalItemsAndTax", "FY", pends[0], pbasis) or pb.first(PBT_KEYS, "FY", pends[0], pbasis)
            if cap is None or pbt is None:
                return None
            extra = [pb.get(k, pt, pends[0], pbasis) for k, pt in (("FinanceCosts", "FY"), ("OtherIncome", "FY"), ("net_liquid_assets", "INSTANT"))]
            finance, other, liquid = ((_v(f) or 0.0) for f in extra)
            ebit = _v(pbt) + finance - other
            if ebit <= 0:
                return None
            return (_v(cap) - liquid) / ebit, [cap, pbt] + [f for f in extra if f is not None]

        by_peer_segment: dict[str, list] = {}
        for peer, segment in select_peers(db, stock):
            found = peer_multiple(peer) if segment else None
            if found is not None and found[0] <= 60:
                by_peer_segment.setdefault(segment, []).append((peer, *found))
        for u in units:
            usable = by_peer_segment.get(u["name"], [])
            group = benchmark_industry(plan.get(u["name"]))
            industry_f = benchmarks_for(db, group).get("ev_ebit") if group else None
            industry = _v(industry_f) if industry_f is not None and 0 < _v(industry_f) < 80 else None
            if len(usable) >= 2:
                value = median(m for _, m, _ in usable)
                fact = calc("valuation", "peer_ev_to_ebit_median", value, "x",
                            "median over listed peers of (market value − cash and current investments + borrowings) ÷ "
                            "(profit before exceptional items and tax + finance costs − other income), latest full year",
                            dimension=u["name"], inputs=[f for _, _, facts in usable for f in facts], attributes={"peers": len(usable)})
                multiples[u["name"]] = {"value": value, "industry": industry, "inputs": [fact],
                                        "basis": "Median of listed peers: " + ", ".join(f"{p.company_name} {m:.1f}×" for p, m, _ in usable)}
            elif industry is not None:
                multiples[u["name"]] = {"value": industry, "industry": industry, "inputs": [industry_f], "basis": f"Industry average: {group}"}
        matched = [(u, multiples[u["name"]]) for u in units if u["name"] in multiples]
        weight = sum(max(u["revenue0"] * u["margin"], 0.0) for u, _ in matched)
        if matched and weight > 0:
            average = sum(max(u["revenue0"] * u["margin"], 0.0) * m["value"] for u, m in matched) / weight
            for u in units:
                if u["name"] not in multiples:
                    multiples[u["name"]] = {"value": average, "industry": None, "inputs": [i for _, m in matched for i in m["inputs"]],
                                            "basis": "Profit-weighted average of the segments above: no listed peer or industry group matches this one"}
        else:  # nothing matched segment by segment: the company's own industry group for every segment
            company_f = benchmarks_for(db, company_group).get("ev_ebit") if company_group else None
            if company_f is not None and 0 < _v(company_f) < 80:
                multiples = {u["name"]: {"value": _v(company_f), "industry": _v(company_f), "inputs": [company_f],
                                         "basis": f"Industry average: {company_group}"} for u in units}
        # Segment results are struck before head-office costs; a peer's operating profit is after them.
        segment_sum = sum(_v(f[SEGMENT_RESULT]) for f in segments.values())
        ebit0 = _v(pbt_f) + (_v(get("FinanceCosts")) or 0.0) - (_v(get("OtherIncome")) or 0.0)
        if segment_sum > 0 and 0 < ebit0 < segment_sum:
            unallocated = _clamp(ebit0 / segment_sum, 0.5, 1.0)
            assume("segment_result_kept_after_unallocated_costs", unallocated, "ratio",
                   f"(Profit before exceptional items and tax + finance costs − other income) ÷ sum of segment results in FY{fy.year}: "
                   "the share of segment profit left after costs no segment carries. Applied to the sum of the parts.",
                   inputs=[pbt_f] + [f for f in (get("FinanceCosts"), get("OtherIncome")) if f is not None])

    for name, rows in forecast.items():
        s: dict = {"eps_1": rows[0]["eps"], "rows": rows}
        if wacc is not None and wacc > terminal + 0.01 and all(r["fcff"] is not None for r in rows):
            per_share, ev, tv_share = dcf_per_share(rows, wacc, terminal)
            s["dcf"] = per_share
            first_part = _clamp((rows[0]["end"] - today).days / 365, 0.0, 1.0)
            s["dcf_pv"] = [row["fcff"] * (first_part if i == 0 else 1.0) / (1 + wacc) ** max((row["end"] - today).days / 365 - 0.5 * (first_part if i == 0 else 1.0), 0.05)
                           for i, row in enumerate(rows)]
            s["dcf_ev"], s["dcf_terminal_share"] = ev, tv_share
            calc("valuation", "dcf_enterprise_value", ev, "INR", "discounted free cash flow to the firm + discounted terminal value", dimension=name,
                 attributes={"terminal_share": tv_share})
            calc("valuation", "dcf_value_per_share", per_share, "INR/share",
                 "(enterprise value less the minority share + assets outside the forecast) ÷ shares outstanding",
                 dimension=name, inputs=list(assumptions.values()) + bridge_facts + [shares_f])
        if multiples and len(multiples) == len(units):
            if "ev_ebit" not in out:
                out["ev_ebit"] = {n: scalar("ev_ebit_multiple", m["value"], unit=n) for n, m in multiples.items()}
            parts = [{"name": x["name"], "result": x["result"], "multiple": out["ev_ebit"][x["name"]], "basis": multiples[x["name"]]["basis"],
                      "industry": multiples[x["name"]]["industry"], "value": x["result"] * out["ev_ebit"][x["name"]]} for x in rows[0]["units"]]
            s["sotp_parts"] = parts
            s["sotp_unallocated"] = sum(p["value"] for p in parts) * (1 - unallocated)
            s["sotp"] = to_equity(sum(p["value"] for p in parts) * unallocated) / shares
            calc("valuation", "sotp_value_per_share", s["sotp"], "INR/share",
                 "(Σ year-1 segment result × EV ÷ EBIT of its line of business, less unallocated costs and the minority share, "
                 "+ assets outside the forecast) ÷ shares outstanding",
                 dimension=name, inputs=list(assumptions.values()) + [i for m in multiples.values() for i in m["inputs"]] + bridge_facts + [shares_f])
        if peer_pe:
            s["relative"] = peer_pe * rows[0]["eps"]
            calc("valuation", "peer_value_per_share", s["relative"], "INR/share", "peers' median price-to-earnings × year-1 earnings per share",
                 dimension=name, inputs=list(assumptions.values()) + [pe_f])
        lenses = [k for k in ("dcf", "sotp", "relative") if k in s]
        if lenses:
            weight = sum(BLEND[k] for k in lenses)
            s["weights"] = {k: BLEND[k] / weight for k in lenses}
            s["average"] = sum(s[k] * s["weights"][k] for k in lenses)
            s["gap"] = s["average"] / price - 1
            calc("valuation", "average_value_per_share", s["average"], "INR/share",
                 "blend of the lenses available at fixed weights (cash flow 40, sum of the parts 45, peer multiple 15, rescaled to those present); "
                 "the weights are a convention, not a statistical estimate",
                 dimension=name, attributes={"gap_to_price": s["gap"], "lenses": len(lenses), "weights": s["weights"]})
        out["scenarios"][name] = s

    if wacc is not None and "dcf" in out["scenarios"]["Base"]:
        grid = []
        for g in (terminal - 0.01, terminal - 0.005, terminal, terminal + 0.005, terminal + 0.01):
            line = []
            for w in (wacc - 0.01, wacc - 0.005, wacc, wacc + 0.005, wacc + 0.01):
                value = dcf_per_share(forecast["Base"], w, g)[0] if w > g + 0.01 else None
                line.append(value)
                if value is not None:
                    calc("valuation", "dcf_sensitivity", value, "INR/share", "Base-case discounted cash flow at this cost of capital and terminal growth",
                         dimension=f"wacc={w:.4f}|g={g:.4f}")
            grid.append({"g": g, "values": line})
        out["sensitivity"] = {"waccs": [wacc - 0.01, wacc - 0.005, wacc, wacc + 0.005, wacc + 0.01], "rows": grid}
    parts = out["scenarios"]["Base"].get("sotp_parts") or []
    if len(parts) >= 2:
        first, second = sorted(parts, key=lambda x: -x["value"])[:2]
        rest = sum(x["value"] for x in parts) - first["value"] - second["value"]
        steps = (0.8, 0.9, 1.0, 1.1, 1.2)
        out["sotp_sensitivity"] = {
            "across": first["name"], "down": second["name"], "across_multiples": [first["multiple"] * k for k in steps],
            "rows": [{"multiple": second["multiple"] * j,
                      "values": [to_equity((first["result"] * first["multiple"] * k + second["result"] * second["multiple"] * j + rest) * unallocated) / shares
                                 for k in steps]} for j in steps]}

    # One assumption fact per override in force, beside (never instead of) the system's own estimate.
    seen = set()
    for a in applied:
        key = (a["metric"], a["unit"], a["scenario"], a["year"])
        if key in seen:
            continue
        seen.add(key)
        fact = record_fact(
            db, scope="COMPANY", company_id=company_id, fact_type="assumption", key=f"override:{a['metric']}",
            dimension=f"{a['scenario']}|{a['unit']}|{a['year'] or 'all years'}", statement_type=basis, value_num=a["value"],
            unit="ratio" if a["metric"] not in ("beta", "peer_price_to_earnings", "ev_ebit_multiple") else "x",
            attributes={"source_type": "ANALYST_OVERRIDE", "system_value": a["system"], "override_id": a["id"]},
            nature="ANALYST_ASSUMPTION", extraction_method="ANALYST_OVERRIDE", source_tier=3, confidence="LOW",
            formula=a["reason"], replace=False)
        fact.verification_status = "ASSUMPTION"
    distinct: dict = {}
    # One line per stored rule, showing the Base-case figures where the rule applies to every scenario.
    for a in sorted(applied, key=lambda a: a["scenario"] not in ("Base", "All")):
        distinct.setdefault(a["id"] or (a["metric"], a["unit"], a["scenario"], a["year"]), a)
    rule_by_id = {getattr(o, "id", None): o for o in rules}
    out["overrides"] = [{**a, "scenario": getattr(rule_by_id.get(a["id"]), "scenario", a["scenario"]),
                         "year": getattr(rule_by_id.get(a["id"]), "fiscal_year", a["year"])} for a in distinct.values()]
    out["grid"], out["scalars"] = paths, scalars

    out.update({
        "price": price, "price_date": price_f.period_end, "fy": fy, "basis": basis, "net_liquid": net_liquid, "shares": shares,
        "sotp_unallocated": unallocated, "sheet0": sheet0, "associates": associates, "pe_parts": pe_parts, "payout": payout, "liquid0": liquid0, "roc": locals().get("roc"),
        "equity_bridge": {"items": bridge_items, "added": added, "minority": minority, "fact_ids": [f.id for f in bridge_facts]},
        "deals": {k: [{**{x: y for x, y in d.items() if x != "facts"}, "fact_ids": [f.id for f in d["facts"]]} for d in v] for k, v in deals.items()},
        "peer_pe": peer_pe, "peer_count": len(peer_pes), "units": units, "tax_rate": tax_rate, "bridge": bridge,
        "ratios": {"capex": capex_ratio, "depreciation": da_ratio, "working_capital": wc_ratio},
        "assumption_ids": [f.id for f in assumptions.values()],
    })
    return out
