"""Facts from a Business Responsibility and Sustainability Report data file
(mandatory for the 1,000 largest listed companies): what the company does
and in what proportions, where it sells, who it sells to, the group entities
it lists, and how concentrated its purchases and sales are.
"""
from __future__ import annotations

import html
import re
from datetime import date

from sqlalchemy.orm import Session

from app.bie import xbrl
from app.bie.evidence import clear_document_facts, record_fact
from app.infrastructure.database.models import Document

_MAIN = "DCYMain"  # current-year duration context
_PROFILE_NUMBERS = {
    "Turnover": "INR", "NetWorth": "INR",
    "NumberOfStatesWhereMarketServedByTheEntity": "count",
    "NumberOfCountriesWhereMarketServedByTheEntity": "count",
    "PercentageOfContributionOfExportsInTheTotalTurnoverOfTheEntity": "ratio",
}
_PROFILE_TEXT = {
    "CorporateIdentityNumber", "DateOfIncorporation", "WebsiteOfCompany", "ReportingBoundary",
    "ABriefOnTypesOfCustomersExplanatoryTextBlock",
}
_CONCENTRATION = {
    "PercentageOfPurchasesFromTradingHousesInTotalPurchasesForConcentrationOfPurchases": "ratio",
    "NumberOfTradingHousesWherePurchasesAreMade": "count",
    "PercentageOfPurchasesFromTopTenTradingHousesInTotalPurchasesFromTradingHouses": "ratio",
    "PercentageOfSalesToDealersOrDistributorsInTotalSales": "ratio",
    "NumberOfDealersOrDistributorsToWhomSalesAreMade": "count",
    "PercentageOfSalesToTopTenDealersOrDistributorsInTotalSalesToDealersOrDistributors": "ratio",
    "PercentageOfPurchasesFromRelatedPartiesInTotalPurchasesForShareOfRelatedPartyTransactions": "ratio",
    "PercentageOfSalesToRelatedPartiesInTotalSalesForShareOfRelatedPartyTransactions": "ratio",
    "PercentageOfLoansAndAdvancesGivenToRelatedPartiesInTotalLoansAndAdvances": "ratio",
    "PercentageOfInvestmentsInRelatedPartiesInTotalInvestments": "ratio",
}
_LOCATION_CONTEXTS = {
    "D_Plant_National": "Plants, India", "D_Office_National": "Offices, India",
    "D_Plant_International": "Plants, overseas", "D_Office_International": "Offices, overseas",
}


def _clean(text: str) -> str:
    text = html.unescape(html.unescape(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_brsr(db: Session, *, company_id: str, document: Document, content: bytes) -> int:
    inst = xbrl.parse(content)
    main = inst.contexts.get(_MAIN)
    fy_start = main.start if main else None
    fy_end = main.end if main else None
    clear_document_facts(db, document)
    written = 0

    def write(fact: xbrl.XFact, *, fact_type: str, key: str, dimension: str = "", unit: str | None = None,
              number: float | None = None, text: str | None = None, attributes: dict | None = None) -> None:
        nonlocal written
        record_fact(
            db, scope="COMPANY", company_id=company_id, fact_type=fact_type, key=key, dimension=dimension,
            period_type="FY", period_start=fy_start, period_end=fy_end, statement_type="NA",
            value_num=number, value_text=text, unit=unit, attributes=attributes, nature="REPORTED",
            document=document, locator_type="XBRL", locator=f"{fact.name}@{fact.context_id}", quote=fact.value,
            extraction_method="XBRL_PARSE", source_tier=1, confidence="HIGH", replace=False,
        )
        written += 1

    for name, unit in {**_PROFILE_NUMBERS, **_CONCENTRATION}.items():
        fact = inst.get(name, _MAIN)
        if fact is not None and fact.number() is not None:
            write(fact, fact_type="concentration" if name in _CONCENTRATION else "business_profile",
                  key=name, unit=unit, number=fact.number())
    for name in _PROFILE_TEXT:
        fact = inst.get(name, _MAIN)
        if fact is not None and _clean(fact.value):
            write(fact, fact_type="business_profile", key=name, text=_clean(fact.value))

    for ctx_id, label in _LOCATION_CONTEXTS.items():
        fact = inst.get("NumberOfLocations", ctx_id)
        if fact is not None and fact.number() is not None:
            write(fact, fact_type="footprint", key="NumberOfLocations", dimension=label, unit="count", number=fact.number())

    for ctx in inst.contexts.values():
        in_ctx = {f.name: f for f in inst.in_context(ctx.id)}
        if ctx.id.startswith("D_BusinessActivities"):
            share = in_ctx.get("PercentageOfTotalTurnoverForBusinessActivities")
            name = in_ctx.get("DescriptionOfBusinessActivity")
            if share is not None and name is not None and share.number() is not None:
                main_activity = in_ctx.get("DescriptionOfMainActivity")
                write(share, fact_type="business_activity", key="turnover_share", dimension=_clean(name.value)[:300],
                      unit="ratio", number=share.number(),
                      attributes={"main_activity": _clean(main_activity.value) if main_activity else None})
        elif ctx.id.startswith("D_ProductServiceSold"):
            share = in_ctx.get("PercentageOfTotalTurnoverForProductOrServiceSold")
            name = in_ctx.get("ProductOrServiceSoldByTheEntity")
            if share is not None and name is not None and share.number() is not None:
                nic = in_ctx.get("NICCodeOfProductOrServiceSoldByTheEntity")
                write(share, fact_type="product", key="turnover_share", dimension=_clean(name.value)[:300],
                      unit="ratio", number=share.number(), attributes={"nic_code": nic.value if nic else None})
        elif ctx.id.startswith("D_HoldingSubsidiaryAssociateCompaniesAndJointVentures"):
            name = in_ctx.get("NameOfTheHoldingOrSubsidiaryAssociateCompaniesOrJointVentures")
            if name is None or not _clean(name.value):
                continue
            # Some companies put a pointer here ("names are on page 314 of our Annual Report") instead of a name.
            if len(_clean(name.value)) > 110 or re.search(r"annual report|https?://|www\.", _clean(name.value), re.I):
                continue
            held = in_ctx.get("PercentageOfSharesHeldByListedEntity")
            category = in_ctx.get("CategoryOfCompany")
            write(name, fact_type="group_entity", key="relationship", dimension=_clean(name.value)[:300],
                  text=_clean(category.value) if category is not None and category.value else "Not stated",
                  attributes={"shares_held_ratio": held.number() if held is not None else None})
    return written


def fiscal_year_end(content: bytes) -> date | None:
    main = xbrl.parse(content).contexts.get(_MAIN)
    return main.end if main else None
