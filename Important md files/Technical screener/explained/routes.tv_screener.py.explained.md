# backend/app/routes/tv_screener.py — Beginner Explanation

**Source file:** `backend/app/routes/tv_screener.py`

## What this file does

Exposes the TradingView screener over HTTP under the `/tv` prefix. All logic is in `tv_screener_service`; this file only validates the request body (Pydantic) and forwards it.

## Endpoints

- `GET /tv/markets` — market names, the operator list, and asset scopes (used to fill the UI dropdowns).
- `GET /tv/fields?market=india` — the field catalog for that market (name, label, type, available timeframes, allowed values).
- `GET /tv/presets` — ready-made scans the UI can load.
- `POST /tv/scan` — run a scan.

## `TVScanRequest`

- `markets` — one or more markets sharing a catalog.
- `columns` — fields to return, e.g. `["name","close|1","RSI|60"]`.
- `filters` — optional filter tree (see the service explained file).
- `sort_by`, `ascending`, `limit` (1–1000), `offset` — ordering and paging.
- `tickers`, `index` — restrict to specific symbols (`NSE:TCS`) or an index (`SYML:NSE;NIFTY`).
- `asset_scope` — `all | stock | etf | fund | dr`.
- `use_cache` — set false to bypass the 30-second Redis cache.
