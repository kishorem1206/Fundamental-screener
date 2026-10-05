# Nifty Index Data Agent — Production Implementation Specification

## Objective

Build a production-ready **Nifty Index Data Ingestion and Classification system** inside the existing project.

The purpose of this system is to obtain official Nifty Indices constituent CSV data, store it reliably in the existing PostgreSQL database, maintain historical index membership, and expose a query layer that can determine **all Nifty indices to which a stock belongs**.

The official source is:

https://www.niftyindices.com/reports/index-factsheet

The source currently organizes indices into:

* Broad Market Indices
* Sectoral Indices
* Thematic Indices
* Strategy Indices
* Fixed Income Indices
* Hybrid Indices

Do not assume the list of indices is static. The implementation must dynamically support new indices, renamed indices, discontinued indices, and changes to source files.

---

# 1. IMPORTANT ARCHITECTURAL PRINCIPLE

Do NOT build this as:

```text
User asks stock
        ↓
LLM visits Nifty website
        ↓
LLM guesses/indexes membership
```

Build it as:

```text
Nifty Indices
     ↓
CSV ingestion
     ↓
Validation
     ↓
PostgreSQL
     ↓
Stock Index Classification Service
     ↓
LLM/API/UI
```

PostgreSQL must be the source of truth for stock-to-index membership.

The LLM must NOT invent or infer index membership.

If the database says a stock belongs to an index, return it.

If the database does not contain that membership, do not claim that it does.

---

# 2. FIRST: INSPECT THE EXISTING PROJECT

Before modifying anything:

1. Inspect the entire repository.
2. Understand the current architecture.
3. Identify:

   * Backend framework
   * Frontend framework
   * PostgreSQL configuration
   * ORM/query layer
   * Existing database migrations
   * Existing Docker configuration
   * Existing environment variables
   * Existing scheduled jobs/background workers
   * Existing API conventions
   * Existing testing framework
4. Reuse the existing architecture wherever practical.
5. Do NOT introduce a new framework unnecessarily.
6. Do NOT create a second PostgreSQL database.
7. Use the PostgreSQL database that already exists in the project.
8. Follow the project's existing naming conventions.

Before coding, provide a concise implementation plan based on what you discover.

Do not ask me to manually create tables if they can be created through the project's migration system.

---

# 3. SOURCE OF TRUTH

Primary source:

https://www.niftyindices.com/reports/index-factsheet

Use official Nifty Indices/NSE sources only for index classification data.

The system should support the following categories:

```text
BROAD_MARKET
SECTORAL
THEMATIC
STRATEGY
FIXED_INCOME
HYBRID
```

Do not hard-code only the currently visible index list.

The ingestion system must be capable of discovering/processing all available index data supplied by the source.

The current Nifty Indices page contains many indices under each category, so the implementation must be scalable and dynamic.

---

# 4. CORE COMPONENTS

Create the following logical components.

## Component A — Nifty Data Ingestion Service

Responsible for:

* discovering source data
* downloading CSV files
* parsing CSV files
* identifying the corresponding index
* identifying the index category
* normalizing stock identifiers
* validating records
* loading staging data
* comparing staging data with production data
* updating production tables
* recording ingestion metadata
* maintaining historical membership

Suggested name:

```text
NiftyIndexIngestionService
```

Use an appropriate name if the existing project has a better convention.

---

## Component B — Stock Index Classification Service

Responsible for queries such as:

```text
Which Nifty indices contain AUBANK?
```

```text
What sectoral indices contain ITC?
```

```text
Which thematic indices contain BEL?
```

```text
Give me every Nifty index containing TCS.
```

```text
Which stocks belong to Nifty Pharma?
```

This component must query PostgreSQL.

It must not scrape the website.

Suggested name:

```text
StockIndexClassificationService
```

---

# 5. DATABASE DESIGN

Create proper PostgreSQL migrations.

## Table: index_categories

Purpose:

Store supported Nifty index categories.

Suggested structure:

```text
id
code
name
description
created_at
updated_at
```

Example:

```text
BROAD_MARKET
SECTORAL
THEMATIC
STRATEGY
FIXED_INCOME
HYBRID
```

