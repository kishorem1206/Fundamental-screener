# LLM Usage Reference

Reference doc for every place this codebase calls an LLM — Groq (primary) and
local Ollama (fallback, and in two places the *primary*). Written 2026-09-23
after auditing every call site in `backend/app/`. Update this file whenever a
new LLM call site is added, a model changes, or a rate-limit workaround is
retuned — it exists so a future session doesn't have to re-derive this from
scratch.

## 1. The core client — `app/llm/client.py`

One class, `LLMClient`, instantiated twice as module-level singletons:

- `llm_client = LLMClient()` — **Groq-primary**. Falls back to Ollama.
- `local_llm_client = LLMClient(primary="local")` — **Ollama-primary**. Falls back to Groq.

Public methods:
- `chat(system_prompt, user_prompt, json_mode=False, max_tokens=None) -> str`
- `chat_json(system_prompt, user_prompt, max_tokens=None) -> dict` — calls
  `chat()` with `json_mode=True`, `json.loads()`s the result, and falls back
  to a regex `\{.*\}` extraction before raising `ValueError` if parsing still
  fails.

**Fallback direction is NOT symmetric — this is the single most important
thing to remember about this system:**

| Client | Primary | Fallback | Fallback triggers on |
|---|---|---|---|
| `llm_client` (Groq-primary) | Groq `gpt-oss-20b` | Ollama `llama3.2:3b` | **only** `RateLimitError` (HTTP 429) — any other exception (bad prompt, schema bug) propagates as a real error, it does not silently degrade to the weaker local model |
| `local_llm_client` (Ollama-primary) | Ollama `llama3.2:3b` | Groq `gpt-oss-20b` | **any** `Exception` — Ollama has no rate-limit concept, so a down daemon just raises a connection error/timeout, not a typed rate-limit exception |

The Groq `OpenAI()` SDK client is built with `max_retries=1` (not the SDK
default) specifically to shrink the SDK's own backoff-and-retry loop on 429 —
the default behavior caused multi-minute pipeline stalls when several calls
collided. The intent is "one quick retry, then fail over to Ollama instead of
waiting through Groq's full backoff sequence."

Every call records `self.last_used_fallback` (bool) and
`self.last_token_count` — callers are expected to treat a fallback-served
answer as lower-confidence than a primary one. `annual_report_ingestion.py`
is the one place that actually acts on `last_used_fallback` today (see §5).

## 2. Config — `app/config.py`

```
llm_model              = "openai/gpt-oss-20b"
llm_api_base_url       = "https://api.groq.com/openai/v1"
llm_max_tokens         = 4096      # default when a caller passes none
llm_temperature        = 0.1
llm_fallback_enabled   = True
llm_fallback_base_url  = "http://localhost:11434/v1"   # Ollama OpenAI-compat endpoint
llm_fallback_model     = "llama3.2:3b"
ollama_base_url        = "http://localhost:11434"       # Ollama's native (non-OpenAI-compat) endpoint
embedding_model        = "qwen3-embedding"
embedding_dims         = 4096
gemini_api_key / gemini_api_base_url / gemini_model      # configured, NOT wired up anywhere (see §3)
```

`llm_api_key`/`gemini_api_key` come from `.env`, empty string by default.
**No config field holds the "8000 TPM" number** — that constraint only exists
as hand-tuned `max_tokens`/char-budget values plus comments explaining why
(see §6). If Groq's tier limit ever changes, every value in §6's table needs
re-tuning by hand; nothing reads a single source of truth for it.

## 3. Every call site

All chat call sites go through `llm_client.chat_json(...)` or
`local_llm_client.chat_json(...)` — nothing instantiates its own `OpenAI`
client or calls `.chat()` directly outside `client.py` itself.

### Groq-primary (`llm_client`)

