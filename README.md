# Fundamental Screener

An AI-assisted fundamental analysis platform for the Indian equity market (NSE). It ingests financial data from multiple sources, runs sector-aware scoring across ~34 industry frameworks, and produces detailed analyst-style reports with peer comparison, risk flags, and AI-written commentary — for a single company or across the full ~1,600-stock universe.

## What it does

- **Full analysis pipeline** — a ~20-stage orchestrated pipeline per company: data ingestion (Screener.in, Yahoo Finance, NSE/BSE filings, annual reports, concall transcripts), ratio calculation, sector-specific scoring, peer comparison, risk/catalyst detection, and an LLM-written editorial report (with a PDF/HTML export that mirrors the live dashboard).
- **Sector-aware scoring** — 34 sector frameworks (Banks, NBFCs, IT Services, Pharma, FMCG, ...), each with its own metric set and score weights, plus universal fallbacks for everything else. Growth scores blend annual (FY CAGR) and recent-quarter momentum so a strong multi-year trend can't hide a real recent slowdown.
- **Quick Screener** — a Yahoo-only fast-scoring mode across the entire stock universe, for shortlisting before running a full analysis.
- **Peer comparison** — peers selected by NSE's own industry classification (basic industry → industry → sector fallback), enriched with Yahoo business-description similarity for thin industry buckets.
- **Balance sheet / cash flow / P&L intelligence engines** — deeper compute-on-read analysis layered on top of the core ledger (working capital, income quality, common-size analysis, coverage auditing).
- **Bank ROE simulator, concall intelligence, quarterly sector KPIs** — sector-specific deep dives (e.g. hospital ARPOB, bank NIM/cost-to-income, IT attrition) sourced from investor presentations, press releases, and earnings calls via LLM extraction.

## Tech stack

- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, PostgreSQL (+ pgvector for concall embeddings), Redis, Alembic migrations
- **Frontend**: React + TypeScript + Vite, Recharts
- **LLM**: Groq (`gpt-oss-20b`) primary, local Ollama fallback on rate limits
- **Data sources**: Screener.in (via `openscreener`), Yahoo Finance, NSE/BSE filings, annual reports, earnings-call transcripts

## Getting started

```bash
# Backend
cd backend
cp .env.example .env        # fill in your database URL, LLM key, etc.
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --port 3002 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                 # http://localhost:5174
```

Requires PostgreSQL (with the `pgvector` extension) and Redis running locally — see `.env.example` for the expected connection settings, and `HOW_TO_RUN.md` for the full setup walkthrough (Docker Compose, PDF renderer, migrations).

Every value in `.env.example` that isn't a placeholder is a safe local default; every placeholder (`your_..._key_here`) needs a real key from that provider before the corresponding feature works. Most of the app runs fine without every key filled in — the Screener.in login, IndianAPI key, and Gemini key are all optional, and each feature they gate degrades gracefully without them.

## Project layout

```
backend/    FastAPI app — pipeline, scoring, ingestion, routes (app/)
frontend/   React/Vite dashboard (src/)
Important md files/   Design docs, sector framework specs, architecture notes
```

See `HOW_TO_RUN.md` for detailed local setup and `Important md files/AGENTS.md` / `ARCHITECTURE.md` for how the pipeline and scoring system are put together.
