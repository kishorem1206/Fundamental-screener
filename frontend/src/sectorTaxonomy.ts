// Maps the ~35 sector-framework buckets the backend already resolves
// (`app/sectors/registry.py`, one per `.py` file there) onto NSE's own
// published two-tier "Macro-economic Sector -> Sector" classification —
// the same taxonomy documented per-file in
// `Important md files/Sector analysis framework/*.md` (each file's
// "Macro Sector"/"Sector Value" header). This keeps the 22 top-level
// groups real and traceable to that source rather than an invented
// grouping. Frameworks not listed here (or an unrecognized backend value)
// fall back to OTHER_SECTOR_NAME — never silently dropped.
export interface MainSectorDef {
  name: string;
  macroSector: string;
}

export const OTHER_SECTOR_NAME = "Other / Unclassified";

export const MAIN_SECTORS: MainSectorDef[] = [
  { name: "Financial Services", macroSector: "Financial Services" },
  { name: "Capital Goods", macroSector: "Industrials" },
  { name: "Construction", macroSector: "Industrials" },
  { name: "Healthcare", macroSector: "Healthcare" },
  { name: "Fast Moving Consumer Goods", macroSector: "FMCG" },
  { name: "Consumer Durables", macroSector: "Consumer Discretionary" },
  { name: "Consumer Services", macroSector: "Consumer Discretionary" },
  { name: "Automobile & Auto Components", macroSector: "Consumer Discretionary" },
  { name: "Media, Entertainment & Publication", macroSector: "Consumer Discretionary" },
  { name: "Realty", macroSector: "Consumer Discretionary" },
  { name: "Textiles", macroSector: "Consumer Discretionary" },
  { name: "Chemicals", macroSector: "Commodities" },
  { name: "Construction Materials", macroSector: "Commodities" },
  { name: "Metals & Mining", macroSector: "Commodities" },
  { name: "Forest Materials", macroSector: "Commodities" },
  { name: "Information Technology", macroSector: "Information Technology" },
  { name: "Services", macroSector: "Services" },
  { name: "Telecommunication", macroSector: "Telecommunication" },
  { name: "Power", macroSector: "Utilities" },
  { name: "Utilities", macroSector: "Utilities" },
  { name: "Oil, Gas & Consumable Fuels", macroSector: "Energy" },
  { name: "Diversified", macroSector: "Diversified" },
];

// backend `framework.sector_name` -> main sector name above.
export const FRAMEWORK_TO_MAIN: Record<string, string> = {
  "Banks": "Financial Services",
  "NBFCs": "Financial Services",
  "Housing Finance": "Financial Services",
  "Microfinance": "Financial Services",
  "Gold Loans": "Financial Services",
  "Insurance": "Financial Services",
  "Fintech": "Financial Services",

  "Capital Goods": "Capital Goods",
  "Industrials": "Capital Goods",
  "Defence": "Capital Goods",

  "Construction": "Construction",
  "Infrastructure": "Construction",

  "Healthcare": "Healthcare",

  "Fast Moving Consumer Goods": "Fast Moving Consumer Goods",

  "Consumer Durables": "Consumer Durables",
  "Electronics": "Consumer Durables",

  "Hotels & Restaurants": "Consumer Services",
  "Retail": "Consumer Services",

  "Automobile": "Automobile & Auto Components",
  "Auto Ancillaries": "Automobile & Auto Components",

  "Media & Entertainment": "Media, Entertainment & Publication",

  "Real Estate": "Realty",

  "Textiles": "Textiles",

  "Chemicals": "Chemicals",
  "Specialty Chemicals": "Chemicals",

  "Cement": "Construction Materials",

  "Metals": "Metals & Mining",
  "Mining": "Metals & Mining",

  "Forest Materials": "Forest Materials",

  "Information Technology": "Information Technology",

  "Services": "Services",
  "Logistics": "Services",
  "Aviation": "Services",

  "Telecom": "Telecommunication",

  "Power": "Power",
  "Renewable Energy": "Power",

  "Utilities": "Utilities",

  "Oil & Gas": "Oil, Gas & Consumable Fuels",

  "Diversified": "Diversified",
};

export function mainSectorFor(frameworkSectorName: string): string {
  return FRAMEWORK_TO_MAIN[frameworkSectorName] || OTHER_SECTOR_NAME;
}
