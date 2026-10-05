# .env.example — Beginner Explanation

> **Source file:** `.env.example`

---

## 1. What is this file?

This file is a **template** for the `.env` file — a file that contains secret configuration values (passwords, API keys, URLs) that the backend server reads at startup.

The `.env.example` file itself is **safe to commit to git** because it contains no real secrets — just example values with descriptive comments. The real `.env` file (which has your actual passwords and keys) is listed in `.gitignore` and must NEVER be committed.

---

## 2. Why does this file exist?

**Problem:** The backend needs to know things like:
- What port to run on
- How to connect to the database
- What AI API key to use

These values differ between developers' computers and production servers. You can't hardcode them.

**Solution:** Environment variables. Each developer copies `.env.example` to `.env` and fills in their own values. The server reads from `.env` at startup.

**The template exists because:** When a new developer joins or you set up a new server, you need to know which variables are needed. The example file documents all required variables with comments explaining each one.

---

## 3. Where does it fit in the project?

```
.env.example ← THIS FILE (template, committed to git)
      ↓
Developer copies: cp .env.example .env
      ↓
Fills in real values in .env
      ↓
Node.js / tsx reads .env automatically
Populates process.env with key=value pairs
      ↓
backend/src/config.ts reads process.env
Exports typed config object
      ↓
All backend files use config.*
```

---

## 5. Line-by-line explanation

```
NODE_ENV=development
```

**`NODE_ENV`** — A convention used by almost every Node.js library to change behaviour based on environment. Common values:
- `development` — More verbose logging, pretty error messages, hot reloading
- `production` — Minimal logging, optimised performance, no debug output
- `test` — Test-specific behaviour (e.g., use a test database)

---

```
API_PORT=3001
API_HOST=0.0.0.0
```

**`API_PORT=3001`** — The port the backend HTTP server listens on. The frontend Vite dev server proxies `/api` requests to this port.

**`API_HOST=0.0.0.0`** — Listen on all network interfaces. `0.0.0.0` means "accept connections from any network address" (including Docker containers, other computers on the same network). `127.0.0.1` would restrict to only connections from the same computer.

---

```
DATABASE_URL=postgresql://screener:screener@localhost:5433/screener
```

**`DATABASE_URL`** — The PostgreSQL connection string. Format: `postgresql://username:password@host:port/database`

Breaking it down:
- `screener` (username) — The PostgreSQL user created by Docker
- `screener` (password) — The password for that user
- `localhost` — PostgreSQL is on the same machine
- `5433` — Port 5433 (not the default 5432) because Docker's PostgreSQL is mapped to 5433 to avoid conflict with a local Homebrew PostgreSQL
- `screener` (database name) — The database created by Docker

**This is the only required variable.** `config.ts` has a fallback for everything else but DATABASE_URL must be set.

---

```
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10
```

**`DATABASE_POOL_MIN=2`** — Keep at least 2 connections open to PostgreSQL. Prevents the "cold start" delay when the first request hits.

**`DATABASE_POOL_MAX=10`** — Never open more than 10 simultaneous connections. PostgreSQL has a default connection limit (usually 100). Keeping this modest leaves room for other clients (e.g., drizzle-kit, pgAdmin).

---

```
REDIS_URL=redis://localhost:6379
REDIS_KEY_PREFIX=screener:
```

