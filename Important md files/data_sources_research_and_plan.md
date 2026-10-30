# Data sources for Kishore Stock Screener — research and plan

Source list: *Market Analysis Websites Directory* (105 sites). Researched 2026-10-29.

How each site was judged: **can the app read it automatically, legally and
reliably**, and **does it fill a gap the app has today**. "Verified" means the
access route was tested live on 2026-10-29 (HTTP request or MCP handshake from
this machine); everything else is from documentation or third-party reports and
is marked as such.

---

## 1. What the app already reads

| Need | Source in use today | Where |
|---|---|---|
| Financial statements, ratios, quarterly results, shareholding, top ratios | Screener.in (first), Yahoo Finance (fallback) | `ingestion/screener_*`, `pnl_history_client.py`, `quick_analysis/screener_annual.py` |
| Exchange filings, results XBRL, annual reports, concalls, presentations, shareholding/pledge, IPOs | NSE (website feeds) | `ingestion/nse_*`, `bie/nse_filings.py` |
| Announcements | BSE (`api.bseindia.com`) | `ingestion/bse_client.py` |
| Corporate actions, price history for Yahoo gaps, live quotes, breadth | NSE MCP + NSE website | `nse_mcp/` |
| Daily prices (adjusted) | Yahoo; NSE bhavcopy as the check | `prices/` |
| Index prices with P/E, P/B, yield; index constituents | NSE daily index file; niftyindices.com | `prices/nse_indices.py`, `technical/services/nifty_index_ingestion_service.py` |
| Technical screening | TradingView screener, yfinance indicators | `technical/` |
| Holdings | Kite (read-only MCP) | `portfolio/kite_link.py` |
| Broker research history | Trendlyne (free table) | `ingestion/trendlyne_client.py` |
| Analyst consensus, movers | IndianAPI | `ingestion/indianapi_client.py` |
| Sector volumes / industry data | FADA, TRAI, AAI, AMFI monthly, IRDAI, GI Council, CEA/NPP, PPAC | `bie/volumes.py`, `ingestion/*_client.py` |
| Macro | MoSPI IIP API, Office of the Economic Adviser core industries, CCIL indicative yields, IMF DataMapper | `bie/official_data.py`, `bie/macro.py` |
| News | Google News search | `ingestion/news_search_client.py` |

The directory therefore matters most where the app is **thin today**:
regulatory and governance risk, credit ratings, institutional flows,
mutual-fund valuation in the portfolio, macro context (rates, liquidity,
inflation, global risk), earnings revisions, and a second opinion on scores.

---

## 2. How a site can be used

| Mode | Meaning | Used for |
|---|---|---|
| **Feed** | Official file, API or MCP the backend can read on a schedule | Numbers that go into scores or pages |
| **Scrape** | Undocumented endpoint or HTML; works but can break, and terms of use must be checked | Only where no official route exists and the value is high |
| **Link** | An "Open in …" button from a stock page; nothing stored | Manual verification and deep reading |
| **Skip** | Not useful for this app (US-only, F&O execution, institutional paid terminals, duplicates) | — |

Rule kept from the existing app: exchange and regulator sources are the
source of truth; aggregators (Screener, Tickertape, Trendlyne…) are
convenience layers and cross-checks; proprietary scores (MarketsMojo,
Trendlyne DVM, Tickertape scorecards) are *second opinions*, never inputs to
our own scores.

---

## 3. Recommendation by requirement

