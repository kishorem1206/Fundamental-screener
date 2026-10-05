"""Calculated facts. Each is plain arithmetic on reported facts and names
them as inputs, so a reader can walk from any derived figure back to the
filings it rests on. Rebuilt from scratch on every run.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.bie.evidence import record_fact
from app.bie.facts import (
    PROFIT_KEYS, REVENUE_KEYS, SEGMENT_ASSETS, SEGMENT_LIABILITIES, SEGMENT_RESULT, SEGMENT_REVENUE, FactBook,
)
from app.infrastructure.database.models import BieFact

_EXCISE = re.compile(r"excise", re.I)


def _is_business(fact: BieFact) -> bool:
    return bool((fact.attributes or {}).get("is_business_segment", True))


def derive_company(db: Session, company_id: str) -> int:
    db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.nature == "CALCULATED").delete(
        synchronize_session=False)
    db.flush()
    book = FactBook(db, company_id)
    written = 0

    def calc(*, fact_type: str, key: str, dimension: str, period: tuple, basis: str, value: float, unit: str,
             inputs: list[BieFact], formula: str) -> None:
        nonlocal written
        record_fact(
            db, scope="COMPANY", company_id=company_id, fact_type=fact_type, key=key, dimension=dimension,
            period_type=period[0], period_start=period[1], period_end=period[2], statement_type=basis,
            value_num=value, unit=unit, nature="CALCULATED", extraction_method="CALCULATION",
            source_tier=min(f.source_tier for f in inputs), confidence="HIGH",
            inputs=[f.id for f in inputs], formula=formula, replace=False,
        )
        written += 1

    for basis in book.bases():
        for period_type in ("FY", "Q"):
            for end in book.period_ends(period_type, basis):
                # Revenue net of excise duty, where the company itemises excise as an expense.
                revenue = book.first(REVENUE_KEYS[:1], period_type, end, basis)
                excise = next((f for f in book.facts
                               if f.fact_type == "line_detail" and f.key == "OtherExpenses" and _EXCISE.search(f.dimension)
                               and f.period_type == period_type and f.period_end == end and f.statement_type == basis), None)
                if revenue is not None and excise is not None and revenue.value_num is not None:
                    period = (period_type, revenue.period_start, end)
                    calc(fact_type="financial", key="revenue_net_of_excise", dimension="", period=period, basis=basis,
                         value=float(revenue.value_num) - float(excise.value_num), unit="INR",
                         inputs=[revenue, excise], formula="RevenueFromOperations − excise duty expense")

                segments = {label: facts for label, facts in book.segments(period_type, end, basis).items()
                            if all(_is_business(f) for f in facts.values())}
                revenues = {l: f[SEGMENT_REVENUE] for l, f in segments.items() if SEGMENT_REVENUE in f}
                results = {l: f[SEGMENT_RESULT] for l, f in segments.items() if SEGMENT_RESULT in f}
                total_revenue = sum(float(f.value_num) for f in revenues.values())
                total_result = sum(float(f.value_num) for f in results.values())
                for label, facts in segments.items():
                    rev, res = facts.get(SEGMENT_REVENUE), facts.get(SEGMENT_RESULT)
                    period = (period_type, (rev or res).period_start if (rev or res) else None, end)
                    if rev is not None and res is not None and float(rev.value_num) > 0:
                        calc(fact_type="segment", key="segment_margin", dimension=label, period=period, basis=basis,
                             value=float(res.value_num) / float(rev.value_num), unit="ratio", inputs=[rev, res],
                             formula="segment result ÷ segment revenue")
                    if rev is not None and total_revenue > 0:
                        calc(fact_type="segment", key="segment_revenue_share", dimension=label, period=period, basis=basis,
                             value=float(rev.value_num) / total_revenue, unit="ratio", inputs=list(revenues.values()),
                             formula="segment revenue ÷ sum of business-segment revenue (before inter-segment elimination)")
                    if res is not None and total_result > 0:
                        calc(fact_type="segment", key="segment_result_share", dimension=label, period=period, basis=basis,
                             value=float(res.value_num) / total_result, unit="ratio", inputs=list(results.values()),
                             formula="segment result ÷ sum of business-segment results")
                    assets, liabilities = facts.get(SEGMENT_ASSETS), facts.get(SEGMENT_LIABILITIES)
                    if period_type == "FY" and assets is not None and liabilities is not None:
                        employed = float(assets.value_num) - float(liabilities.value_num)
                        calc(fact_type="segment", key="segment_capital_employed", dimension=label,
                             period=("INSTANT", None, end), basis=basis, value=employed, unit="INR",
                             inputs=[assets, liabilities], formula="segment assets − segment liabilities")
                        if res is not None and employed > 0:
                            calc(fact_type="segment", key="segment_return_on_capital", dimension=label, period=period,
                                 basis=basis, value=float(res.value_num) / employed, unit="ratio",
                                 inputs=[res, assets, liabilities],
                                 formula="segment result ÷ (segment assets − segment liabilities) at year end")
        # ── cash generation and where it went (full years) ───────────────
        for end in book.period_ends("FY", basis):
            def g(key: str, period_type: str = "FY"):
                return book.get(key, period_type, end, basis)

            def val(f) -> float:
                return float(f.value_num)

            period = ("FY", None, end)
            cfo, profit = g("CashFlowsFromUsedInOperatingActivities"), book.first(PROFIT_KEYS, "FY", end, basis)
            capex_parts = [f for f in (g("PurchaseOfTangibleAssetsClassifiedAsInvestingActivities"),
                                       g("PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities"),
                                       g("PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities")) if f is not None]
            dividends = g("DividendsPaidClassifiedAsFinancingActivities")
            if capex_parts:
                capex = sum(abs(val(f)) for f in capex_parts)
                calc(fact_type="financial", key="capital_expenditure", dimension="", period=period, basis=basis, value=capex,
                     unit="INR", inputs=capex_parts, formula="cash paid for tangible and intangible assets")
                if cfo is not None:
                    fcf = val(cfo) - capex
                    calc(fact_type="financial", key="free_cash_flow", dimension="", period=period, basis=basis, value=fcf,
                         unit="INR", inputs=[cfo, *capex_parts], formula="operating cash flow − capital expenditure")
                    if dividends is not None and abs(val(dividends)) > 0:
                        calc(fact_type="financial", key="dividend_cover_by_free_cash_flow", dimension="", period=period,
                             basis=basis, value=fcf / abs(val(dividends)), unit="ratio", inputs=[cfo, *capex_parts, dividends],
                             formula="free cash flow ÷ dividends paid in cash")
            if cfo is not None and profit is not None and val(profit) > 0:
                calc(fact_type="financial", key="cash_conversion", dimension="", period=period, basis=basis,
                     value=val(cfo) / val(profit), unit="ratio", inputs=[cfo, profit], formula="operating cash flow ÷ profit after tax")
            # Lender measures (banking layout): spread income, funding mix, efficiency, cost of bad loans.
            earned, expended = g("InterestEarned"), g("InterestExpended")
            if earned is not None and expended is not None:
                calc(fact_type="financial", key="net_interest_income", dimension="", period=period, basis=basis,
                     value=val(earned) - val(expended), unit="INR", inputs=[earned, expended], formula="interest earned − interest expended")
                other, opex = g("OtherIncome"), g("OperatingExpenses")
                if other is not None and opex is not None and val(earned) - val(expended) + val(other) > 0:
                    calc(fact_type="financial", key="cost_to_income", dimension="", period=period, basis=basis,
                         value=val(opex) / (val(earned) - val(expended) + val(other)), unit="ratio", inputs=[opex, earned, expended, other],
                         formula="operating expenses ÷ (net interest income + other income)")
                advances, deposits, provisions = g("Advances", "INSTANT"), g("Deposits", "INSTANT"), g("ProvisionsOtherThanTaxAndContingencies")
                if advances is not None and deposits is not None and val(deposits) > 0:
                    calc(fact_type="financial", key="credit_deposit_ratio", dimension="", period=("INSTANT", None, end), basis=basis,
                         value=val(advances) / val(deposits), unit="ratio", inputs=[advances, deposits], formula="advances ÷ deposits")
                if advances is not None and provisions is not None and val(advances) > 0:
                    calc(fact_type="financial", key="credit_cost", dimension="", period=period, basis=basis,
                         value=val(provisions) / val(advances), unit="ratio", inputs=[provisions, advances],
                         formula="provisions other than tax ÷ year-end advances")
            # Insurer measures: what is paid out and spent per rupee of premium, and the capital behind it.
            gross = g("GrossPremiumsWritten") or g("GrossPremiumIncome")
            if gross is not None and val(gross) > 0:
                commission, opex = g("NetCommission"), g("OperatingExpensesRelatedToInsuranceBusiness")
                capital, reserves = g("ShareCapital", "INSTANT"), g("ReservesAndSurplus", "INSTANT")
                if capital is not None and reserves is not None and val(capital) + val(reserves) > 0:
                    calc(fact_type="financial", key="net_worth", dimension="", period=("INSTANT", None, end), basis=basis,
                         value=val(capital) + val(reserves), unit="INR", inputs=[capital, reserves], formula="share capital + reserves and surplus")
                    if profit is not None:
                        calc(fact_type="financial", key="return_on_equity", dimension="", period=period, basis=basis,
                             value=val(profit) / (val(capital) + val(reserves)), unit="ratio", inputs=[profit, capital, reserves],
                             formula="profit after tax ÷ (share capital + reserves and surplus) at year end")
                earned, claims, net_written = g("PremiumEarned"), g("IncurredClaims"), g("NetPremiumWritten")
                if net_written is not None and val(net_written) > 0:  # general insurer
                    calc(fact_type="financial", key="retention_ratio", dimension="", period=period, basis=basis, value=val(net_written) / val(gross),
                         unit="ratio", inputs=[net_written, gross], formula="net premium written ÷ gross premium written")
                    if earned is not None and claims is not None and commission is not None and opex is not None and val(earned) > 0:
                        claims_ratio, expense_ratio = val(claims) / val(earned), (val(commission) + val(opex)) / val(net_written)
                        calc(fact_type="financial", key="claims_ratio", dimension="", period=period, basis=basis, value=claims_ratio,
                             unit="ratio", inputs=[claims, earned], formula="incurred claims ÷ net earned premium")
                        calc(fact_type="financial", key="expense_ratio", dimension="", period=period, basis=basis, value=expense_ratio,
                             unit="ratio", inputs=[commission, opex, net_written], formula="(net commission + operating expenses) ÷ net premium written")
                        calc(fact_type="financial", key="combined_ratio", dimension="", period=period, basis=basis, value=claims_ratio + expense_ratio,
                             unit="ratio", inputs=[claims, earned, commission, opex, net_written], formula="claims ratio + expense ratio")
                elif commission is not None and opex is not None:  # life insurer
                    calc(fact_type="financial", key="expense_ratio", dimension="", period=period, basis=basis,
                         value=(val(commission) + val(opex)) / val(gross), unit="ratio", inputs=[commission, opex, gross],
                         formula="(net commission + operating expenses) ÷ gross premium")
                # Filers enter these ratios on different scales (1.77, 177 or 0.0177 for the same thing): restate on one.
                for source_key, key, floor, what in (("SolvencyRatio", "solvency_multiple", 0.2, "a multiple of required capital"),
                                                     ("PersistencyRatio13ThMonth", "persistency_13th_month", 0.02, "a share of policies"),
                                                     ("PersistencyRatio61ThMonth", "persistency_61st_month", 0.02, "a share of policies")):
                    filed = g(source_key)
                    if filed is None or filed.value_num is None or val(filed) <= 0:
                        continue
                    scale = 100 if val(filed) < floor else 0.01 if val(filed) > 20 else 1
                    calc(fact_type="financial", key=key, dimension="", period=period, basis=basis, value=val(filed) * scale, unit="ratio",
                         inputs=[filed], formula=f"ratio as filed, restated as {what}" + (f" (filed figure × {scale:g})" if scale != 1 else ""))
            liquid = [f for f in (g("CashAndCashEquivalents", "INSTANT"), g("BankBalanceOtherThanCashAndCashEquivalents", "INSTANT"),
                                  g("CurrentInvestments", "INSTANT")) if f is not None]
            debt = [f for f in (g("BorrowingsNoncurrent", "INSTANT"), g("BorrowingsCurrent", "INSTANT")) if f is not None]
            equity = g("Equity", "INSTANT")
            if liquid and equity is not None:  # general layout only: a lender's borrowings are its raw material
                net = sum(val(f) for f in liquid) - sum(val(f) for f in debt)
                calc(fact_type="financial", key="net_liquid_assets", dimension="", period=("INSTANT", None, end), basis=basis,
                     value=net, unit="INR", inputs=[*liquid, *debt],
                     formula="cash, bank balances and current investments − borrowings")
                if val(equity) > 0:
                    calc(fact_type="financial", key="debt_to_equity", dimension="", period=("INSTANT", None, end), basis=basis,
                         value=sum(val(f) for f in debt) / val(equity), unit="ratio", inputs=[*debt, equity] if debt else [equity],
                         formula="borrowings ÷ total equity")
    return written