Use a database constraint or enum/reference table so invalid categories cannot silently enter the database.

---

# 6. TABLE: indices

Store the master index catalogue.

Suggested fields:

```text
id
index_name
index_code
category_id
source_url
source_identifier
is_active
first_seen_at
last_seen_at
created_at
updated_at
```

Important:

Do not assume `index_name` is sufficient as a unique identifier.

If the source provides an official index code/identifier, use that.

Otherwise create a robust normalized identifier.

Use appropriate unique constraints.

Example:

```text
Nifty 500
Nifty Bank
Nifty Financial Services
Nifty IT
Nifty Private Bank
Nifty India Defence
Nifty100 Quality 30
...
```

---

# 7. TABLE: stocks

If the existing project already has a stock/security master, reuse it.

Do NOT create a duplicate stock table unless necessary.

If no suitable table exists, create:

```text
id
symbol
company_name
isin
exchange
is_active
created_at
updated_at
```

The primary identifier should preferably be:

```text
ISIN
```

when available.

NSE symbol should also be indexed.

---

# 8. TABLE: index_constituents

This is the most important table.

Suggested structure:

```text
id
index_id
stock_id
weight
effective_from
effective_to
source_file_id
ingestion_run_id
created_at
updated_at
```

Add appropriate indexes on:

```text
stock_id
index_id
effective_from
effective_to
```

Add a uniqueness constraint preventing duplicate active membership records.

Conceptually:

```text
AUBANK
    ├── Nifty 500
    ├── Nifty Midcap 150
    ├── Nifty Bank
    ├── Nifty Financial Services
    ├── Nifty Private Bank
    ├── Nifty ...
    └── Nifty ...
```

A stock can belong to many indices.

An index can contain many stocks.

This is therefore a many-to-many relationship.

---

# 9. HISTORICAL MEMBERSHIP

Do NOT simply delete old membership when a quarterly update occurs.

Maintain history.

For example:

```text
AUBANK | Nifty Bank | effective_from = 2026-04-01 | effective_to = 2026-06-30

AUBANK | Nifty Bank | effective_from = 2026-07-01 | effective_to = NULL
```

If a stock leaves an index:

```text
effective_to = date_of_removal
```

If it remains:

keep the current record active.

If its weight changes, preserve the appropriate historical information rather than destroying the previous record.

The system should allow historical queries.

Example:

```text
Which Nifty indices contained AUBANK on 2026-06-15?
```

---

# 10. TABLE: source_files

Track every downloaded CSV.

Suggested structure:

```text
id
filename
source_url
index_id
category
file_hash
file_size
downloaded_at
effective_date
processed_at
processing_status
error_message
created_at
```

Use a cryptographic hash such as SHA-256.

If the same file is downloaded again, detect it using the hash and avoid unnecessary reprocessing.

---

# 11. TABLE: ingestion_runs

Every ingestion execution must be auditable.

Suggested fields:

```text
id
started_at
completed_at
source
status
files_discovered
files_downloaded
files_processed
records_read
records_inserted
records_updated
records_removed
records_unchanged
validation_errors
error_message
created_at
```

Statuses:

```text
RUNNING
SUCCESS
PARTIAL_SUCCESS
FAILED
```

---

# 12. STAGING TABLE

Do not load CSV data directly into production tables.

Create a staging process/table.

For example:

```text
staging_index_constituents
```

The pipeline should be:

```text
CSV
 ↓
staging_index_constituents
 ↓
validation
 ↓
comparison/diff
 ↓
production tables
```

This prevents a malformed CSV from corrupting the production dataset.

---

# 13. CSV INGESTION

The ingestion service must handle CSV variations robustly.

Do not assume every CSV will always have exactly the same column names.

Support common variations such as:

```text
Symbol
SYMBOL
Ticker
Company Name
Company Name
ISIN Code
ISIN
Weight (%)
Weight
```

Normalize headers before processing.

Example normalization:

```text
"Symbol" → symbol
"SYMBOL" → symbol
"Company Name" → company_name
"ISIN Code" → isin
"Weight (%)" → weight
```

Do not silently ignore unknown columns.

Log them.

---

# 14. STOCK IDENTIFIER NORMALIZATION