| Requirement | Best source | Mode | Why | Status |
|---|---|---|---|---|
| Regulatory / enforcement risk on a company or its promoters (Business Quality "regulatory risk", governance gate) | **SEBI RSS** (`sebi.gov.in/sebirss.xml`: orders, circulars, press releases) | Feed | Official, free; today's items name companies and individuals | **Verified** (orders dated 29 Oct 2026 in the feed) |
| Credit rating actions (downgrade = red flag; especially lenders, infra, leveraged) | **Exchange filings** ("Credit Rating" announcements under Reg 30, already readable through the NSE feeds the app uses) + agency rationale links (CRISIL, ICRA, CARE, India Ratings, Acuité, Infomerics) | Feed + Link | Every listed company must disclose rating actions to the exchange; agencies have no public API | NSE route proven in app; agencies: link only |
| Mutual-fund holdings in the portfolio (value, asset class) | **AMFI NAVAll.txt** | Feed | Official daily NAV for every scheme, with ISIN, free | **Verified** (1.5 MB, semicolon-delimited) |
| Institutional flows (FPI by sector, daily FPI equity/debt) | **NSDL FPI reports** (daily + fortnightly sector-wise); CDSL as backup | Feed (HTML/Excel tables) | Official source; sector-level FPI flows are a useful sector-strength signal | Daily page reachable; needs a parser |
| Indian macro: GDP, CPI, IIP, WPI | **MoSPI MCP / eSankhyiki API** | Feed | Official MCP server, no key | **Verified** (MCP live: `get_indicators`, `get_metadata`, `get_data`, `list_datasets`) |
| Rates, liquidity, banking credit growth | **RBI DBIE** (data.rbi.org.in) | Feed (CSV/Excel export) | Official; long time series | Site live; no documented API found — scheduled CSV download |
| Bond yields / yield curve (cost of capital in DCF, rate context) | **CCIL** (zero-coupon yield curve Excel daily ~7 pm; tenorwise yields) | Feed | Official; app already reads tenorwise yields for the deep report | In app (partly) |
| Budget / fiscal | India Budget | Link (annual) | Annual documents; low frequency | — |
| Policy events affecting sectors | **PIB RSS** | Feed (keyword-matched to sectors) | Official government releases | RSS exists (documented) |
| Global risk appetite | **CBOE VIX history CSV**; India VIX already in NSE index file | Feed | Free CSV since 1990 | **Verified** (data to 28 Oct 2026) |
| Global macro (US rates, dollar, commodities) | **FRED API** (free key) | Feed | Free, 120 requests/min | Key-free CSV timed out from here; use the API key route |
| Cross-country macro | **World Bank API**, IMF DataMapper (in app), OECD SDMX | Feed | Free, official | World Bank **verified**; IMF in app; OECD needs SDMX headers |
| Fed rate expectations | CME FedWatch API | Feed (paid, ~$25/month reported) | Only if global-rates context matters | Optional |
| Holdings from other brokers | **DhanHQ API** (official, `dhanhq` SDK), **Groww Trade API** (₹499/month reported), **Upstox API** (free, documented) | Feed | Alternatives to Kite; Dhan MCP still needs authorising | Docs found; needs your API keys |
| MF holdings across folios | MF Central | Link | No public API; servicing portal | — |
| Earnings revisions (framework section 5, currently not measured) | Trendlyne MCP (paid), TIKR / MarketScreener (paid or scrape), IndianAPI consensus (in app) | Feed if paid | No free official source; IndianAPI gives a current snapshot only — storing it daily would build our own revision history | Cheapest: snapshot IndianAPI consensus daily |
| Operational KPIs / business model | Tijori Finance | Link (no official API; community tools scrape a logged-in session) | Valuable reading, not automatable cleanly | Link |
| Second opinion on scores | Trendlyne (DVM), Tickertape (scorecard), MarketsMojo, MoneyWorks4Me, Value Research | Link (Tickertape unofficial API exists) | Compare with our classification; never feed into our score | Link; optional Tickertape cross-check column |
| Technical scans | TradingView (in app), Chartink (scan clause POST; needs session cookie) | In app / optional scrape | TradingView already covers most scans | Chartink optional |
| Company registry / directors | MCA | Link (free portal; APIs are paid vendors) | Director and charge checks during due diligence | Link |
| Concall transcripts beyond NSE | Quartr API (paid; India coverage unconfirmed) | Skip for now | App already reads NSE concall filings | — |
| News | Moneycontrol, ET Markets, Mint, Reuters (RSS feeds) | Feed (RSS) | Broader than the Google News search used now | RSS; check each site's terms |

---

## 4. Site-by-site review (all 105)

Legend — **Use**: Feed / Scrape / Link / Skip. **In app**: already used.

