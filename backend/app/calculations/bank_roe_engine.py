"""ROE -> book value -> P/B engine for lenders (banks, NBFCs, HFCs, MFIs).

Ports the mentor's IDFC FIRST "ROE Simulator" (idfc-first-roe-simulator.html)
so our bank analysis uses the SAME method, not a new one. His method:

  * Equity compounds at ROE x (1 - payout). That is the only self-funded
    growth a lender has:  self_funded_growth = ROE x (1 - payout).
  * Balance-sheet growth above that must be funded by FRESH SHARES, issued at
    BVPS x P/B x (1 - placement discount). Dilution is charged to the holder.
  * Price = BVPS x P/B. P/B re-rates in step with ROE progress (not on hope).
  * ROE ramps in a straight line to a terminal value over N years, then holds.
  * Return attribution is exactly: book-value compounding x multiple re-rating.
  * "Crossover ROE" = growth / (1 - payout): the ROE at which the bank stops
    needing new shares.

`simulate()` is line-for-line the JS `simulate()` (same ramp, same raise rule,
same issue price, same cumulative-dividend total return) so outputs match his
page for the same inputs (tested against his IDFC numbers).

Additions beyond the mentor's page, from Financial_Services_Analysis_
Framework.md sections 5.6/18/24/28 ("ROE = ROA x leverage", "ROE-adjusted
P/B", "if ROE increased: ROA, leverage, credit cost, ..."):
DuPont history, justified P/B and market-implied ROE (Gordon), implied
share-count dilution history, and a live quarterly checklist. All are
labelled as calculations/heuristics, never as reported figures.

Units: shares in crore, money in INR crore, per-share in INR (mentor's units).
"""
from __future__ import annotations

# Mentor's own preset cases, used as the ROE -> exit-P/B anchor curve so the
# multiple a target ROE "earns" matches how he priced it: bear 7% -> 1.0x,
# as-is 9% -> 1.1x, management 15% -> 2.2x, best case 17% -> 3.0x.
PB_ANCHORS = [(7.0, 1.0), (9.0, 1.1), (15.0, 2.2), (17.0, 3.0)]
HORIZON = 10

# Default cost of equity / long-run growth for the Gordon cross-check only —
# they never drive the simulation (the mentor's exit P/B is an explicit input).
DEFAULT_COE = 12.0
DEFAULT_LT_GROWTH = 7.0


def pb_for_roe(roe_pct: float) -> float:
    """Piecewise-linear over the mentor's anchor cases, flat outside them."""
    pts = PB_ANCHORS
    if roe_pct <= pts[0][0]:
        return pts[0][1]
    if roe_pct >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= roe_pct <= x1:
            return y0 + (y1 - y0) * (roe_pct - x0) / (x1 - x0)
    return pts[-1][1]


def sustainable_growth(roe_pct: float, payout_pct: float) -> float:
    """Self-funded growth % = ROE x (1 - payout)."""
    return roe_pct * (1 - payout_pct / 100.0)


def crossover_roe(growth_pct: float, payout_pct: float) -> float | None:
    """ROE at which growth is fully self-funded; None if payout is 100%."""
    keep = 1 - payout_pct / 100.0
    return growth_pct / keep if keep > 0 else None


def justified_pb(roe_pct: float, coe_pct: float = DEFAULT_COE, g_pct: float = DEFAULT_LT_GROWTH) -> float | None:
    """Gordon: P/B = (ROE - g) / (COE - g). None when COE <= g."""
    if coe_pct <= g_pct:
        return None
    return (roe_pct - g_pct) / (coe_pct - g_pct)


def implied_roe(pb: float, coe_pct: float = DEFAULT_COE, g_pct: float = DEFAULT_LT_GROWTH) -> float | None:
    """The ROE the current P/B is pricing in (inverse of justified_pb)."""
    if coe_pct <= g_pct:
        return None
    return g_pct + pb * (coe_pct - g_pct)