Implement a dedicated normalization function.

Example:

```text
normalize_symbol()
normalize_isin()
normalize_company_name()
```

Rules should include:

* trim whitespace
* normalize casing
* remove accidental surrounding spaces
* handle known source formatting differences
* preserve legitimate symbols exactly
* never use fuzzy matching without logging/review

ISIN should be preferred over company name for matching whenever available.

Do not match securities purely by company name.

---

# 15. INDEX CATEGORY DETECTION

Every index must have one of the supported categories.

Prefer source metadata rather than guessing from the index name.

For example:

```text
Nifty Bank
→ SECTORAL

Nifty 500
→ BROAD_MARKET

Nifty India Defence
→ THEMATIC

Nifty100 Quality 30
→ STRATEGY
```

Do not create logic such as:

```text
if "Bank" in index_name:
    category = SECTORAL
```

unless it is used only as a fallback and is clearly marked as inferred.

The source classification is authoritative.

---

# 16. FIXED-INCOME AND HYBRID INDICES

The source contains Fixed Income and Hybrid categories.

The database must support them.

However, the stock classification endpoint should distinguish:

```text
equity index membership
```

from:

```text
non-equity index membership
```

Do not incorrectly classify an equity stock as a constituent of a fixed-income index merely because the index catalogue exists.

Use an `asset_type`/instrument-type concept if required.

Example:

```text
EQUITY
BOND
DEBT
HYBRID
OTHER
```

---

# 17. INGESTION DIFF ENGINE

For every new ingestion:

Compare:

```text
previous production dataset
```

against:

```text
new staging dataset
```

Identify:

```text
NEW INDEX
REMOVED INDEX
RENAMED INDEX
NEW STOCK MEMBERSHIP
REMOVED STOCK MEMBERSHIP
WEIGHT CHANGE
UNCHANGED MEMBERSHIP
```

Produce a summary.

Example:

```text
Nifty Bank

Added:
- ABC
- XYZ

Removed:
- DEF

Weight changes:
- AUBANK: 2.34% → 2.51%

Unchanged:
- 10 constituents
```

---

# 18. TRANSACTION SAFETY

Production updates must be transactional.

Do not leave the database half-updated.

Recommended:

```text
BEGIN TRANSACTION

validate staging

update indices
update stocks
update memberships
close removed memberships
insert new memberships
update metadata
complete ingestion_run

COMMIT
```

If a critical error occurs:

```text
ROLLBACK
```

The previous valid dataset must remain intact.

---

# 19. VALIDATION

Before committing a new ingestion, validate:

### File validation

* file is readable
* expected columns exist
* no duplicate rows
* no completely empty file
* valid encoding
* valid dates

### Security validation

* HTTPS source only
* reasonable file size limits
* do not execute downloaded content
* protect against path traversal
* sanitize filenames

### Data validation

* valid symbols
* valid ISIN where supplied
* valid weights
* weights are numeric
* no impossible negative weights unless source explicitly permits them
* duplicate stock/index combinations detected
* index category exists

### Sanity checks

If an index previously had 50 constituents and the new file suddenly contains 0 or 2, treat this as suspicious and DO NOT automatically replace production data.

Require a validation failure.

Similarly, if an index suddenly changes by an extreme percentage, log a warning.

---

# 20. QUARTERLY UPDATE

The system must support automatic updates every 3 months.

However, do not assume that Nifty itself uses a universal quarterly rebalance schedule.

The requirement is:

```text
Our data refresh process runs quarterly.
```

The actual effective/rebalance date must come from the source data wherever available.

Create a configurable scheduler.

Do not hard-code a specific calendar date.

Configuration example:

```text
NIFTY_DATA_REFRESH_ENABLED=true
NIFTY_DATA_REFRESH_CRON=...
NIFTY_DATA_SOURCE_URL=https://www.niftyindices.com/reports/index-factsheet
```

Make the schedule configurable through environment variables/configuration.

---

# 21. MANUAL INGESTION

Also create a manual command.

Example:

```bash
npm run nifty:ingest
```

or the equivalent command based on the project's existing stack.

Also support:

```bash
npm run nifty:validate
```

```bash
npm run nifty:status
```

