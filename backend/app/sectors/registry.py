"""
Sector registry — single source of truth for sector detection and framework lookup.

Framework selection priority (first match wins):
1. Exact or near-exact match on sector_aliases
2. Sub-type check (HFC, MFI, Gold Loan within NBFC hierarchy)
3. Generic fallback

Financial sector separation:
  Banks     → BankingSector (commercial banks only)
  NBFCs     → NBFCSector and sub-types (NOT banks)
  Insurance → InsuranceSector (completely separate)

"Financial Services" or "Finance" as generic sector from the DB maps to the most
specific match within the financial hierarchy, then falls back to NBFC if ambiguous.
"""
from __future__ import annotations
import re
from app.sectors.base import SectorFramework
from app.sectors.automobile import AutomobileSector
from app.sectors.auto_ancillaries import AutoAncillariesSector
from app.sectors.banking import BankingSector
from app.sectors.nbfc import NBFCSector, HousingFinanceSector, MicrofinanceSector, GoldLoanSector
from app.sectors.insurance import InsuranceSector
from app.sectors.it_services import ITServicesSector
from app.sectors.pharma import PharmaSector
from app.sectors.fmcg import FMCGSector
from app.sectors.consumer_durables import ConsumerDurablesSector
from app.sectors.commodities_chemicals import ChemicalsSector, SpecialtyChemicalsSector
from app.sectors.metals import MetalsSector, MiningSector
from app.sectors.cement import CementSector
from app.sectors.commodities_forest_materials import ForestMaterialsSector
from app.sectors.oil_gas import OilGasSector
from app.sectors.power import PowerSector, RenewableEnergySector
from app.sectors.other_utilities import UtilitiesSector
from app.sectors.telecom import TelecomSector
from app.sectors.retail import RetailSector
from app.sectors.real_estate import RealEstateSector
from app.sectors.construction import ConstructionSector, InfrastructureSector
from app.sectors.capital_goods import CapitalGoodsSector, IndustrialsSector, DefenceSector
from app.sectors.aviation import AviationSector
from app.sectors.hotels import HotelsSector
from app.sectors.logistics import LogisticsSector
from app.sectors.services import ServicesSector
from app.sectors.media import MediaSector
from app.sectors.electronics import ElectronicsSector
from app.sectors.fintech import FintechSector
from app.sectors.textiles import TextilesSector
from app.sectors.diversified import DiversifiedSector
from app.sectors.generic import GenericSector
from app.sectors.classification_map import BASIC_INDUSTRY_TO_FRAMEWORK


# ── Ordered framework list ────────────────────────────────────────────────────
# More-specific frameworks appear before broader ones.
# Within financial sub-types, HFC/MFI/Gold come before generic NBFC.

_FRAMEWORKS: list[SectorFramework] = [
    # Financial — most specific first within each group
    BankingSector(),
    HousingFinanceSector(),
    MicrofinanceSector(),
    GoldLoanSector(),
    NBFCSector(),
    InsuranceSector(),

    # Industrials — more specific before broader
    AutoAncillariesSector(),   # before AutomobileSector
    AutomobileSector(),
    SpecialtyChemicalsSector(),  # before ChemicalsSector
    ChemicalsSector(),
    MiningSector(),              # before MetalsSector
    MetalsSector(),
    InfrastructureSector(),      # before ConstructionSector
    ConstructionSector(),
    RenewableEnergySector(),     # before PowerSector
    UtilitiesSector(),           # before PowerSector
    PowerSector(),
    DefenceSector(),             # before CapitalGoodsSector
    IndustrialsSector(),         # before CapitalGoodsSector
    CapitalGoodsSector(),

    # Consumer / services
    ITServicesSector(),
    FintechSector(),    # list position doesn't matter for "financial technology
                        # (fintech)" itself — classification_map.py's exact
                        # lookup resolves it before this list is ever
                        # consulted; only matters as a Pass-2 regex fallback
                        # for basic_industry text the exact map hasn't seen yet
    PharmaSector(),
    FMCGSector(),
    ConsumerDurablesSector(),
    RetailSector(),
    MediaSector(),
    HotelsSector(),
    AviationSector(),
    LogisticsSector(),
    ServicesSector(),
    TelecomSector(),
    ElectronicsSector(),
    TextilesSector(),

    # Property
    RealEstateSector(),

    # Commodities / energy
    CementSector(),
    ForestMaterialsSector(),
    OilGasSector(),

    # Conglomerates — last: "Holding Company"/"Diversified"/"Investment
    # Company" are generic enough terms that every more specific sector's
    # own keyword match should win first in the Pass-1/Pass-2 fallback
    # (classification_map.py's exact basic_industry lookup, which runs
    # before this list is ever consulted, is unaffected by position here).
    DiversifiedSector(),
]

_GENERIC = GenericSector()

