"""Phase 5 — the assessment: a risk register and monitoring triggers
derived by rule from the facts in the report, and a short narrative.

The narrative is the only place an LLM writes. It is given a pack of
already-computed statements and may use no number that is not in the pack:
any other figure in its answer causes the whole answer to be discarded and
the rule-written narrative to be used instead. It never sees or changes an
assumption.
"""
from __future__ import annotations

import json
import re

from app.logger import logger

_QUESTIONS = (
    ("business", "What is this business?"),
    ("profit_engine", "Where does the profit come from?"),
    ("changing", "What is changing?"),
    ("risks", "What could go wrong?"),
    ("valuation", "What is the valuation saying?"),
)
_SYSTEM = (
    "You are an equity research editor. Write plain, specific prose from the evidence pack only. Rules: use no number, "
    "name or fact that is not in the pack; copy figures exactly as written; no recommendation, no price target, no "
    "adjectives of praise; say 'the model' for forecasts and 'management said' for guidance. Return JSON with exactly these "
    'keys, each two or three sentences: {"business": "", "profit_engine": "", "changing": "", "risks": "", "valuation": ""}.'
)


def _cr(v) -> str:
    return f"₹{v:,.0f} crore"


def _pct(v, d: int = 0) -> str:
    return f"{v * 100:.{d}f}%"