```bash
npm run nifty:diff
```

Use the project's existing command conventions instead of blindly using npm if the project uses another package manager.

---

# 22. DRY RUN

The ingestion service must support:

```text
--dry-run
```

Example:

```bash
npm run nifty:ingest -- --dry-run
```

Dry run must:

* download/read files
* validate
* calculate changes
* show proposed changes

but:

```text
MUST NOT modify production data.
```

---

# 23. API

Create an API for stock classification.

Example:

```http
GET /api/stocks/AUBANK/indices
```

Response:

```json
{
  "symbol": "AUBANK",
  "last_updated": "2026-07-01",
  "indices": {
    "broad_market": [],
    "sectoral": [],
    "thematic": [],
    "strategy": []
  }
}
```

Do not hard-code categories in application logic.

Categories should come from PostgreSQL.

---

# 24. API RESPONSE

Include useful metadata.

Example:

```json
{
  "symbol": "AUBANK",
  "company_name": "AU Small Finance Bank",
  "data_as_of": "2026-07-01",
  "source": "NSE Indices",
  "indices": {
    "broad_market": [
      {
        "name": "Nifty 500",
        "weight": 0.42
      }
    ],
    "sectoral": [
      {
        "name": "Nifty Bank",
        "weight": 1.23
      },
      {
        "name": "Nifty Financial Services",
        "weight": 0.81
      }
    ],
    "thematic": [],
    "strategy": []
  }
}
```

Only include weight when it is actually present in the source data.

Never fabricate weight.

---

# 25. INDEX → STOCK API

Also support the reverse lookup.

Example:

```http
GET /api/indices/nifty-bank/constituents
```

Return:

```json
{
  "index": "Nifty Bank",
  "category": "SECTORAL",
  "data_as_of": "2026-07-01",
  "constituents": []
}
```

---

# 26. HISTORICAL API

Support historical lookup.

Example:

```http
GET /api/stocks/AUBANK/indices?date=2026-06-15
```

This must use:

```text
effective_from <= requested_date
AND
(effective_to IS NULL OR effective_to >= requested_date)
```

Do not simply return the latest data.

---

# 27. CLASSIFICATION AGENT

Create a thin agent/query layer on top of the classification service.

The agent should be able to understand requests such as:

```text
Which indices contain AUBANK?
```

```text
What sectoral indices contain ITC?
```

```text
Which thematic Nifty indices contain BEL?
```

```text
Show me all strategy indices containing TCS.
```

```text
Which stocks are present in both Nifty Bank and Nifty Financial Services?
```

```text
Which Nifty indices did AUBANK enter in the latest update?
```

The agent should translate the request into structured database queries.

It must never invent membership.

---

# 28. AGENT GUARDRAILS

The agent must follow these rules:

1. PostgreSQL is the source of truth.
2. Never hallucinate an index.
3. Never infer membership from the company sector.
4. Never infer membership merely from the index name.
5. Never claim current membership without checking the latest valid ingestion.
6. If data is stale, explicitly state the data date.
7. If the requested stock does not exist, return a clear error.
8. If an index does not exist, return a clear error.
9. If data is missing, say so.
10. Do not silently fall back to Google or third-party websites.
11. Preserve the distinction between current and historical membership.

---

# 29. NATURAL LANGUAGE EXAMPLES

The agent should correctly handle:

### Example 1

User:

```text
What Nifty indices does AUBANK belong to?
```

Agent:

```text
AUBANK is currently present in:

Broad Market:
- ...

Sectoral:
- Nifty Bank
- Nifty Financial Services
- Nifty Private Bank

Thematic:
- ...

Strategy:
- ...

Data as of: YYYY-MM-DD
```

---

### Example 2

User:

```text
Give me all sectoral classifications for ITC.
```

Return only:

```text
SECTORAL
```

Do not mix in broad-market or strategy indices.

---

### Example 3

User:

```text
Which stocks are common between Nifty Bank and Nifty Financial Services?
```

Perform a PostgreSQL intersection query.

Do not ask an LLM to calculate the intersection from text.

---

# 30. DATABASE QUERY EXAMPLES

The implementation should support queries conceptually equivalent to:

