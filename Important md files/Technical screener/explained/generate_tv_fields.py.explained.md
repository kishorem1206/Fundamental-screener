# backend/scripts/generate_tv_fields.py — Beginner Explanation

**Source file:** `backend/scripts/generate_tv_fields.py`

## What this file does

Downloads the public TradingView-Screener "fields" pages (stocks, crypto, coin, forex, futures, options, bonds, bond, cfd, economics2) and saves one JSON file per market type into `backend/app/data/tv_fields/`. `tv_screener_service` reads those files to validate field names and timeframes without any network call.

Run it when TradingView adds fields: `cd backend && PYTHONPATH=. .venv/bin/python3.12 scripts/generate_tv_fields.py`.

## Key parts

- `parse` — each table row is `field | label | type | allowed values`. Fields that exist on several timeframes are folded into a `<details>` cell: the `<summary>` is the base name and each `<li>` is `name|timeframe`; we store the timeframes list on the base field.
- Output per field: `name, label, type, timeframes, value_count, values`.

The human-readable version of the same data is in `docs/tradingview_fields/*.md` (index: `README.md` there).