### Official and primary (1–15)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 1 | NSE India | Yes | Feed | Filings, results, shareholding, corporate actions, bhavcopy, indices, MCP | Source of truth; already the backbone |
| 2 | BSE India | Yes | Feed | Announcements; BSE-only companies; cross-check dual-listed filings | Unofficial `bse` Python package documents the announcement endpoints |
| 3 | SEBI | No | **Feed** | Orders, enforcement, circulars via RSS → governance/regulatory red flags per company | **Verified** RSS live |
| 4 | RBI Statistics (DBIE) | No | **Feed** | Repo, liquidity, bank credit/deposit growth, sectoral credit → lender sector context, cost of capital | CSV/Excel export; API not documented |
| 5 | MCA | No | Link | Directors, charges, company status for due diligence | Programmatic access only via paid vendors |
| 6 | AMFI | Partly (monthly AUM report) | **Feed** | Daily NAV for every scheme → value MF holdings in Portfolio; MF industry flows | **Verified** NAVAll.txt |
| 7 | NSDL | No | **Feed** | FPI daily flows, fortnightly sector-wise FPI holdings → institutional flow signal per sector | Page reachable; parser needed |
| 8 | CDSL | No | Skip / backup | Depository stats; FPI data mirror | Use only if NSDL changes |
| 9 | MoSPI | Partly (IIP API) | **Feed** | GDP, CPI, IIP, WPI, ASI through the MoSPI MCP | **Verified** MCP live, no key |
| 10 | India Budget | No | Link | Budget documents, fiscal numbers | Annual |
| 11 | DPIIT | No | Link | FDI factsheets, industrial policy | Quarterly PDFs; sector context only |
| 12 | PIB | No | Feed (optional) | Government announcements → sector policy events | RSS |
| 13 | CCIL | Partly | **Feed** | Zero-coupon yield curve (daily Excel) → risk-free rate for DCF; G-Sec yields | Extend the deep report's use |
| 14 | FIMMDA | No | Skip | Bond valuation conventions | Member-oriented |
| 15 | Nifty Indices | Yes | Feed | Index constituents; index P/E, P/B history and TRI (undocumented `Backpage.aspx` endpoints) | TRI would give true total-return benchmarks |

### India equity research (16–40)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 16 | Screener.in | Yes | Feed | Statements, ratios, ROCE (single source), shareholding | Primary fundamental source |
| 17 | Tijori Finance | No | Link | Business model, segment KPIs, sector context | No official API; community tools use a logged-in browser |
| 18 | Trendlyne | Yes (broker reports) | Feed (paid MCP) / Link | Estimates, DVM scores, credit-rating feed per company, insider trades | Has an official paid MCP; would fill **earnings revisions** |
| 19 | Tickertape | No | Link / optional Scrape | Scorecard, screener data, index constituents | Unofficial API (tickersnap, bharat-sm-data); second opinion only |
| 20 | StockEdge | No | Link | Scans, ownership | No API |
| 21 | ScanX | No | Link | Combined scans, market activity | No API |
| 22 | StockScans | No | Skip | Event scanning | App reads filings directly |
| 23 | NSE Market Lens | No | Link | NSE's own screener (beta, 2,000+ stocks) | Useful to cross-check screens; no API |
| 24 | Fuzz (AskFuzz.ai) | No | Link | Document search | Answers must be traced to source |
| 25 | MarketsMojo | No | Link | Quality / valuation / trend scores (closest to our framework) | Good benchmark for our classifications; no current public API |
| 26 | MarketSmith India | No | Skip / Link | CAN SLIM growth-momentum ratings | Paid; our Technical + RS cover momentum |
| 27 | Finology Ticker | No | Link | Fundamental screening | Duplicate of Screener |
| 28 | MoneyWorks4Me | No | Link | Long-term quality and valuation | Second opinion |
| 29 | Value Research Online | No | Link | Stock and fund research | Fund ratings for portfolio context |
| 30 | PrimeInvestor | No | Skip | Paid recommendations | Opinion layer |
| 31 | Research 360 | No | Skip | Broker research ideas | Trendlyne already gives broker history |
| 32 | Trade Brains Portal | No | Skip | Retail screener | Duplicate |
| 33 | Equitymaster | No | Skip | Commentary | Opinion |
| 34 | Definedge RADAR | No | Link | Fundamental scans, peer comparison | Cross-check |
| 35 | Capitaline | No | Skip (paid) | Institutional database | Consider only with a subscription |
| 36 | CMIE ProwessIQ | No | Skip (paid) | Deep company database | Institutional |
| 37 | ACE Equity | No | Skip (paid) | Company and corporate-action data | Institutional |
| 38 | Moneycontrol | No | Feed (RSS) / Link | News, results, consensus | RSS for news; verify numbers with filings |
| 39 | ET Markets | No | Feed (RSS) | Market news, broker views | Separate fact from opinion |
| 40 | Mint Markets | No | Feed (RSS) | Business news | Context |