```sql
SELECT
    i.index_name,
    c.name AS category,
    ic.weight
FROM index_constituents ic
JOIN indices i
    ON i.id = ic.index_id
JOIN index_categories c
    ON c.id = i.category_id
JOIN stocks s
    ON s.id = ic.stock_id
WHERE s.symbol = 'AUBANK'
  AND ic.effective_from <= CURRENT_DATE
  AND (
      ic.effective_to IS NULL
      OR ic.effective_to >= CURRENT_DATE
  )
ORDER BY c.name, i.index_name;
```

Use the project's ORM/query builder if one exists.

Do not introduce raw SQL everywhere unnecessarily.

---

# 31. PERFORMANCE

Add appropriate indexes.

At minimum optimize:

```text
stock symbol lookup
ISIN lookup
index lookup
stock_id + index_id
stock_id + effective dates
index_id + effective dates
```

The query:

```text
Which indices contain AUBANK?
```

should be extremely fast even after thousands of index memberships are stored.

---

# 32. CACHING

Do not cache aggressively during ingestion.

For API queries, optional caching may be introduced if the existing project already has Redis/cache infrastructure.

Do not add Redis solely for this feature unless there is a demonstrated need.

PostgreSQL should comfortably handle this dataset.

---

# 33. LOGGING

Use structured logging.

Every ingestion should log:

```text
ingestion_run_id
source
file
index
category
records_read
records_inserted
records_updated
records_removed
warnings
errors
duration
```

Do not log secrets.

---

# 34. ERROR HANDLING

Handle:

* website unavailable
* HTTP errors
* timeout
* malformed CSV
* changed CSV structure
* missing index metadata
* duplicate records
* database failure
* partial downloads
* unexpected encoding
* invalid dates
* invalid weights
* stock matching failures

The system must fail safely.

A failed quarterly ingestion must not destroy the previous valid dataset.

---

# 35. TESTING

Create comprehensive tests.

## Unit tests

Test:

```text
CSV header normalization
symbol normalization
ISIN normalization
category mapping
weight parsing
duplicate detection
date parsing
membership comparison
diff generation
```

## Integration tests

Test:

```text
CSV → staging → PostgreSQL
```

Test:

```text
new membership
removed membership
unchanged membership
weight change
```

## API tests

Test:

```text
GET stock indices
GET index constituents
GET historical membership
invalid stock
invalid index
```

## Agent tests

Test natural-language requests such as:

```text
Which indices contain AUBANK?
```

and verify that the final answer comes from database results.

---

# 36. TEST DATA

Do not depend on the live Nifty website for automated unit tests.

Create deterministic fixture CSVs.

Example:

```text
tests/fixtures/nifty/
    broad_market/
    sectoral/
    thematic/
    strategy/
```

Include small representative CSV files.

Integration tests should use a temporary/test PostgreSQL database or the project's existing test database infrastructure.

---

# 37. DOCUMENTATION

Create documentation for this feature.

At minimum:

```text
docs/nifty-index-data-agent.md
```

Document:

1. Architecture
2. Source
3. Database schema
4. Ingestion workflow
5. Quarterly update process
6. Manual ingestion
7. Dry run
8. Validation
9. API endpoints
10. Historical membership
11. Troubleshooting
12. How to add a new source format
13. How to recover from a failed ingestion

---

# 38. ENVIRONMENT VARIABLES

Add only the required environment variables.

Example:

```text
NIFTY_INDEX_SOURCE_URL=https://www.niftyindices.com/reports/index-factsheet

NIFTY_INDEX_INGESTION_ENABLED=true

NIFTY_INDEX_REFRESH_CRON=...

NIFTY_INDEX_REQUEST_TIMEOUT=...

NIFTY_INDEX_MAX_FILE_SIZE=...
```

Do not commit secrets.

Update `.env.example`.

Never put real credentials in the repository.

---

# 39. DOCKER

If the existing project uses Docker:

* integrate the ingestion service into the existing Docker architecture
* do not create a second PostgreSQL container
* ensure the service can connect to the existing PostgreSQL service
* make the scheduler production-safe
* ensure containers restart appropriately

If a scheduler already exists, reuse it.