**`REDIS_URL=redis://localhost:6379`** — Connection to Redis. Standard Redis on default port 6379 (Docker Redis is mapped 1:1 here — no conflict with local Redis since most Macs don't have Redis installed by default).

**`REDIS_KEY_PREFIX=screener:`** — All keys stored in Redis by this app are prefixed with `screener:`. For example, a key stored as `INFY:LTP` becomes `screener:INFY:LTP` in Redis. This prevents collisions if Redis is ever shared with other apps.

---

```
LLM_PROVIDER=gpt-oss
LLM_MODEL=
LLM_API_KEY=
LLM_API_BASE_URL=
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.1
```

**`LLM_PROVIDER=gpt-oss`** — Which AI provider to use. Options: `gpt-oss` (OpenAI-compatible), `claude` (Anthropic), `openai` (official OpenAI).

**`LLM_MODEL=`** — Intentionally left empty. When empty, `GPTOSSProvider` defaults to `gpt-4o-mini`. Set to `gpt-4o` for more capable but expensive AI.

**`LLM_API_KEY=`** — Your OpenAI/Anthropic API key. **This is the secret you must fill in.** Never commit a real API key. The health check shows `not_configured` until this is set.

**`LLM_API_BASE_URL=`** — Intentionally empty. When empty, defaults to OpenAI's official API. Override to use:
- A self-hosted model: `http://localhost:11434/v1` (Ollama)
- A company proxy: `https://my-openai-proxy.example.com/v1`
- Any OpenAI-compatible endpoint

**`LLM_MAX_TOKENS=4096`** and **`LLM_TEMPERATURE=0.1`** — Used by `GPTOSSProvider` as defaults. Temperature 0.1 = very deterministic AI responses (good for a screener that needs consistent, predictable output).

---

```
LOG_LEVEL=info
LOG_PRETTY=true
```

**`LOG_LEVEL=info`** — Minimum log level to show. Levels (quietest to loudest): `trace → debug → info → warn → error → fatal`. With `info`, debug messages are hidden (too verbose for normal use). Change to `debug` to see detailed request traces.

**`LOG_PRETTY=true`** — Enable human-readable formatted logs in the terminal (colours, readable timestamps). In production, set to `false` for JSON logs that log aggregation tools (like Datadog, Splunk) can parse.

---

```
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**`CORS_ORIGINS`** — Comma-separated list of frontend URLs allowed to make requests to the backend.

- `http://localhost:5173` — Vite dev server (frontend)
- `http://localhost:3000` — Alternative port sometimes used for preview

If the frontend URL isn't in this list, the browser blocks API requests with a CORS error. In production, this would be your actual domain: `https://yourapp.example.com`.

---

## 6. How to use this file

```bash
# 1. Copy the template to create your actual .env file
cp .env.example .env

# 2. Edit .env with your real values
# At minimum, set LLM_API_KEY if you want AI features

# 3. Start Docker services
pnpm docker:up

# 4. Start the development servers
pnpm dev
```

---

## 7. What is in .gitignore regarding .env?

The actual `.env` file should be in `.gitignore`. This prevents it from ever being committed to git:

```
.env
.env.local
.env.*.local
```

The `.env.example` file is committed. The real `.env` file is not.

---

## 8. What happens if I change or remove something?

| Change | Consequence |
|--------|-------------|
| Leave `DATABASE_URL` empty | Backend fails to start; `config.ts` uses fallback URL |
| Change port to 5432 in DATABASE_URL | Connects to local Homebrew PostgreSQL instead of Docker; wrong database |
| Set `LLM_API_KEY=sk-real-key-here` | LLM health changes from `not_configured` to `ok`; AI features work |
| Set `LOG_LEVEL=debug` | Very verbose output; every HTTP request, every query |
| Set `LOG_PRETTY=false` | JSON output; harder to read manually but better for log tools |
| Add a domain to `CORS_ORIGINS` | Frontend at that domain can now call the backend |

---

## 9. Beginner concepts to learn

- **What are environment variables?** — Key=value pairs that programs read from the OS at startup; keep secrets out of code
- **What is `.env`?** — A file of environment variables loaded by Node.js tools automatically
- **What is `.gitignore`?** — A file listing paths that git should never track (secrets, build output)
- **What is a connection string?** — A URL-like format encoding all database connection info in one string
- **What is CORS?** — Browser security restricting cross-origin (cross-port/domain) requests

---

## 10. Simple mental model

Think of `.env.example` as a **hotel room inventory checklist template**:

- Every room (development environment) needs the same set of items (variables)
- The checklist (`.env.example`) shows what items are needed with notes on each
- Each room has different specific items (your API key, their API key)
- The filled-in checklist for each room (`.env`) is confidential — not shared

A new housekeeper (developer) gets the blank template, fills it in for their specific room (environment), and keeps their filled copy private. They don't share their API keys on the public template.