def verdict_of(x: float) -> str:
    """The mentor's verdict bands on the total price multiple."""
    if x < 1.3:
        return "Dead money"
    if x < 2.0:
        return "Underwhelming — below a fixed deposit's cousin"
    if x < 3.0:
        return "Modest compounder"
    if x < 5.0:
        return "Strong compounder"
    if x < 10.0:
        return "Multibagger territory"
    return "Rare outcome — check your assumptions twice"


def simulate(start: dict, p: dict) -> dict:
    """Line-for-line port of the mentor's JS `simulate()`.

    start: {px0, bv0, sh0, roe0(fraction)}; p: {roe, yrs, g, pay, pb, disc}
    all in percent except pb (multiple) and yrs (years)."""
    px0, bv0, sh0, roe0 = start["px0"], start["bv0"], start["sh0"], start["roe0"]
    eq0 = bv0 * sh0
    pb0 = px0 / bv0
    roe_t, g, pay, disc = p["roe"] / 100, p["g"] / 100, p["pay"] / 100, p["disc"] / 100
    yrs = max(float(p["yrs"]), 1.0)

    eq, sh, raised, cum_div = eq0, sh0, 0.0, 0.0
    rows = []
    for y in range(1, HORIZON + 1):
        roe = roe0 + (roe_t - roe0) * min(y / yrs, 1)
        if roe_t != roe0:
            prog = (roe - roe0) / (roe_t - roe0)
        else:
            prog = min(y / yrs, 1)
        prog = max(0.0, min(1.0, prog))
        pb = pb0 + (p["pb"] - pb0) * prog

        opening = eq
        pat = opening * roe
        div = pat * pay
        cum_div += div / sh
        eq = opening + pat - div

        need = opening * (1 + g)  # equity required to hold capital ratios
        raise_ = max(0.0, need - eq)
        if raise_ > 0:
            issue_px = (eq / sh) * pb * (1 - disc)
            sh += raise_ / issue_px
            eq += raise_
            raised += raise_
        bvps, eps = eq / sh, pat / sh
        px = bvps * pb
        rows.append({
            "year": y, "roe": roe, "pb": pb, "pat": pat, "raise": raise_, "shares": sh,
            "bvps": bvps, "eps": eps, "price": px, "multiple": px / px0,
            "total_return_multiple": (px + cum_div) / px0,
            "cagr": (px / px0) ** (1 / y) - 1,
        })
    last = rows[-1]
    self_g = sustainable_growth(p["roe"], p["pay"])
    return {
        "params": p, "rows": rows,
        "raised": raised, "dilution": sh / sh0 - 1, "end_shares": sh,
        "verdict": verdict_of(last["multiple"]),
        "attribution": {
            "book_value_compounding": last["bvps"] / bv0,
            "multiple_rerating": last["pb"] / pb0,
            "total": last["multiple"],
        },
        "self_funded_growth": self_g,
        "growth_gap": max(0.0, p["g"] - self_g),
        "crossover_roe": crossover_roe(p["g"], p["pay"]),
    }


def default_presets(start: dict, payout_pct: float, growth_pct: float) -> list[dict]:
    """Preset cases parameterised off the company's own state. Shapes mirror
    the mentor's five chips; P/B for each target ROE comes from his anchors."""
    roe0 = start["roe0"] * 100
    g = float(min(max(round(growth_pct), 5), 25))
    pay = float(round(payout_pct))
    tgt = 15.0
    presets = [
        {"key": "asis", "name": "As-is, nothing changes",
         "params": {"roe": round(roe0, 1), "yrs": 5, "g": g, "pay": pay, "pb": round(max(1.0, pb_for_roe(roe0)), 1), "disc": 5}},
        {"key": "mature", "name": "Reaches mature-bank ROE (15%)",
         "params": {"roe": tgt, "yrs": 5, "g": g, "pay": pay, "pb": round(pb_for_roe(tgt), 1), "disc": 5}},
        {"key": "self", "name": "Slower, self-funded",
         "params": {"roe": tgt, "yrs": 5, "g": float(int(sustainable_growth(tgt, pay))), "pay": pay, "pb": round(pb_for_roe(tgt), 1), "disc": 5}},
        {"key": "bull", "name": "Best case",
         "params": {"roe": 17.0, "yrs": 4, "g": min(g + 2, 25.0), "pay": max(pay - 2, 0.0), "pb": round(pb_for_roe(17.0), 1), "disc": 5}},
        {"key": "bear", "name": "It slips back",
         "params": {"roe": max(round(roe0) - 2, 4.0), "yrs": 5, "g": max(g - 3, 5.0), "pay": pay, "pb": 1.0, "disc": 10}},
    ]
    return presets