Do not introduce duplicate scheduling mechanisms.

---

# 40. SCHEDULER DESIGN

Prefer the project's existing scheduling system.

If none exists, implement a simple production-safe scheduler/worker.

Avoid having multiple application instances execute the same quarterly ingestion simultaneously.

Use an appropriate locking mechanism, such as a PostgreSQL advisory lock, if required by the architecture.

Example conceptual flow:

```text
Scheduler
   ↓
Acquire ingestion lock
   ↓
Check whether a recent successful ingestion exists
   ↓
Run ingestion
   ↓
Release lock
```

---

# 41. DATA FRESHNESS

Expose:

```text
last_successful_ingestion
```

and:

```text
data_as_of
```

to the API.

If data is older than the configured expected refresh interval, return a warning/metadata flag.

Example:

```json
{
  "data_status": "STALE",
  "data_as_of": "2026-04-01"
}
```

Do not hide stale data.

---

# 42. SOURCE TRACEABILITY

Every production membership should be traceable back to:

```text
source_file
ingestion_run
effective_date
```

This is important because this system will eventually be used for investment/trading analytics.

A user should be able to determine:

```text
Why does the system say AUBANK belongs to Nifty Bank?
```

and trace it back to the source ingestion.

---

# 43. DATA LICENSING / TERMS

The implementation should respect the terms and licensing requirements of NSE Indices.

Do not circumvent authentication, licensing restrictions, robots controls, paywalls, or access restrictions.

Use only data that the application is permitted to retrieve and store.

Do not attempt to bypass anti-bot mechanisms.

If the required constituent data is only available through a licensed subscription/API, design the ingestion layer so the source adapter can be replaced with the authorized feed.

---

# 44. SOURCE ADAPTER ARCHITECTURE

Do not tightly couple the entire application to the Nifty website.

Create a source adapter abstraction.

Conceptually:

```text
IndexDataSource
      │
      └── NiftyIndicesSource
```

This allows a future source to be added:

```text
NSEIndexSource
LicensedNiftyDataSource
LocalCSVSource
```

without rewriting the database/classification layer.

---

# 45. LOCAL CSV SUPPORT

Because the data will be provided as CSV files, implement a local ingestion mode as well.

Example:

```bash
npm run nifty:ingest -- --directory ./data/nifty
```

The directory may contain:

```text
data/nifty/
    broad_market/
    sectoral/
    thematic/
    strategy/
    fixed_income/
    hybrid/
```

The system should be able to process these files without requiring the website.

This is important for:

* testing
* manual updates
* disaster recovery
* reproducibility
* development

---

# 46. CHANGE REPORT

After every successful ingestion, generate a machine-readable and human-readable summary.

Example:

```text
Nifty Index Data Update
=======================

Run ID: 2026Q3
Date: YYYY-MM-DD

Files discovered: 120
Files processed: 120

Indices:
    New: 2
    Updated: 15
    Removed: 1

Memberships:
    Added: 183
    Removed: 177
    Weight changes: 245
    Unchanged: 4,821

Warnings: 3
Errors: 0

Status: SUCCESS
```

Persist the summary.

If the project has an existing reporting/logging mechanism, integrate with it.

---

# 47. ADMIN/STATUS ENDPOINT

If appropriate for the existing application, create:

```http
GET /api/admin/nifty/ingestion/status
```

Return:

```json
{
  "last_run": "...",
  "status": "SUCCESS",
  "files_processed": 120,
  "records_processed": 5000,
  "last_data_date": "...",
  "next_scheduled_run": "..."
}
```

Protect admin endpoints appropriately.

---

# 48. IMPORTANT: DO NOT OVER-ENGINEER

Do not introduce:

* Kubernetes
* Kafka
* Airflow
* Redis
* separate microservices
* vector databases
* complex agent frameworks

unless the existing application already uses them or there is a clear requirement.

This dataset is relatively small compared with PostgreSQL's capabilities.

A well-designed:

```text
Python/Node ingestion service
+
PostgreSQL
+
scheduler
+
API
```

is sufficient.

---

# 49. EXPECTED FINAL DATABASE RELATIONSHIP

The final system should effectively represent:

