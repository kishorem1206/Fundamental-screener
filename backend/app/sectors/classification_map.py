"""Exact `basic_industry` -> framework lookup, built from NSE's own official
taxonomy (`fa_stock_classification`, scraped from Screener.in's breadcrumb —
see `scripts/classify_stocks_screener.py`).

Why this exists alongside `registry.py`'s keyword/regex matching (2026-09-16):
that matching was built when `sector`/`industry`/`basic_industry` came from
mixed sources with inconsistent spelling, so substring/keyword matching was
the only practical way to bucket variant text into the 34 frameworks. Once
`stocks` was synced to `fa_stock_classification`'s clean, consistent NSE
taxonomy (880/884 companies, verified zero drift), that justification
mostly disappeared — and the substring approach is exactly what caused four
real misclassification bugs found in one session: "Technology" matching
inside "Financial Technology (Fintech)" (Pine Labs -> IT), "Banking"
matching inside "Non Banking Financial Company" (~37 real NBFCs -> Banks),
"Electrical Equipment" matching heavy industrial equipment (-> Consumer
Durables), "Industrial" matching "Industrial Minerals"/"Industrial Gases"
(-> Capital Goods), and "Software" matching "TV Broadcasting & Software
Production" (-> IT). Every one of those slipped through NAME collisions a
human reviewing the actual `basic_industry` values catches instantly but a
keyword scanner cannot.

This module is that human review, encoded: every distinct `basic_industry`
value seen in `fa_stock_classification` as of 2026-09-16 (178 combos, 177
distinct basic_industry strings, manually audited against the framework
they resolve to — confirmed zero basic_industry value maps to more than one
framework across the live DB), mapped directly to its correct framework
name. `get_framework()` checks this FIRST — an exact, O(1), zero-ambiguity
lookup — before falling back to `registry.py`'s keyword matching, which
remains in place only as a safety net for text this map hasn't seen yet
(a brand-new IPO not yet in `fa_stock_classification`, or a value NSE
introduces later). When a new `basic_industry` value shows up and lands in
the regex fallback, add it here after a manual check, same as every entry
below was added.

A few entries map to "Generic" not because Generic is a good fit, but
because no dedicated framework exists for that industry yet (e.g. Capital
Markets services, BPO/consulting) — a real framework coverage gap, not a
matching bug. `"financial technology (fintech)"` used to be one
of these too, until `FintechSector` (app/sectors/fintech.py) was built
2026-09-17, `"paper & paper products"` similarly until
`ForestMaterialsSector` (app/sectors/commodities_forest_materials.py) was
built 2026-09-20, `"garments & apparels"`/`"other textile products"`
similarly until `TextilesSector` (app/sectors/textiles.py) was built
2026-09-20, and `"diversified"`/`"holding company"` similarly until
`DiversifiedSector` (app/sectors/diversified.py) was built 2026-09-20 —
update the entries below the same way if Capital Markets/Asset Management
get dedicated frameworks later.

Separately, a real (not "no framework yet") bug fixed 2026-09-20:
`"lpg/cng/png/lng supplier"` (Adani Total Gas, Petronet LNG, IGL, MGL,
IRM Energy — 7 real City Gas Distribution companies) and `"oil equipment &
services"` were mapped to `'Generic'` even though `OilGasSector`
(app/sectors/oil_gas.py) already lists "Gas Distribution"/"City Gas
Distribution" among its own `sector_aliases` and the MD spec explicitly
includes gas distribution and oilfield services under Oil, Gas &
Consumable Fuels — the exact-match-first design meant that alias could
never actually be reached for these real companies. Both now route to
`'Oil & Gas'`.
"""
from __future__ import annotations