def _avg(a, b):
    return (a + b) / 2 if a is not None and b is not None else None


def _dupont_history(equity: dict, assets: dict, net_income: dict) -> list[dict]:
    """ROE = ROA x leverage, per FY, on AVERAGE balances (needs prior year)."""
    fys = sorted(k for k in net_income if net_income.get(k) is not None and equity.get(k) is not None)
    out = []
    for fy in fys:
        prev = f"FY{int(fy[2:]) - 1}"
        avg_eq = _avg(equity.get(fy), equity.get(prev))
        avg_as = _avg(assets.get(fy), assets.get(prev))
        ni = net_income[fy]
        if not avg_eq or not avg_as:
            continue
        roe, roa = ni / avg_eq * 100, ni / avg_as * 100
        out.append({"fy": fy, "roe": roe, "roa": roa, "leverage": avg_as / avg_eq,
                    "equity_growth": ((equity[fy] / equity[prev] - 1) * 100) if equity.get(prev) else None})
    return out


def _share_history(equity: dict, bvps_by_fy: dict) -> list[dict]:
    """Implied shares (crore) = equity / BVPS per FY — the only share-count
    history available without a filings feed — and YoY change."""
    out, prev = [], None
    for fy in sorted(bvps_by_fy):
        eq, bv = equity.get(fy), bvps_by_fy[fy]
        if not eq or not bv:
            continue
        sh_cr = eq / bv / 1e7
        out.append({"fy": fy, "shares_cr": sh_cr,
                    "yoy_pct": ((sh_cr / prev - 1) * 100) if prev else None})
        prev = sh_cr
    return out


