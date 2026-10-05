# frontend/src/components/TVScreenerPage.tsx — Beginner Explanation

**Source file:** `frontend/src/components/TVScreenerPage.tsx`

## What this file does

The "TradingView" tab. A left panel builds a scan; the right side shows results. It talks to the backend `/tv/*` endpoints through helpers appended to `api.ts` (`getTVMarkets`, `getTVFields`, `getTVPresets`, `scanTV`).

## Key parts

- **Presets** — load a ready-made scan (markets, columns, filters, sort).
- **Market + scope** — any of 80 markets; for stock markets an "Only ETFs / funds / stocks / DRs" scope (the default hides ETFs). Optional index (`SYML:NSE;NIFTY`) and ticker list.
- **Filters** — rows of `field operator value`. Operators are the library's full set (comparisons, crosses, between, in-list, % above/below another field, empty…). "compare to another field" turns the value into a column reference. "match ALL / ANY" is AND / OR.
- **Field picker** — type to search the catalog (browser datalist); a dropdown appears for fields that have timeframes (1m, 5m … 240m, 1W, 1M) and writes `field|tf`.
- **Columns / sort / limit** — choose what to show and how to order.
- **Results** — formatted numbers (K/M/B/T), green/red for change-like columns, CSV export, "cached" and timing badge.
- Settings persist in `localStorage` (`tv_screener_settings_v1`).