| File | Function | Purpose | Expected shape |
|---|---|---|---|
| `app/pipeline/orchestrator.py:1812` | `_run_ai_analysis()` | Final investment-thesis narrative persisted to `FundamentalAnalysis.ai_analysis` | `rating`, `conviction`, `confidence`, `business_quality`/`growth_quality`/`financial_quality` (0-100), `valuation_view`, `executive_summary`, `investment_thesis[]`, `bull_case[]`, `bear_case[]`, `key_risks[]`, `key_catalysts[]`, `monitoring_points[]` |
| `app/ingestion/annual_report_ingestion.py:635` | `extract_area(area, text, ...)` | Per-area note extraction from annual reports (PPE, raw material cost, R&D, revenue geography, banking asset quality/funding/capital, sector operating metrics) | flat dict of nullable numeric fields + `period_label`, schema per area in `_AREA_PROMPTS` |
| `app/ingestion/banking_ingestion.py:86` | `extract_metrics_from_ocr_text()` | Extracts CAR/gross-NPA/net-NPA/ROA/advances/deposits from OCR'd bank filing text (input capped `[:8000]` chars, `max_tokens=3000`) | dict matching `_REPORTED_FIELDS` |
| `app/ingestion/earnings_call_client.py` | `extract_it_operational_metrics()`, `extract_fintech_operational_metrics()`, `extract_fmcg_operational_metrics()` | Sector-specific operational KPIs from concall transcripts (attrition/utilization/deal-TCV for IT; GTV/take-rate/contribution-margin for fintech; FMCG-specific KPIs) — input capped `[:16000]` chars, `max_tokens=3000` | one dict per sector, sector-specific keys |
| `app/ingestion/quarterly_operating_metrics_ingestion.py:1006` | `extract_area(prompt_key, text, ...)` | Generic per-sector quarterly operating-metric extraction from NSE investor-presentation/concall text (input capped `[:8000]` chars, `max_tokens=3000`) | keyed by `_AREA_PROMPTS[prompt_key]` |
| `app/interpretation/guidance_extraction.py:234` | `_extract_from_batch()` | Concall Intelligence Stage C3 — management guidance extraction (targets/ranges/periods), restricted to CEO/CFO/Deputy MD/COO/Chairman utterances by construction | `{"guidance_items": [...]}` |
| `app/interpretation/guidance_extraction.py:455` | `_extract_topics_from_batch()` | Concall Topic-Sentiment Grid — tags each utterance with 1 of 10 fixed topics + sentiment | `{"topic_items": [...]}` |