### Technical and charting (41–52)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 41 | TradingView | Yes | Feed | Screener (80 markets, 1,135 fields), MCP for charts | Already in the Technical Screener |
| 42 | Chartink | No | Optional Scrape | Custom technical scans (scan-clause syntax) | Needs session cookie and XSRF token; fragile |
| 43 | Investing.com | No | Link | Global quotes, economic calendar | Terms restrict scraping; use FRED / Trading Economics for data |
| 44 | GoCharting | No | Skip | Order flow, market profile | Trading-oriented |
| 45 | StockCharts | No | Skip | US charting | US-centric |
| 46 | Finviz | No | Skip | US screening | US only |
| 47 | Barchart | No | Skip | Futures, commodities | Optional for commodity context |
| 48 | TrendSpider | No | Skip | Automated TA | Paid, US |
| 49 | ChartMill | No | Skip | Screening | US/global |
| 50 | MarketInOut | No | Skip | Screening | Candidate generation only |
| 51 | Streak | No | Skip | Strategy backtests (Zerodha) | Execution-oriented |
| 52 | ProRealTime | No | Skip | Professional charting | Paid |

### Options and derivatives (53–62)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 53 | Sensibull | No | Skip | Option chain, OI | App is not an F&O tool; no official API |
| 54 | Opstra | No | Skip | Options analytics | No API |
| 55 | Quantsapp | No | Skip | Options analytics | No API |
| 56 | Strike.money | No | Skip | Derivatives insights | Secondary |
| 57 | AlgoTest | No | Skip | Options backtests | Out of scope |
| 58 | StockMock | No | Skip | Options simulation | Out of scope |
| 59 | Tradetron | No | Skip | Strategy automation | Out of scope |
| 60 | NeoStox | No | Skip | Paper trading | Out of scope |
| 61 | Stolo | No | Skip | F&O terminal | Out of scope |
| 62 | Dhan | Partly (MCP, not authorised) | **Feed** | Holdings via official DhanHQ API (`dhanhq` SDK) as a second broker | Needs your client ID and token (24-hour tokens) |

Note: if F&O ever matters for the framework (e.g. open-interest build-up as a
technical confirmation), NSE's own derivatives bhavcopy and Upstox's free
option-chain API are the clean routes, not these sites.

### Credit and debt risk (63–68)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 63 | CRISIL Ratings | No | Link + filings | Rating rationales | Rating actions also arrive as exchange filings |
| 64 | ICRA | No | Link + filings | Company / sector credit reports | Especially lenders, infra |
| 65 | CARE Ratings | No | Link + filings | Ratings | Check surveillance date |
| 66 | India Ratings & Research | No | Link + filings | Ratings | Cross-check |
| 67 | Acuité | No | Link + filings | SME / mid-market ratings | Small caps |
| 68 | Infomerics | No | Link + filings | Issuer ratings | Small caps |

How ratings enter the app: read "Credit Rating" announcements from the
exchange feeds already in use, store agency, instrument, old and new rating and
outlook, and treat a **downgrade or negative outlook in the last 12 months** as
a governance / balance-sheet red flag in the decision engine (section 17 of the
framework). Rationale PDFs open from the stock page.

### Mutual funds and ETFs (69–77)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 69 | Morningstar India | No | Link | Fund ratings, portfolio analysis | No public API |
| 70 | Advisorkhoj | No | Link | Rolling returns | Confirm NAVs with AMFI |
| 71 | ET Money | No | Skip | Retail platform | — |
| 72 | Groww | No | Feed (optional) | Holdings via Groww Trade API | Paid API (₹499/month reported) |
| 73 | ETF.com | No | Skip | US ETFs | — |
| 74 | justETF | No | Skip | UCITS ETFs | — |
| 75 | Portfolio Visualizer | No | Link | Asset-allocation backtests | Complements section 14; not automatable |
| 76 | VettaFi ETF Database | No | Skip | US ETFs | — |
| 77 | MF Central | No | Link | Consolidated MF holdings across folios | Verification only; no public API |