def build_risks(r: dict) -> list[dict]:
    """Each risk is a threshold crossed by a figure already in the report."""
    risks: list[dict] = []

    def add(kind: str, severity: str, text: str, cites=None) -> None:
        risks.append({"kind": kind, "severity": severity, "text": text, "cites": cites or []})

    segments = r["segments"][0] if r["segments"] else None
    if segments:
        top = segments["top"]
        if (top["result_share"] or 0) >= 0.6:
            add("Business concentration", "High" if top["result_share"] >= 0.75 else "Medium",
                f"{top['name']} earns {_pct(top['result_share'])} of segment profit. A setback there cannot be offset by the rest of the group.",
                segments["cites"])
        falling = []
        for h in segments["history"]:
            margins = [x["margin"] for x in h["series"] if x["margin"] is not None]
            if len(margins) >= 3 and margins[0] - margins[-1] >= 0.03:
                falling.append(f"{h['name']} from {_pct(margins[0], 1)} to {_pct(margins[-1], 1)}")
        if falling:
            add("Margin erosion", "Medium", "Segment margin has fallen over the years on file: " + "; ".join(falling[:4]) + ".", segments["cites"])
    cash = r["cash"]["latest"]
    if cash:
        if cash["cover"] is not None and cash["cover"] < 1:
            add("Payout above cash generated", "Medium",
                f"In {cash['label']} free cash flow covered cash dividends {cash['cover']:.2f} times; the shortfall was met from the balance sheet.", r["cash"]["cites"])
        if cash["conversion"] is not None and cash["conversion"] < 0.7:
            add("Weak cash conversion", "Medium", f"Operating cash flow was {cash['conversion']:.2f} times profit after tax in {cash['label']}.", r["cash"]["cites"])
        if cash["debt_to_equity"] is not None and cash["debt_to_equity"] > 1:
            add("Leverage", "High" if cash["debt_to_equity"] > 2 else "Medium", f"Borrowings are {cash['debt_to_equity']:.2f} times equity at {cash['label']}.", r["cash"]["cites"])
    for n in r["normalisation"][:3]:
        if abs(n["value"]) >= 0.05 * abs((r["latest_fy"] or {}).get("profit") or 1e18):
            add("Earnings not comparable", "Medium", f"{n['period']}: {n['item'].lower()} of {_cr(n['value'])} distorts that year's profit.", n["cites"])
    business = r["business"]
    if business.get("export_share") and business["export_share"] >= 0.5:
        add("Export dependence", "Medium", f"Exports are {_pct(business['export_share'])} of turnover: currency and overseas regulation matter.", business["cites"])
    for c in business.get("concentration", []):
        if c["is_ratio"] and c["value"] and c["value"] >= 0.25 and ("related" in c["label"].lower() or "top ten" in c["label"].lower()):
            add("Counterparty concentration", "Medium", f"{c['label']}: {_pct(c['value'])}.", business["cites"])
    kinds: dict[str, int] = {}
    for e in r["events"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    if kinds.get("Regulatory order", 0) + kinds.get("Litigation", 0) >= 2:
        add("Regulatory and legal", "Medium",
            f"{kinds.get('Regulatory order', 0)} regulatory-order and {kinds.get('Litigation', 0)} litigation disclosures in the recent filings listed.", r["event_cites"])
    if kinds.get("Acquisition", 0) >= 4:
        add("Acquisition integration", "Low", f"{kinds['Acquisition']} acquisition disclosures in the recent filings listed; each has to earn its cost.", r["event_cites"])
    for b in r.get("insurers", []):
        if b["is_subject"]:
            if b["combined_ratio"] is not None and b["combined_ratio"] > 1:
                add("Underwriting loss", "High" if b["combined_ratio"] > 1.10 else "Medium",
                    f"Combined ratio is {_pct(b['combined_ratio'], 1)}: claims and expenses exceed premium, so profit depends on investment income.", b["cites"])
            if b["solvency_multiple"] is not None and b["solvency_multiple"] < 1.8:
                add("Thin solvency", "Medium", f"Solvency is {b['solvency_multiple']:.2f} times required capital.", b["cites"])
            if b["persistency_13th_month"] is not None and b["persistency_13th_month"] < 0.80:
                add("Policy lapses", "Medium", f"Only {_pct(b['persistency_13th_month'], 1)} of policies are still paying after 13 months.", b["cites"])
    for b in r["lenders"]:
        if b["is_subject"]:
            if b["gnpa"] is not None and b["gnpa"] >= 0.03:
                add("Asset quality", "High", f"Gross bad loans are {_pct(b['gnpa'], 2)} of advances.", b["cites"])
            if b["cet1"] is not None and b["cet1"] < 0.13:
                add("Thin capital", "Medium", f"Core capital ratio is {_pct(b['cet1'], 1)}.", b["cites"])
            if b["cti"] is not None and b["cti"] >= 0.55:
                add("Cost base", "Medium", f"Costs take {_pct(b['cti'])} of income.", b["cites"])
            if b["cd"] is not None and b["cd"] >= 0.9:
                add("Funding stretch", "Medium", f"Advances are {_pct(b['cd'])} of deposits; growth depends on raising deposits.", b["cites"])
    v = r["valuation"]
    if "skipped" not in v:
        base = v["scenarios"]["Base"]
        lenses = [base[k] for k in ("dcf", "sotp", "relative") if k in base]
        if len(lenses) > 1 and max(lenses) / min(lenses) >= 1.5:
            add("Valuation uncertainty", "High" if max(lenses) / min(lenses) >= 2 else "Medium",
                f"The valuation methods span ₹{min(lenses):,.0f} to ₹{max(lenses):,.0f} a share: the answer depends on the method chosen.")
        if base.get("dcf_terminal_share", 0) >= 0.7:
            add("Value rests on the distant future", "Medium", f"{_pct(base['dcf_terminal_share'])} of the cash-flow value comes from beyond year five.")
        if not v["overrides"] and r["normalisation"]:
            add("Unchallenged model", "Medium",
                "The forecast extrapolates history that contains one-off items, and no assumption has been reviewed by an analyst.")
    if not business["available"]:
        add("Thin disclosure", "Low", "No business responsibility report is filed, so activity mix, markets and concentration are not disclosed in data form.")
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(risks, key=lambda x: order[x["severity"]])


def build_triggers(r: dict) -> dict:
    """What to check in each new filing: the Bull and Bear assumptions restated as thresholds."""
    v = r["valuation"]
    out = {"bullish": [], "bearish": [], "watch": []}
    if "skipped" in v:
        return out
    year = v["scenarios"]["Base"]["rows"][0]["label"]
    grid = {(g["unit"], g["metric"], g["scenario"]): g for g in v["grid"] if g["year"] == v["scenarios"]["Base"]["rows"][0]["end"].year}
    units = sorted(v["units"], key=lambda u: -(u["revenue0"] * u["margin"]))[:3]
    for u in units:
        name = "Company" if u["name"] == "Company" else u["name"]
        for metric, word in (("revenue_growth", "revenue growth"), ("margin", "margin")):
            bull, bear, base = (grid.get((u["name"], metric, s)) for s in ("Bull", "Bear", "Base"))
            if not (bull and bear and base):
                continue
            out["bullish"].append(f"{name} {word} above {_pct(bull['active'], 1)} in {year} (model assumes {_pct(base['active'], 1)})")
            out["bearish"].append(f"{name} {word} below {_pct(bear['active'], 1)} in {year}")
    cash = r["cash"]["latest"]
    if cash and cash["cover"] is not None:
        (out["bullish"] if cash["cover"] < 1 else out["watch"]).append("Free cash flow covering cash dividends at least 1.00 times" if cash["cover"] < 1
                                                                      else f"Dividend cover holding above 1.00 times (last {cash['cover']:.2f})")
        if cash["cover"] < 1:
            out["bearish"].append(f"Dividend cover falling further below {cash['cover']:.2f} times")
    for b in r.get("insurers", []):
        if b["is_subject"] and b["combined_ratio"] is not None:
            out["bullish"].append(f"Combined ratio falling below {_pct(min(b['combined_ratio'] - 0.02, 1.0), 1)}")
            out["bearish"].append(f"Combined ratio rising above {_pct(b['combined_ratio'] + 0.02, 1)}")
        if b["is_subject"] and b["persistency_13th_month"] is not None:
            out["bullish"].append(f"13th-month persistency rising above {_pct(b['persistency_13th_month'] + 0.01, 1)}")
            out["bearish"].append(f"13th-month persistency falling below {_pct(b['persistency_13th_month'] - 0.02, 1)}")
        if b["is_subject"] and b["solvency_multiple"] is not None:
            out["watch"].append(f"Solvency holding above 1.80 times (last {b['solvency_multiple']:.2f})")
    for b in r["lenders"]:
        if b["is_subject"] and b["gnpa"] is not None:
            out["bearish"].append(f"Gross bad loans rising above {_pct(b['gnpa'] + 0.005, 2)} of advances")
            out["bullish"].append(f"Cost-to-income falling below {_pct(b['cti'] - 0.02)}" if b["cti"] else "Cost-to-income falling")
    for e in r["events"][:3]:
        out["watch"].append(f"{e['kind']} disclosed {e['date']:%d %b %Y}: completion, cost and first reported contribution")
    if r["guidance"]:
        out["watch"].append("Whether management repeats, raises or lowers the guidance quoted in this report at the next earnings call")
    out["watch"].append("Any new exceptional item, discontinued operation or scheme of arrangement in the next results filing")
    return out


def _pack(r: dict, risks: list[dict]) -> dict:
    """The only material the LLM is given: finished statements with their numbers."""
    lf, v = r["latest_fy"] or {}, r["valuation"]
    pack = {
        "company": r["stock"].company_name, "industry": r["basic_industry"],
        "activities": [f"{a['name'][:90]}: {_pct(a['share'], 1)} of turnover" for a in r["business"].get("activities", [])[:5]],
        "markets": (f"{r['business']['states']:.0f} Indian states, {r['business']['countries']:.0f} countries, exports {_pct(r['business']['export_share'], 1)} of turnover"
                    if r["business"].get("states") is not None and r["business"].get("export_share") is not None else None),
        "latest_year": (f"{lf.get('label')}: revenue {_cr(lf['revenue'])}, revenue growth {lf['revenue_growth'] * 100:+.1f}%, profit after tax {_cr(lf['profit'])}"
                        if lf.get("revenue") and lf.get("profit") is not None and lf.get("revenue_growth") is not None else None),
        "segments": [f"{s['name']}: {_pct(s['revenue_share'])} of segment revenue, {_pct(s['result_share'])} of segment profit, margin {_pct(s['margin'], 1)}"
                     for s in (r["segments"][0]["rows"] if r["segments"] else []) if s["revenue_share"] is not None and s["result_share"] is not None and s["margin"] is not None],
        "single_segment": r["single_segment"],
        "cash": (f"{r['cash']['latest']['label']}: free cash flow {_cr(r['cash']['latest']['fcf'])}, dividends {_cr(r['cash']['latest']['dividends'])}, cover {r['cash']['latest']['cover']:.2f} times"
                 if r["cash"]["latest"] and r["cash"]["latest"]["cover"] is not None else None),
        "one_offs": [f"{n['period']}: {n['item']} {_cr(n['value'])}" for n in r["normalisation"][:4]],
        "recent_events": [f"{e['date']:%b %Y}: {e['text'][:170]}" for e in r["events"][:4]],
        "management_said": [g["text"][:200] for g in r["guidance"][:2]],
        "risks": [x["text"] for x in risks[:6]],
    }
    if "skipped" not in v:
        base = v["scenarios"]["Base"]
        pack["model"] = {
            "next_year_profit": f"{base['rows'][0]['label']} profit after tax {_cr(base['rows'][0]['pat'] / 1e7)} in the Base case",
            "values_per_share": {k: f"₹{base[key]:,.0f}" for k, key in (("discounted cash flow", "dcf"), ("sum of the parts", "sotp"), ("peer multiple", "relative")) if key in base},
            "price": f"₹{v['price']:,.2f}",
            "analyst_overrides": len(v["overrides"]),
        }
    return {k: val for k, val in pack.items() if val}


def _numbers(text: str) -> set[str]:
    return {m.replace(",", "").rstrip(".") for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}


def rule_narrative(r: dict, risks: list[dict]) -> dict:
    p = _pack(r, risks)
    seg = p.get("segments") or []
    model = p.get("model") or {}
    values = model.get("values_per_share") or {}
    return {
        "business": " ".join(x for x in (
            f"{p['company']} is classified by the exchange under {p['industry']}.",
            ("Its reported activities are " + "; ".join(p["activities"][:3]) + ".") if p.get("activities") else None,
            (f"It sells in {p['markets']}.") if p.get("markets") else None) if x),
        "profit_engine": (("By segment: " + "; ".join(seg[:3]) + ".") if seg else
                          (f"The company reports one segment ({p['single_segment']}), so its filings do not show where within the business the profit is earned."
                           if p.get("single_segment") else "The filings on record do not break profit down by segment.")) + (f" {p['latest_year']}." if p.get("latest_year") else ""),
        "changing": (("Recent disclosures: " + "; ".join(p["recent_events"][:3]) + ".") if p.get("recent_events") else "No acquisition, restructuring or scheme has been disclosed in the recent filings on record.")
                    + ((" One-off items: " + "; ".join(p["one_offs"][:2]) + ".") if p.get("one_offs") else ""),
        "risks": " ".join(p["risks"][:3]) if p.get("risks") else "None of the report's risk thresholds is crossed by the figures on file.",
        "valuation": ((f"The model's Base case gives " + ", ".join(f"{val} by {k}" for k, val in values.items()) + f", against a price of {model['price']}. ") if values else "No valuation was computed. ")
                     + (f"{model['analyst_overrides']} assumption(s) carry an analyst override." if model.get("analyst_overrides") else "No assumption has been reviewed by an analyst."),
    }


def write_narrative(r: dict, risks: list[dict]) -> dict:
    """LLM narrative if it stays within the pack's numbers, otherwise the rule-written one."""
    pack = _pack(r, risks)
    fallback = {"sections": rule_narrative(r, risks), "author": "rules"}
    # The same evidence gives the same narrative: one that passed the number check is kept and reused, so opening a
    # report again costs no model tokens (the model's daily allowance is small) and the text does not change between opens.
    import hashlib
    from pathlib import Path

    from app.config import config
    packed = json.dumps(pack, ensure_ascii=False, default=str, sort_keys=True)
    cache = Path(config.reports_dir).resolve() / ".narratives" / f"{hashlib.sha256(packed.encode()).hexdigest()[:32]}.json"
    if cache.exists():
        try:
            return {"sections": json.loads(cache.read_text()), "author": "llm"}
        except (OSError, ValueError):
            pass
    try:
        from app.llm.client import LLMClient
        # Plain mode with room to think: this model's JSON mode returns nothing when its reasoning uses up a small budget.
        raw = LLMClient().chat(_SYSTEM, json.dumps(pack, ensure_ascii=False, default=str), max_tokens=3000)
        match = re.search(r"\{.*\}", raw or "", re.S)
        answer = json.loads(match.group(0)) if match else None
    except Exception as e:  # noqa: BLE001
        logger.warning("bie: narrative LLM call failed", error=str(e))
        return fallback
    if not isinstance(answer, dict) or any(not isinstance(answer.get(k), str) or len(answer[k]) < 40 for k, _ in _QUESTIONS):
        return fallback
    allowed = _numbers(json.dumps(pack, ensure_ascii=False, default=str))
    used = _numbers(" ".join(answer[k] for k, _ in _QUESTIONS))
    stray = {n for n in used - allowed if not (n.isdigit() and int(n) <= 5)}
    if stray:
        logger.warning("bie: narrative used numbers not in the evidence, discarded", numbers=sorted(stray)[:8])
        return {**fallback, "rejected": sorted(stray)[:8]}
    sections = {k: answer[k].strip() for k, _ in _QUESTIONS}
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(sections, ensure_ascii=False))
    except OSError:
        pass
    return {"sections": sections, "author": "llm"}


def build_assessment(r: dict) -> dict:
    risks = build_risks(r)
    narrative = write_narrative(r, risks)
    return {"risks": risks, "triggers": build_triggers(r), "narrative": narrative,
            "questions": [{"q": q, "a": narrative["sections"][k]} for k, q in _QUESTIONS]}
