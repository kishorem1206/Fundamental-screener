# backend/Makefile — Beginner Explanation

> **Source file:** `backend/Makefile`

---

## 1. What is this file?

A Makefile is a Unix tool that defines short command aliases called **targets**. Instead of typing a long command like `PYTHONPATH=. .venv/bin/python3.12 -m uvicorn app.main:app ...`, you type `make dev`.

Equivalent to the TypeScript project's `pnpm run dev`, `pnpm run seed` etc. from `package.json`.

---

## 2. The commands

### `make dev` — Start the server

```makefile
dev:
    PYTHONPATH=. .venv/bin/python3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Starts the FastAPI development server with auto-reload on file changes.

**`PYTHONPATH=.`** — Tells Python to treat the current directory (`backend/`) as the root for imports. Without it, `from app.config import config` would fail because Python wouldn't know where `app` is.

**`.venv/bin/python3.12`** — Uses the Python interpreter inside the virtual environment (with all our packages installed), not any system-wide Python.

**`-m uvicorn`** — Runs the uvicorn module as a script. Equivalent to running the `uvicorn` command.

**`app.main:app`** — Load the file `backend/app/main.py`, find the variable named `app` inside it (our FastAPI instance).

**`--reload`** — Restarts the server automatically when you save any Python file.

---

### `make seed` — Load stock data

```makefile
seed:
    PYTHONPATH=. .venv/bin/python3.12 scripts/seed_stocks.py
```

Runs the seed script to insert Nifty 50 stocks into the database. Safe to run multiple times — it's get-or-create (won't duplicate data).

---

### `make migrate` — Apply database migrations

```makefile
migrate:
    PYTHONPATH=. .venv/bin/python3.12 -m alembic upgrade head
```

Runs all pending Alembic migrations to bring the database schema up to date. **"head"** means the latest migration.

Run this when you first set up the project, or after someone adds a new migration.

---

### `make generate name="..."` — Create a new migration

```makefile
generate:
    PYTHONPATH=. .venv/bin/python3.12 -m alembic revision --autogenerate -m "$(name)"
```

Usage: `make generate name="add_pe_ratio_to_stocks"`

Alembic compares your SQLAlchemy models to the current database state and **auto-generates** the SQL needed to make them match. Creates a new file in `alembic/versions/`.

---

### `make downgrade` — Undo last migration

```makefile
downgrade:
    PYTHONPATH=. .venv/bin/python3.12 -m alembic downgrade -1
```

Rolls back the most recent migration. `-1` means "one step back".

---

## 3. Typical first-time setup

```bash
cd backend/
make migrate   # Create all tables in the database
make seed      # Load 50 Nifty stocks
make dev       # Start the server
```

---

## 4. How Make works

A Makefile target looks like:
```
target-name:
    shell command
```

The **indentation must be a TAB** (not spaces). If you get `missing separator` errors, that's why.

**`.PHONY`** at the top tells Make that these are command names, not files. Without `.PHONY`, Make would check if a file named `dev` or `seed` exists and skip the command if it finds one.