### Global equity research (78–92)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 78 | Yahoo Finance | Yes | Feed | Adjusted prices, Yahoo statements (fallback) | Kept as fallback |
| 79 | Google Finance | No | Skip | Quotes | Duplicate |
| 80 | Koyfin | No | Link | Cross-asset dashboards | No API on the free tier |
| 81 | TIKR | No | Skip / paid | Global financials, consensus estimates | Would fill earnings revisions if subscribed |
| 82 | Quartr | No | Skip for now | Transcripts and IR documents (API) | Paid; India coverage not confirmed |
| 83 | AlphaSense | No | Skip | Institutional search | Expensive |
| 84 | SEC EDGAR | No | Skip | US filings | Only for US-listed peers / ADRs |
| 85 | Nasdaq | No | Skip | US market data | — |
| 86 | MarketScreener | No | Link | Global estimates | Consensus context |
| 87 | Simply Wall St | No | Skip | Visual summaries | — |
| 88 | GuruFocus | No | Skip | Value models | — |
| 89 | Seeking Alpha | No | Skip | Opinions | — |
| 90 | StockAnalysis.com | No | Skip | US statements | — |
| 91 | Macrotrends | No | Skip | Long US/global series | — |
| 92 | CompaniesMarketCap | No | Link | Global market-cap rankings | Peer scale |

### Macro and economic data (93–100)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 93 | FRED | No | **Feed** | US yields, dollar, oil, global series | Free API key; 120 requests/min |
| 94 | Trading Economics | No | Feed (paid) / Link | Economic calendar, country data | API ~$149+/month reported; calendar is the useful part |
| 95 | World Bank Data | No | **Feed** | Long-run India and peer-country indicators | **Verified** API |
| 96 | IMF Data | Yes (DataMapper) | Feed | Forecasts and cross-country macro | In deep report |
| 97 | OECD Data | No | Feed (optional) | Leading indicators | SDMX API |
| 98 | CME FedWatch | No | Feed (paid, optional) | Fed rate probabilities | ~$25/month reported |
| 99 | CBOE | No | **Feed** | VIX history (global risk appetite) | **Verified** CSV |
| 100 | MacroMicro | No | Link | Cycle dashboards | Derived |

### Professional and news (101–105)

| # | Site | In app | Use | What it gives this app | Notes |
|---|---|---|---|---|---|
| 101 | Reuters Markets | No | Link / RSS | Fast factual news | Licensing for data |
| 102 | Bloomberg Markets | No | Link | News | Paywall |
| 103 | S&P Capital IQ | No | Skip (institutional) | Deals, company data | Enterprise |
| 104 | FactSet | No | Skip (institutional) | Data and analytics | Enterprise |
| 105 | LSEG Workspace | No | Skip (institutional) | Terminal | Enterprise |

**Count:** 16 to read automatically (Feed), 4 optional paid feeds, 2
optional scrapes, about 35 to link from stock pages, the rest skipped.

---

## 5. Plan

Each phase is small, uses official sources first, and ends with a check against
the source. Phases can be done in any order; the first two give the most value.

### Phase A — Risk and governance (fills framework gaps) — BUILT 2026-10-30 (`backend/app/risk/`)
1. **SEBI orders feed** → `sebi_orders` table; match order titles to company
   names, ISINs and promoter names (from shareholding filings). A recent order
   against the company or a promoter becomes a **governance red flag** in the
   core gate, and Business Quality's "regulatory risk" stops being "not
   measured" for those companies.
2. **Credit rating actions from exchange filings** → `credit_ratings` table
   (agency, instrument, rating, outlook, date, rationale link). Changed by the user
   on 2026-10-30: credit ratings affect no score or flag and appear only in
   the full analysis report, with the agency rationale linked from there.

### Phase B — Portfolio completeness — BUILT 2026-10-30 (`portfolio/amfi.py`, `portfolio/brokers.py`)
3. **AMFI NAV** → value mutual-fund holdings daily; ISIN match; classify by
   scheme category (debt, gold, international, equity) from AMFI's own
   category headings instead of guessing from the fund name.
4. **Broker APIs** → DhanHQ (official SDK) and optionally Groww / Upstox as
   sources next to Kite (needs your keys).

### Phase C — Market and macro context page — BUILT 2026-10-30 (`backend/app/macro/`; bank credit growth not available; item 6 was already in place)
5. **Macro page**: MoSPI MCP (GDP, CPI, IIP, WPI), RBI DBIE (repo, credit
   growth, liquidity), CCIL yield curve, India VIX (already stored), CBOE VIX,
   FRED (US 10-year, dollar index, Brent), World Bank / IMF for long-run.
6. **Use in valuation**: the 10-year G-Sec from CCIL as the risk-free rate in
   the deep report's DCF instead of a fixed number.