def compute_bank_roe_analysis(inp: dict) -> dict:
    """inp keys (all optional except price/bvps/shares):
      price, bvps, shares (absolute count), payout_ratio (fraction), trailing_eps,
      equity {FY: INR}, assets {FY: INR}, net_income {FY: INR}   (yfinance, absolute INR)
      quarterly_pat_cr [(period, INR cr)]  oldest->newest, preferred STANDALONE
      bvps_by_fy {FY: INR/share}, ratios {credit_cost, cost_to_income_ratio, roa, ...}
    Returns a JSON-safe dict; missing inputs degrade to nulls, never zeros."""
    price, bvps, shares = inp.get("price"), inp.get("bvps"), inp.get("shares")
    if not price or not bvps or not shares:
        return {"available": False, "reason": "price, book value per share and share count are required"}

    sh_cr = shares / 1e7
    eq_cr = bvps * sh_cr
    pb = price / bvps
    payout_pct = (inp.get("payout_ratio") or 0.0) * 100
    equity, assets, ni = inp.get("equity") or {}, inp.get("assets") or {}, inp.get("net_income") or {}

    dupont = _dupont_history(equity, assets, ni)
    latest_fy = dupont[-1] if dupont else None

    # Run-rate ROE: latest quarter annualised over CURRENT equity (mentor's
    # "Q1 FY27 annualised"); else trailing EPS x shares; else last FY average-equity ROE.
    q = inp.get("quarterly_pat_cr") or []
    run_rate_source, roe_run = None, None
    if q:
        roe_run = q[-1][1] * 4 / eq_cr * 100
        run_rate_source = f"{q[-1][0]} PAT x4 / current equity"
    elif inp.get("trailing_eps"):
        roe_run = inp["trailing_eps"] * sh_cr / eq_cr * 100
        run_rate_source = "trailing EPS x shares / current equity (understates a fast-improving bank)"
    elif latest_fy:
        roe_run, run_rate_source = latest_fy["roe"], f"{latest_fy['fy']} average-equity ROE"
    if roe_run is None:
        return {"available": False, "reason": "no earnings data to derive ROE"}

    ttm_pat_cr = inp["trailing_eps"] * sh_cr if inp.get("trailing_eps") else None
    balance_growth = None
    if len(assets) >= 2:
        ks = sorted(assets)
        if assets.get(ks[-1]) and assets.get(ks[-2]):
            balance_growth = (assets[ks[-1]] / assets[ks[-2]] - 1) * 100
    growth_setting = balance_growth if balance_growth is not None else 15.0

    start = {"px0": price, "bv0": bvps, "sh0": sh_cr, "roe0": roe_run / 100}
    self_g = sustainable_growth(roe_run, payout_pct)

    coe, g_lt = DEFAULT_COE, DEFAULT_LT_GROWTH
    j_pb = justified_pb(roe_run, coe, g_lt)
    imp_roe = implied_roe(pb, coe, g_lt)

    shares_hist = _share_history(equity, inp.get("bvps_by_fy") or {})
    presets = default_presets(start, payout_pct, growth_setting)
    sims = [dict(simulate(start, ps["params"]), key=ps["key"], name=ps["name"]) for ps in presets]

    r = inp.get("ratios") or {}
    q_roe = None
    if len(q) >= 5:
        q_roe = [{"period": p_, "annualised_roe": v * 4 / eq_cr * 100} for p_, v in q[-6:]]
    checklist = [
        {"key": "roe", "title": "ROE trajectory",
         "why": "Is it walking up quarter after quarter? One quarter proves nothing; four in a row prove a lot.",
         "value": round(roe_run, 1), "unit": "% run-rate", "series": q_roe},
        {"key": "cost_to_income", "title": "Cost-to-income",
         "why": "Reported vs incremental. The gap closes only if income grows faster than cost.",
         "value": r.get("cost_to_income_ratio"), "unit": "%"},
        {"key": "roa", "title": "Return on assets",
         "why": "Holding above ~1% through a full year, not just one good quarter.",
         "value": r.get("roa") if r.get("roa") is not None else (round(latest_fy["roa"], 2) if latest_fy else None), "unit": "%"},
        {"key": "credit_cost", "title": "Credit cost",
         "why": "Normalising after a clean-up, or creeping back up.",
         "value": r.get("credit_cost"), "unit": "%"},
        {"key": "share_count", "title": "Share count",
         "why": "The quietest number on the page. Watch YoY change every quarter.",
         "value": shares_hist[-1]["yoy_pct"] if shares_hist else None, "unit": "% YoY (implied)"},
        {"key": "raise_terms", "title": "Terms of any raise",
         "why": "Not just how much, but at what price and what the money earns once deployed.",
         "value": None, "unit": None},
        {"key": "governance", "title": "Internal controls",
         "why": "A bank runs on trust; governance is a number too, it just has no decimal.",
         "value": None, "unit": None},
    ]

    insights = []
    gap = growth_setting - self_g
    if gap > 0:
        insights.append(
            f"At {roe_run:.1f}% ROE and {payout_pct:.0f}% payout the bank funds about {self_g:.1f}% growth from "
            f"retained profit against ~{growth_setting:.0f}% balance-sheet growth — a {gap:.1f}-point gap that has "
            f"to come from new shares. It needs ~{crossover_roe(growth_setting, payout_pct):.1f}% ROE to stop asking.")
    else:
        insights.append(
            f"At {roe_run:.1f}% ROE the bank funds ~{self_g:.1f}% growth from retained profit, covering the "
            f"~{growth_setting:.0f}% balance-sheet growth without new equity.")
    if imp_roe is not None:
        insights.append(
            f"P/B of {pb:.2f}x prices in ~{imp_roe:.1f}% sustainable ROE (COE {coe:.0f}%, long-run growth {g_lt:.0f}%) "
            f"versus a {roe_run:.1f}% run-rate — the market is paying for improvement, not current earnings."
            if imp_roe > roe_run + 1 else
            f"P/B of {pb:.2f}x prices in ~{imp_roe:.1f}% sustainable ROE, at or below the {roe_run:.1f}% run-rate.")
    if shares_hist and shares_hist[-1]["yoy_pct"] is not None and shares_hist[-1]["yoy_pct"] > 5:
        insights.append(f"Implied share count rose {shares_hist[-1]['yoy_pct']:.0f}% in {shares_hist[-1]['fy']} — dilution has been eating per-share returns.")

    return {
        "available": True,
        "start": {
            "price": price, "bvps": bvps, "shares_cr": sh_cr, "equity_cr": eq_cr, "pb": pb,
            "run_rate_roe": roe_run, "run_rate_source": run_rate_source,
            "ttm_pat_cr": ttm_pat_cr, "ttm_pe": (price / inp["trailing_eps"]) if inp.get("trailing_eps") else None,
            "payout_pct": payout_pct, "market_cap_cr": price * sh_cr, "balance_sheet_growth_pct": balance_growth,
            "eps_ttm": inp.get("trailing_eps"),
        },
        "sustainability": {
            "self_funded_growth": self_g, "balance_sheet_growth": balance_growth,
            "gap": (balance_growth - self_g) if balance_growth is not None else None,
            "crossover_roe": crossover_roe(growth_setting, payout_pct),
        },
        "dupont": dupont[-5:],
        "valuation_check": {
            "coe": coe, "long_run_growth": g_lt, "justified_pb_at_run_rate": j_pb,
            "market_implied_roe": imp_roe, "pb_anchor_for_run_rate_roe": pb_for_roe(roe_run),
        },
        "share_history": shares_hist[-5:],
        "pb_anchors": [{"roe": a, "pb": b} for a, b in PB_ANCHORS],
        "presets": sims,
        "default_preset": "mature",
        "checklist": checklist,
        "insights": insights,
        "disclaimer": "Scenario model, not a forecast or recommendation: it projects arithmetic from assumptions, "
                      "and knows nothing about credit cycles, competition, rates, regulation or governance events.",
    }