# name -> instance, for classification_map.py's exact-lookup path (see its
# docstring). Built from the same _FRAMEWORKS list/instances used below, so
# a name from the map always resolves to a real, already-constructed
# framework object — never a second, divergent instance.
_FRAMEWORK_BY_NAME: dict[str, SectorFramework] = {fw.sector_name: fw for fw in _FRAMEWORKS}
_FRAMEWORK_BY_NAME["Generic"] = _GENERIC

# ── Sectors that must NEVER be matched to a financial framework ────────────────
# Prevents broad terms from mis-routing industrial companies
_FINANCIAL_FRAMEWORK_NAMES = {"Banks", "NBFCs", "Housing Finance", "Microfinance",
                               "Gold Loans", "Insurance"}

# Broad financial terms that should only route to financial frameworks when the
# sector string contains no other non-financial keyword
_BROAD_FINANCIAL_TERMS = {"financial services", "finance", "financial"}


def get_framework(sector: str | None, industry: str | None = None,
                  basic_industry: str | None = None) -> SectorFramework:
    """
    Return the best-matching sector framework for the given sector/industry classification.

    Resolution order:
    0. Exact lookup of basic_industry in classification_map.py's
       BASIC_INDUSTRY_TO_FRAMEWORK (NSE's own taxonomy, zero-ambiguity —
       see that module's docstring for why this now runs first)
    1. Match on basic_industry (most specific, keyword/regex)
    2. Match on industry
    3. Match on sector
    4. Generic fallback
    """
    if not sector and not industry and not basic_industry:
        return _GENERIC

    if basic_industry:
        exact_name = BASIC_INDUSTRY_TO_FRAMEWORK.get(basic_industry.strip().lower())
        if exact_name is not None:
            return _FRAMEWORK_BY_NAME[exact_name]

    def _match(text: str | None) -> SectorFramework | None:
        if not text:
            return None
        t = text.lower().strip()
        # Pass 1: exact match — highest priority, no ambiguity
        for fw in _FRAMEWORKS:
            for alias in fw.sector_aliases:
                if alias.lower() == t:
                    return fw
        # Pass 2: alias is a substring of the input text (more specific input wins)
        # e.g. alias="nbfc - housing finance" IN text="nbfc - housing finance companies"
        # We do NOT do the reverse (text in alias) to avoid "nbfc" matching "nbfc - housing finance"
        # Word-boundary matching, not raw `in` — a naive substring check let
        # "IT Services" match inside "Credit Services" (literally
        # "cred" + "it services"), silently routing NBFCs classified under
        # "Credit Services" to the IT framework. Found while generalizing
        # Stage 8 to NBFCs (Architecture v2 upgrade, 2026-09-12).
        #
        # "non "/"non-" negative lookbehind added 2026-09-16: real bug found
        # live after backfilling basic_industry for ~880 companies —
        # BankingSector's bare "Bank"/"Banking" aliases were matching as a
        # whole word inside "Non Banking Financial Company (NBFC)", silently
        # routing ~37 real NBFCs (Bajaj Finance, Cholamandalam, Muthoot
        # Finance, Shriram Finance, Manappuram, ...) to the Banking
        # framework instead of NBFC. Same root cause as the "Technology"
        # alias matching "Financial Technology (Fintech)" (Pine Labs) —
        # a generic English word appearing, unqualified, inside a phrase
        # that means the opposite of what the alias implies. "Non-X is not
        # X" is a general enough pattern to guard here once rather than
        # patch every colliding alias individually as new ones turn up.
        for fw in _FRAMEWORKS:
            for alias in fw.sector_aliases:
                a = alias.lower()
                if len(a) > 3 and re.search(r"(?<!non )(?<!non-)\b" + re.escape(a) + r"\b", t):
                    return fw
        return None

    # Try most-specific to least-specific
    fw = _match(basic_industry) or _match(industry) or _match(sector)
    if fw:
        return fw

    # Broad financial terms: use NBFCSector as a safer default than BankingSector
    # because the DB often puts a mix of fin companies under "Financial Services"
    s_lower = (sector or "").lower()
    if any(term in s_lower for term in _BROAD_FINANCIAL_TERMS):
        # But only if no industry hint contradicts this
        if not industry or "bank" not in (industry or "").lower():
            return _GENERIC  # return generic — safer than mis-classifying as bank/NBFC

    return _GENERIC


def list_sectors() -> list[str]:
    """Return all registered sector framework names."""
    names = [fw.sector_name for fw in _FRAMEWORKS]
    names.append("Generic (all other sectors)")
    return names


def list_frameworks() -> list[dict]:
    """Return full framework metadata for all registered sectors."""
    return [
        {
            "sector_name": fw.sector_name,
            "aliases": fw.sector_aliases,
            "metric_count": len(fw.key_metrics()),
            "red_flag_count": len(fw.red_flag_rules()),
            "weights": fw.SECTOR_WEIGHTS,
        }
        for fw in _FRAMEWORKS
    ]