```text
STOCK
  │
  │ many-to-many
  ▼
INDEX_CONSTITUENTS
  │
  ▼
INDEX
  │
  ▼
INDEX_CATEGORY
```

with:

```text
SOURCE_FILE
      │
      ▼
INGESTION_RUN
```

providing traceability.

---

# 50. EXAMPLE FINAL QUERY

When the user asks:

```text
Which Nifty indices does AUBANK belong to?
```

the system should execute a database query and produce something equivalent to:

```text
AUBANK

Broad Market
- Nifty 500
- ...

Sectoral
- Nifty Bank
- Nifty Financial Services
- Nifty Private Bank
- ...

Thematic
- ...

Strategy
- ...

Data as of:
2026-07-01

Source:
NSE Indices

Last successful ingestion:
2026-07-01
```

The exact index list must come entirely from PostgreSQL.

---

# 51. IMPLEMENTATION ORDER

Implement in this order:

### Phase 1 — Repository analysis

Inspect the existing project.

### Phase 2 — Database

Create migrations and tables.

### Phase 3 — Source adapter

Implement Nifty source handling.

### Phase 4 — CSV parser

Implement robust CSV normalization.

### Phase 5 — Staging

Implement staging tables/process.

### Phase 6 — Validation

Implement data validation and sanity checks.

### Phase 7 — Diff engine

Implement new/removed/changed membership detection.

### Phase 8 — Production ingestion

Implement transactional database updates.

### Phase 9 — Historical membership

Implement effective dates.

### Phase 10 — API

Implement stock → indices and index → stocks.

### Phase 11 — Scheduler

Implement quarterly ingestion.

### Phase 12 — Agent/query layer

Implement natural-language querying over the database.

### Phase 13 — Tests

Implement unit/integration/API/agent tests.

### Phase 14 — Documentation

Document the complete system.

---

# 52. DEFINITION OF DONE

The implementation is complete only when all of the following are true:

* [ ] Existing project architecture has been inspected.
* [ ] Existing PostgreSQL database is reused.
* [ ] Database migrations are created.
* [ ] All six Nifty categories are supported.
* [ ] Index master table exists.
* [ ] Stock master is reused or created appropriately.
* [ ] Many-to-many stock/index membership is implemented.
* [ ] Historical membership is preserved.
* [ ] Source files are tracked.
* [ ] Ingestion runs are tracked.
* [ ] CSV parsing is robust.
* [ ] CSV validation exists.
* [ ] Staging process exists.
* [ ] Diff engine exists.
* [ ] Production updates are transactional.
* [ ] Failed ingestion does not corrupt existing data.
* [ ] Dry-run mode exists.
* [ ] Manual ingestion exists.
* [ ] Quarterly scheduler exists.
* [ ] Duplicate scheduled executions are prevented.
* [ ] Stock → indices API exists.
* [ ] Index → stocks API exists.
* [ ] Historical lookup exists.
* [ ] Natural-language classification agent exists.
* [ ] Agent does not hallucinate memberships.
* [ ] Source traceability exists.
* [ ] Data freshness is exposed.
* [ ] Unit tests exist.
* [ ] Integration tests exist.
* [ ] API tests exist.
* [ ] Agent tests exist.
* [ ] Fixture CSVs exist.
* [ ] `.env.example` is updated.
* [ ] Docker configuration is updated if required.
* [ ] Documentation is complete.

---

# 53. FINAL INSTRUCTION TO CLAUDE CODE

Do not blindly start creating files.

First inspect the existing repository and determine:

1. current stack
2. current folder structure
3. existing PostgreSQL setup
4. existing ORM
5. existing migrations
6. existing scheduler/background jobs
7. existing API structure
8. existing Docker setup
9. existing environment configuration

Then provide the implementation plan.

After that, implement the feature incrementally.

Reuse existing components wherever possible.

Do not duplicate infrastructure.

Do not create mock implementations where a real implementation is required.

Do not hard-code the current Nifty index list.

The system must dynamically accommodate new Nifty indices and categories.

Most importantly:

**PostgreSQL is the source of truth.**

**Nifty Indices/NSE is the authoritative external source.**

**The LLM is only the query/interface layer and must never invent index membership.**