# ── Scoring hooks (used by BankingSector / NBFCSector._compute_special_metric) ──
QTR_PAT_BRIDGE_KEY = "bank_latest_qtr_pat_cr"


def scoring_metrics(metrics: dict, financial_data: dict) -> dict[str, float | None]:
    """The mentor's two scoreable ideas, from data already in the pipeline:

    * sustainable_growth_gap (percentage points) = balance-sheet growth minus
      ROE x (1 - payout). Positive = growth must be funded by fresh shares.
      ROE is the run-rate (latest standalone quarter x4 over current equity)
      when the ledger has that quarter, else the metrics-engine ROE.
    * pb_roe_premium_pct = current P/B vs the P/B the mentor's anchor curve
      assigns to that ROE, in %. High = the market is paying for hope, not
      current earnings.
    Both return None (never 0) when inputs are missing."""
    fd = financial_data or {}
    market, balance = fd.get("market") or {}, fd.get("balance") or {}
    price, bvps, shares = market.get("current_price"), market.get("book_value"), market.get("shares_outstanding")

    roe = metrics.get("roe")
    qpat = (fd.get("_banking_authoritative_metrics") or {}).get(QTR_PAT_BRIDGE_KEY)
    if qpat is not None and bvps and shares:
        roe = qpat * 4 / (bvps * shares / 1e7) * 100
    out: dict[str, float | None] = {"sustainable_growth_gap": None, "pb_roe_premium_pct": None}
    if roe is None:
        return out

    assets = balance.get("total_assets") or {}
    ks = sorted(k for k, v in assets.items() if v)
    payout = market.get("payout_ratio")
    if len(ks) >= 2 and payout is not None:
        growth = (assets[ks[-1]] / assets[ks[-2]] - 1) * 100
        out["sustainable_growth_gap"] = round(growth - sustainable_growth(roe, payout * 100), 2)
    if price and bvps:
        out["pb_roe_premium_pct"] = round(((price / bvps) / pb_for_roe(roe) - 1) * 100, 1)
    return out
