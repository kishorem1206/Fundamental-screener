# backend/pyproject.toml — Beginner Explanation

> **Source file:** `backend/pyproject.toml`

---

## 1. What is this file?

`pyproject.toml` is Python's modern project configuration file — the equivalent of `package.json` in Node.js. It defines the project name, Python version requirement, and all dependencies.

---

## 2. `pyproject.toml` vs `package.json`

| Node.js (`package.json`) | Python (`pyproject.toml`) |
|--------------------------|--------------------------|
| `"name": "backend"` | `name = "stock-screener-backend"` |
| `"dependencies": {...}` | `[project] dependencies = [...]` |
| `"devDependencies": {...}` | `[project.optional-dependencies] dev = [...]` |
| `npm install` | `uv pip install -r requirements.txt` |
| `pnpm` / `npm` | `uv` (our package manager) |

---

## 3. Key sections

### `[project]`

```toml
[project]
name = "stock-screener-backend"
version = "0.1.0"
requires-python = ">=3.12"
```

**`requires-python = ">=3.12"`** — This project needs Python 3.12 or newer. We use 3.12 because it has the best support for `Mapped[T | None]` style union syntax.

---

### `dependencies`

```toml
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "alembic>=1.14",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "redis>=5.2",
    "structlog>=24.4",
    "httpx>=0.28",
    "python-dotenv>=1.0",
]
```

| Package | Purpose | TypeScript equivalent |
|---------|---------|----------------------|
| `fastapi` | Web framework | Fastify |
| `uvicorn[standard]` | ASGI server (runs FastAPI) | Node.js built-in HTTP |
| `sqlalchemy` | ORM | Drizzle ORM |
| `psycopg2-binary` | PostgreSQL driver | pg (postgres-js) |
| `alembic` | Database migrations | drizzle-kit |
| `pydantic` | Data validation | Zod |
| `pydantic-settings` | Config from `.env` | Zod + dotenv |
| `redis` | Redis client | ioredis |
| `structlog` | Structured logging | Pino |
| `httpx` | HTTP client | fetch() |
| `python-dotenv` | `.env` loader in scripts | dotenv (manual) |

**`[standard]` in `uvicorn[standard]`** — Installs uvicorn with optional performance extras (websockets support, faster HTTP parsing). The brackets are Python's "extras" syntax.

---

## 4. Virtual environment

Packages are installed into `backend/.venv/` (our virtual environment), not system-wide Python. This prevents conflicts between projects.

```bash
# Create virtual environment
python3.12 -m venv .venv

# Install packages (using uv for speed)
uv pip install --python .venv/bin/python3.12 \
    fastapi "uvicorn[standard]>=0.32" sqlalchemy ...
```

Once installed, use `.venv/bin/python3.12` to run any script with these packages available.

---

## 5. `[tool.ruff]` — linter config

```toml
[tool.ruff]
line-length = 100
target-version = "py312"
```

Ruff is a fast Python linter (like ESLint for JavaScript). `line-length = 100` means lines up to 100 characters are allowed.
