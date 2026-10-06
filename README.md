# Fundamental Screener

An AI-assisted equity research platform for the Indian market (NSE): fundamental and technical analysis in one app. It ingests financial data from multiple sources, scores every listed company on the Stock Quality & Portfolio Replacement framework (Quality, Fundamental, Quantitative, Relative Strength, Technical and Valuation, kept separate and never averaged), classifies each stock and compares it with what you own — on top of the original sector-aware fundamental analysis, deep reports and technical screener — across the full ~2,600-stock universe.

## What it does

- **Combined Score** — the framework's six scores side by side for every stock, with a classification (Core Quality, Investable, Improving / Watch, Recovery Candidate, Tactical Only, Replacement Candidate, Avoid), an action, Quality momentum against 6 and 12 months ago, sector rank, and every input with its source. Rules decide; gpt-oss only explains, and its explanation is checked against the decision.
- **Portfolio** — holdings from Kite (read-only, the app's own connection to Zerodha's Kite MCP server), a broker CSV (Dhan, Zerodha console…) or by hand; each holding compared with the best same-sector alternative, sized within your limits, and checked against your asset-allocation targets and drawdown tolerance.
- **Technical Screener** — the former Stock screener app, merged in: RSI momentum, RSI divergence, MACD, a DSL screen builder, the TradingView screener (80 markets) and an AI chat.
- **Integrated report** — one PDF per company: the framework section, the editorial report and the deep report.
- **Price store** — three years of daily prices for every stock (adjusted) and every NSE index (with P/E, P/B, yield), checked against NSE's official closing prices.

- **Full analysis pipeline** — a ~20-stage orchestrated pipeline per company: data ingestion (Screener.in, Yahoo Finance, NSE/BSE filings, annual reports, concall transcripts), ratio calculation, sector-specific scoring, peer comparison, risk/catalyst detection, and an LLM-written editorial report (with a PDF/HTML export that mirrors the live dashboard).
- **Sector-aware scoring** — 34 sector frameworks (Banks, NBFCs, IT Services, Pharma, FMCG, ...), each with its own metric set and score weights, plus universal fallbacks for everything else. Growth scores blend annual (FY CAGR) and recent-quarter momentum so a strong multi-year trend can't hide a real recent slowdown.
- **Quick Screener** — fast scoring of the entire universe, Screener.in first with Yahoo Finance as fallback (one page read per company), for shortlisting before running a full analysis.
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
backend/    FastAPI app (app/)
  app/framework/    Stock Quality framework: six scores, momentum, decision engine, explanation
  app/portfolio/    holdings, Kite link (read-only), portfolio analysis
  app/prices/       daily price store for stocks and NSE indices
  app/technical/    the merged technical screener (routes under /api/technical)
  app/bie/          deep report engine
  app/reporting/    editorial and integrated reports
frontend/   React/Vite app (src/; technical screener pages in src/technical/)
containers/ Docker Compose: Postgres, Redis, MinIO
Important md files/   Design docs, framework specs, architecture notes
```

See `HOW_TO_RUN.md` for detailed local setup, `Important md files/stock_quality_framework_implementation.md` for every framework score's formula and source, and `Important md files/AGENTS.md` / `ARCHITECTURE.md` for how the pipeline and scoring system are put together.