### Phase D — Flows — BUILT 2026-10-30 (`macro/fpi.py`; shown, not scored)
7. **NSDL FPI**: daily FPI equity flows (market context) and fortnightly
   sector-wise FPI holdings → a sector flow signal next to sector benchmarks in
   Relative Strength (shown, not scored, until validated).

### Phase E — Second opinions and links — BUILT 2026-10-30 (Open-in bar; cross-check column not built: scores are paid or unofficial)
8. **"Open in" bar** on every stock: Screener, NSE, BSE, Tijori, Trendlyne,
   Tickertape, MarketsMojo, TradingView, Chartink, MCA, the rating agency,
   Moneycontrol — so manual verification is one click.
9. **Optional cross-check column**: Tickertape scorecard or Trendlyne DVM next
   to our classification, flagged where they disagree strongly. Never an input
   to our scores.

### Phase F — Earnings revisions (framework section 5) — BUILT 2026-10-30 (Yahoo estimate history; shown on the stock, not scored, by the user's decision)
10. Snapshot IndianAPI consensus (already in the app) daily and compute
    revisions from our own history; if you subscribe to Trendlyne's MCP or
    TIKR, use their estimate history instead. Until then, revisions stay "not
    measured".

### Phase G — News breadth — BUILT 2026-10-30 (Economic Times, Mint; Moneycontrol feeds dead, PIB Hindi only)
11. Add RSS from Moneycontrol, ET Markets, Mint and PIB alongside the current
    Google News search, matched to companies and sectors.

### Not recommended
- F&O analytics sites (Sensibull, Opstra, Quantsapp …): outside the app's purpose.
- Institutional terminals (Capital IQ, FactSet, LSEG, CMIE, ACE, Capitaline):
  cost; consider only with a subscription.
- US-centric tools (Finviz, StockCharts, EDGAR …) unless US stocks are added.
- Scraping Investing.com, Tijori, MarketsMojo: terms and fragility outweigh value.

---

## 6. Sources checked

Live checks (2026-10-29): AMFI NAVAll.txt, CBOE VIX_History.csv, SEBI RSS,
MoSPI MCP (initialize + tools/list), World Bank API, NSDL FPI daily page, CCIL
tenorwise yields, data.rbi.org.in (DBIE), Upstox API docs.

Documentation and third-party reports used:
- RBI DBIE downloads — https://website.rbi.org.in/documents/87730/39710577/83889.pdf
- MoSPI MCP — https://glama.ai/mcp/servers/nso-india/esankhyiki-mcp
- AMFI NAV file — https://github.com/fuzail-pixel/amfi-nav-extractor
- SEBI FPI sector data — https://www.sebi.gov.in/hindi/statistics/fpi-investment/fortnightly-sector-wise.html
- Tijori (no official API) — https://glama.ai/mcp/servers/rj250792/tijori-finance-mcp
- Trendlyne MCP — https://trendlyne.com/subscription/mcp/plans/
- Chartink scan endpoint — https://github.com/PriceCatch/Chartink
- NSE Market Lens — https://www.freepressjournal.in/business/nse-market-lens-explained-how-can-investors-screen-over-2000-stocks
- DhanHQ API — https://dhanhq.co/docs/DhanHQ-py/
- CCIL yields — https://www.ccilindia.com/tenorwise-indicative-yields
- Tickertape unofficial API — https://mratanusarkar.github.io/tickersnap
- Nifty Indices endpoints — https://freefincal.com/download-nifty-historical-data-price-total-returns-pe-pb-div-yield/
- BSE unofficial API — https://pypi.org/project/bse
- SEBI RSS — https://www.sebi.gov.in/rss.html
- MCA data access — https://surepass.io/faq/what-is-the-mca-data-api/
- Groww Trade API — https://groww.in/trade-api/docs/curl/changelog
- FRED API — https://www.federalreserve.gov/data/ddp-fred-user-guide.htm
- Quartr API — https://quartr.com/pricing/api
- MarketsMojo — https://www.caplight.com/company/marketsmojo
- CME FedWatch API — https://www.cmegroup.com/market-data/market-data-api/fedwatch-api.html
- PIB RSS — https://www.pib.gov.in/ViewRss.aspx
- Options tools (no APIs) — https://algotest.in/blog/sensibull-alternatives-india/
- Trading Economics API — https://www.tradingeconomics.com/api