BASIC_INDUSTRY_TO_FRAMEWORK: dict[str, str] = {
    '2/3 wheelers': 'Automobile',
    'abrasives & bearings': 'Capital Goods',
    'advertising & media agencies': 'Media & Entertainment',
    'aerospace & defense': 'Defence',
    'airline': 'Aviation',
    'airport & airport services': 'Aviation',
    'aluminium': 'Metals',
    'aluminium, copper & zinc products': 'Metals',
    'amusement parks/ other recreation': 'Hotels & Restaurants',
    'animal feed': 'Fast Moving Consumer Goods',
    'asset management company': 'Generic',
    'auto components & equipments': 'Auto Ancillaries',
    'auto dealer': 'Automobile',
    'biotechnology': 'Healthcare',
    'breweries & distilleries': 'Fast Moving Consumer Goods',
    'business process outsourcing (bpo)/ knowledge process outsourcing (kpo)': 'Services',
    'cables - electricals': 'Capital Goods',
    'carbon black': 'Chemicals',
    'castings & forgings': 'Capital Goods',
    'cement & cement products': 'Cement',
    'ceramics': 'Consumer Durables',
    'cigarettes & tobacco products': 'Fast Moving Consumer Goods',
    'civil construction': 'Construction',
    'coal': 'Mining',
    'commercial vehicles': 'Automobile',
    'commodity chemicals': 'Chemicals',
    'compressors, pumps & diesel engines': 'Capital Goods',
    'computers - software & consulting': 'Information Technology',
    'computers hardware & equipments': 'Information Technology',
    'construction vehicles': 'Capital Goods',
    'consulting services': 'Services',
    'consumer electronics': 'Consumer Durables',
    'copper': 'Metals',
    'dairy products': 'Fast Moving Consumer Goods',
    'depositories, clearing houses and other intermediaries': 'Generic',
    'digital entertainment': 'Media & Entertainment',
    'diversified': 'Diversified',
    'diversified commercial services': 'Services',
    'diversified consumer products': 'Consumer Durables',
    'diversified fmcg': 'Fast Moving Consumer Goods',
    'diversified metals': 'Metals',
    'diversified retail': 'Retail',
    'dredging': 'Capital Goods',
    'dyes and pigments': 'Chemicals',
    'e-learning': 'Generic',
    'e-retail/ e-commerce': 'Retail',
    'edible oil': 'Fast Moving Consumer Goods',
    'education': 'Generic',
    'electrodes & refractories': 'Capital Goods',
    'electronic media': 'Media & Entertainment',
    'exchange and data platform': 'Generic',
    'explosives': 'Chemicals',
    'ferro & silica manganese': 'Metals',
    'fertilizers': 'Chemicals',
    'film production, distribution & exhibition': 'Media & Entertainment',
    'financial institution': 'Generic',
    'financial products distributor': 'Generic',
    'financial technology (fintech)': 'Fintech',
    'footwear': 'Consumer Durables',
    'furniture, home furnishing': 'Consumer Durables',
    'garments & apparels': 'Textiles',
    'gas transmission/marketing': 'Oil & Gas',
    'gems, jewellery and watches': 'Consumer Durables',
    'general insurance': 'Insurance',
    'glass - consumer': 'Consumer Durables',
    'glass - industrial': 'Capital Goods',
    'granites & marbles': 'Consumer Durables',
    'healthcare research, analytics & technology': 'Healthcare',
    'healthcare service provider': 'Healthcare',
    'heavy electrical equipment': 'Capital Goods',
    'holding company': 'Diversified',
    'hospital': 'Healthcare',
    'hotels & resorts': 'Hotels & Restaurants',
    'household appliances': 'Consumer Durables',
    'household products': 'Fast Moving Consumer Goods',
    'houseware': 'Consumer Durables',
    'housing finance company': 'Housing Finance',
    'industrial gases': 'Chemicals',
    'industrial machinery': 'Capital Goods',
    'industrial minerals': 'Mining',
    'industrial products': 'Capital Goods',
    'insurance distributors': 'Insurance',
    'integrated power utilities': 'Power',
    'internet & catalogue retail': 'Retail',
    'investment company': 'Generic',
    'iron & steel': 'Metals',
    'iron & steel products': 'Metals',
    'it enabled services': 'Information Technology',
    'leather and leather products': 'Consumer Durables',
    'life insurance': 'Insurance',
    'logistics solution provider': 'Logistics',
    'lpg/cng/png/lng supplier': 'Oil & Gas',
    'lubricants': 'Oil & Gas',
    'meat products including poultry': 'Fast Moving Consumer Goods',
    'media & entertainment': 'Media & Entertainment',
    'medical equipment & supplies': 'Healthcare',
    'microfinance institutions': 'Microfinance',
    'multi utilities': 'Utilities',
    'non banking financial company (nbfc)': 'NBFCs',
    'offshore support solution drilling': 'Generic',
    'oil equipment & services': 'Oil & Gas',
    'oil exploration & production': 'Oil & Gas',
    'oil storage & transportation': 'Logistics',
    'other agricultural products': 'Fast Moving Consumer Goods',
    'other bank': 'Banks',
    'other beverages': 'Fast Moving Consumer Goods',
    'other capital market related services': 'Generic',
    'other construction materials': 'Construction',
    'other consumer services': 'Generic',
    'other electrical equipment': 'Capital Goods',
    'other financial services': 'Generic',
    'other food products': 'Fast Moving Consumer Goods',
    'other industrial products': 'Capital Goods',
    'other telecom services': 'Telecom',
    'other textile products': 'Textiles',
    'packaged foods': 'Fast Moving Consumer Goods',
    'packaging': 'Capital Goods',
    'paints': 'Chemicals',
    'paper & paper products': 'Forest Materials',
    'passenger cars & utility vehicles': 'Automobile',
    'personal care': 'Fast Moving Consumer Goods',
    'pesticides & agrochemicals': 'Chemicals',
    'petrochemicals': 'Chemicals',
    'pharmaceuticals': 'Healthcare',
    'pharmacy retail': 'Retail',
    'pig iron': 'Metals',
    'plastic products - consumer': 'Consumer Durables',
    'plastic products - industrial': 'Capital Goods',
    'plywood boards/ laminates': 'Consumer Durables',
    'port & port services': 'Infrastructure',
    'power - transmission': 'Power',
    'power distribution': 'Power',
    'power generation': 'Power',
    'power trading': 'Power',
    'precious metals': 'Metals',
    'print media': 'Media & Entertainment',
    'printing & publication': 'Media & Entertainment',
    'private sector bank': 'Banks',
    'public sector bank': 'Banks',
    'railway wagons': 'Capital Goods',
    'ratings': 'Generic',
    'real estate investment trusts (reits)': 'Real Estate',
    'refineries & marketing': 'Oil & Gas',
    'residential, commercial projects': 'Real Estate',
    'restaurants': 'Hotels & Restaurants',
    'road assetstoll, annuity, hybrid-annuity': 'Infrastructure',
    'rubber': 'Capital Goods',
    'sanitary ware': 'Consumer Durables',
    'seafood': 'Fast Moving Consumer Goods',
    'ship building & allied services': 'Capital Goods',
    'shipping': 'Logistics',
    'software products': 'Information Technology',
    'speciality retail': 'Retail',
    'specialty chemicals': 'Specialty Chemicals',
    'sponge iron': 'Metals',
    'stationary': 'Fast Moving Consumer Goods',
    'stockbroking & allied': 'Generic',
    'sugar': 'Fast Moving Consumer Goods',
    'tea & coffee': 'Fast Moving Consumer Goods',
    'telecom - cellular & fixed line services': 'Telecom',
    'telecom - equipment & accessories': 'Telecom',
    'telecom - infrastructure': 'Telecom',
    'tour, travel related services': 'Hotels & Restaurants',
    'tractors': 'Capital Goods',
    'trading & distributors': 'Services',
    'trading - auto components': 'Auto Ancillaries',
    'trading - gas': 'Generic',
    'trading - metals': 'Metals',
    'trading - minerals': 'Metals',
    'trading - textile products': 'Generic',
    'transport related services': 'Services',
    'tv broadcasting & software production': 'Media & Entertainment',
    'tyres & rubber products': 'Auto Ancillaries',
    'waste management': 'Utilities',
    'water supply & management': 'Utilities',
    'web based media and service': 'Media & Entertainment',
    'wellness': 'Healthcare',
    'zinc': 'Metals',
}
