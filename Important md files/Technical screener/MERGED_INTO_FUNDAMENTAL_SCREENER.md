# Technical screener — where everything lives after the merge

On 2026-10-05 the separate **Stock screener** app was merged into this app.
The documents in this folder were written for the old layout; read them with
this table.

| Old (Stock screener) | Now (Fundamental screener) |
|---|---|
| `backend/app/<package>/` | `backend/app/technical/<package>/` |
| `backend/app/config.py`, `logger.py` | shared `backend/app/config.py`, `logger.py` |
| `backend/app/infrastructure/database/` | shared `backend/app/infrastructure/database/` (models appended to `models.py`) |
| `backend/app/infrastructure/redis/client.py` | `backend/app/technical/infrastructure/redis/client.py` (keeps the `screener:` key prefix) |
| `backend/app/main.py` | `backend/app/technical/router.py`, included by `backend/app/main.py` |
| `backend/tests/` | `backend/tests/technical/` |
| `backend/scripts/`, `scripts/` | `backend/scripts/technical/` (seed files in `seeds/`) |
| `backend/alembic/versions/0001`, `0002` | `backend/alembic/versions/0037_technical_screener_tables.py` |
| `docs/`, root `*.md` | this folder |
| `containers/docker-compose.yml` | `containers/docker-compose.yml` (same project name, same volumes) |
| API at `http://localhost:3001/<route>` | `http://localhost:3002/api/technical/<route>` |

Imports changed from `app.<package>` to `app.technical.<package>`; nothing else
in the moved code was altered. The "explained files" rule in the original
`CLAUDE.md` applies to files under `backend/app/technical/`.

Run the technical tests: `cd backend && .venv/bin/python -m pytest tests/technical -q`
(several call the live TradingView API).

## Frontend (phase 2)

| Old (Stock screener) | Now (Fundamental screener) |
|---|---|
| `frontend/src/App.tsx` | `frontend/src/technical/TechnicalScreener.tsx` (the "Technical Screener" page; same six sub-tabs) |
| `frontend/src/components/` | `frontend/src/technical/components/` |
| `frontend/src/api.ts`, `types.ts` | `frontend/src/technical/api.ts`, `types.ts` (base path `/api/technical`) |
| `frontend/src/index.css` | `frontend/src/technical/technical.css`, every rule scoped to `.technical-root` |

Top navigation (`frontend/src/components/TopBar.tsx`): Combined Score · Full Analysis · Quick Screener · Technical Screener · Assumptions.