Guidance/topic extraction is deliberately Groq-primary rather than using the
Ollama-primary client the rest of the interpretation pipeline uses — local
Llama alone produced schema-placeholder-text leakage and self-contradictory
items on first real test (see `guidance_extraction.py`'s own docstring).

### Ollama-primary (`local_llm_client`)

| File | Function | Purpose | Expected shape |
|---|---|---|---|
| `app/interpretation/llama_interpreter.py:58` | `_run_section()`, via `generate_report_blueprint()` | One call per modular blueprint section (`app/interpretation/prompts/sections.py` defines the sections) | `{content, key_points?}` or `{items: [...]}` depending on `content_type` |
| `app/interpretation/brand_extraction.py:103` | `extract_brands(key_points)` | Extracts named brands (market share %, owned/licensed) from a company's Screener "Key Points" text; gated on `len(key_points) >= 400` chars | `{"brands": [...]}` |

### Non-chat LLM-adjacent (embeddings, not chat completions)

`app/interpretation/embeddings.py:23` — `embed_text(text)` (Concall
Intelligence Stage C2). Calls Ollama's **native** `/api/embeddings` endpoint
directly via `requests.post`, NOT through `LLMClient`/the OpenAI SDK (a
different API shape). Model `qwen3-embedding`, 4096-dim. Used by
`app/interpretation/concall_retrieval.py` for semantic similarity search over
concall utterances. Returns `None` on any failure (never raises, never
returns a zero vector — a zero vector would silently corrupt similarity
search for every other chunk it's compared against).

### Confirmed NOT calling an LLM

`app/sectors/*.py` (only comment on a prior Groq-quota incident),
`app/routes/*.py` (comment-only references to LLM provider quota/timing),
`app/interpretation/concall_report_data.py` (explicit docstring: "no new LLM
call here... render what's real, don't fabricate"),
`app/interpretation/prompts/sections.py` (prompt text data, not a call site
itself), `app/services/*.py`.

### Gemini — configured but unused

`app/config.py` defines `gemini_api_key`/`gemini_api_base_url`
(`https://generativelanguage.googleapis.com/v1beta/openai/`)/
`gemini_model="gemini-3.8-flash"` for a planned 2026-09-15 evaluation against
Groq's `gpt-oss-20b`. Nothing in `app/` actually instantiates a Gemini client
or calls it — config-only, not wired to any call site as of this writing.

## 4. The GPT-OSS bypass workflow (manual override)

Established this session as the standard workaround when Groq's rate limit
or output quality makes the LLM-generated `ai_analysis` untrustworthy for a
given company:

1. Clear the company's Redis cache (`fa:*:{SYMBOL}` keys).
2. Trigger a fresh full pipeline run (creates a new `FundamentalAnalysis`
   row, runs every ingestion/calculation stage — the `ai_analysis` stage
   still runs and writes *something*, whether real or a rate-limit-degraded
   answer).
3. Pull the company's real computed data (`scores`, `metrics`, `risks`,
   `catalysts`, peer list) directly from the DB.
4. Hand-author a replacement `ai_analysis` JSON dict, grounded in those real
   numbers, matching the exact schema `_run_ai_analysis()` produces (§3
   table above).
5. Write it directly to `FundamentalAnalysis.ai_analysis` (plus `ai_rating`,
   and `model_version`/`prompt_version` set to something like
   `"MANUAL_ANALYST_<date>"`/`"manual-v1"` so it's traceable as hand-authored,
   not model-generated) via a one-off DB script.
6. Regenerate the PDF: delete the stale `reports/{analysis_id}.html`/`.pdf`,
   then call `app/reporting/editorial_pdf_service.py::generate_editorial_pdf(analysis_id, db)`
   directly (or `POST /api/fundamental/analyses/{analysis_id}/generate-report`
   if a server is running) — it rebuilds the HTML export from current DB
   state (picking up the new `ai_analysis`) and re-renders via Playwright.
7. Copy the resulting PDF out of `backend/reports/` to wherever it needs to
   be reviewed/shared.

This does not touch any of the *other* pipeline stages — P&L/balance-sheet/
cash-flow intelligence, scores, risk flags, etc. are all still the real
computed output; only the narrative `ai_analysis` JSON is hand-replaced.

## 5. Known limitations/gotchas (documented in code comments)

- **Annual-report "LLM-fallback guard"** (`annual_report_ingestion.py`): if
  `default_llm_client.last_used_fallback` is `True` after `extract_area()`,
  the extraction is discarded entirely rather than persisted. Motivated by a
  reproduced bug on Pidilite Industries: a Groq-429-triggered Ollama fallback
  silently transposed digits (`12349.33` instead of `12539.33`), no error
  raised. Covered by `tests/test_annual_report_llm_fallback_guard.py`.
- **`ppe` extraction area built but never wired to storage** — live testing
  found it silently returns wrong-year figures often enough not to trust; a
  more dangerous failure mode than a null value. Do not wire it without a
  validated fix.
- **`blueprint_validator.py`** — numeric-grounding checker for every LLM
  blueprint section: extracts every numeric token from generated text and
  confirms it traces back to a real value in the Master Company Object
  (0.05 absolute / 0.5% relative tolerance). A section that fails grounding
  is dropped, never rewritten. ISO dates (`2023-03-31`) used to be misparsed
  as three negative numbers via the minus/hyphen ambiguity — dates are now
  stripped before number-scanning.
- **`pnl_earnings_quality` section skipped outright for banks/NBFCs** — not
  just prompted differently. `llama3.2:3b` fabricated a "WEAK interest
  coverage" verdict and a flagged 65.71% ratio for HDFC Bank twice
  independently, even when the supplied data correctly showed those fields
  as null/false. The numeric validator couldn't catch it because 65.71 was
  itself a real grounded number — the hallucinated *words* weren't. Prompt
  rewording didn't fix it either; the section is conceptually gated off for
  financial-sector companies.
- **Groq's `gpt-oss-20b` account-level 8000 TPM cap** — the exact number
  appears verbatim in comments across `annual_report_locator.py`,
  `guidance_extraction.py`, `banking_ingestion.py`, `annual_report_ingestion.py`
  (never as a config constant — see §2). Groq reserves the FULL *requested*
  `max_tokens` against the TPM budget upfront, not just tokens actually
  generated, so the naive default `llm_max_tokens=4096` pushed most calls
  over budget on their own. `gpt-oss-20b` also spends real "reasoning"
  tokens even in JSON mode (~600 reasoning + ~140 JSON on one measured
  3308-prompt-token call) — going much below ~1500 truncates the reasoning
  pass and causes an opaque empty-body HTTP 400. Settled values: most
  extraction call sites use `max_tokens=3000`; input text is capped per call
  site (`8000` chars default, `16000` for earnings-call transcripts, with a
  per-area override dict in `annual_report_ingestion.py` raising specific
  areas to 10000-13000 chars after live truncation bugs silently sliced a
  target table/sentence out of the selected text window entirely).

## 6. Historical note — a removed Ollama-backed RAG system

An earlier pgvector-backed embeddings/RAG pipeline
(`app/ingestion/embeddings/`, since deleted) used Ollama-served
`qwen3-embedding` as a *primary* retrieval path. It was torn down completely
per explicit user instruction because Ollama-availability-dependent indexing
stalled a live HDFC Bank analysis on the `sector_analysis` stage for 5+
minutes. Documented in the repo-root `IMPLEMENTATION_PLAN.md`. Today's
Ollama usage — the chat fallback in `app/llm/client.py` and the newer,
narrower `app/interpretation/embeddings.py` (Concall Stage C2 only) — is a
separate, later, deliberately smaller-scope reintroduction. Don't confuse
the two if `IMPLEMENTATION_PLAN.md` comes up in a future search.
