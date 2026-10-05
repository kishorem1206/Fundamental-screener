# backend/scripts/seed_stocks.py — Beginner Explanation

> **Source file:** `backend/scripts/seed_stocks.py`

---

## 1. What is this file?

A standalone Python script that loads Nifty 50 stock data from a JSON file into the database. It's the first thing you run after `make migrate`.

Run with: `make seed` (or `PYTHONPATH=. .venv/bin/python3.12 scripts/seed_stocks.py`)

---

## 2. Why a separate script?

This is a **one-time setup script**, not part of the web server. Unlike route handlers, it:
- Runs directly from the command line, not via HTTP
- Needs to load `.env` explicitly (no middleware to do it)
- Needs to set up `sys.path` manually (no uvicorn to configure it)

---

## 3. Line-by-line explanation

### `sys.path` setup

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
```

**`Path(__file__).parent.parent`** — `__file__` is the script's own path (`backend/scripts/seed_stocks.py`). `.parent` is `backend/scripts/`. `.parent` again is `backend/`. So this resolves to `backend/`.

**`sys.path.insert(0, ...)`** — Prepends `backend/` to Python's module search path. Now `from app.config import config` resolves correctly (Python finds `backend/app/config.py`).

This is equivalent to setting `PYTHONPATH=.` from the command line — the Makefile does it via the environment variable; the script does it in code for robustness.

---

### Loading the `.env` file

```python
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
```

**`load_dotenv()`** — Explicitly loads the `.env` file before importing `app.config`. This is necessary because scripts run outside uvicorn — there's no `pydantic-settings` auto-loading triggered until `config = Settings()` runs, and that needs the env vars already set.

**Why the explicit path?** — When running scripts, the working directory might not be `backend/`. The explicit path ensures `.env` is found regardless of where `python scripts/seed_stocks.py` is invoked from.

---

### Importing app modules (after path setup)

```python
from app.services.stock_seed_loader import stock_seed_loader
from app.logger import logger
```

These imports happen **after** `sys.path.insert` and `load_dotenv()`. Order matters: if you import `app.config` before `load_dotenv()`, `Settings()` runs without the env vars loaded and uses default values (wrong database URL, missing API keys, etc.).

---

### Finding the seed file

```python
SEED_FILE = Path(__file__).parent.parent.parent / "scripts" / "seeds" / "nifty50.json"
```

**Path breakdown**:
- `__file__` → `backend/scripts/seed_stocks.py`
- `.parent` → `backend/scripts/`
- `.parent` → `backend/`
- `.parent` → project root `/`
- `/ "scripts" / "seeds" / "nifty50.json"` → `scripts/seeds/nifty50.json` (at project root)

The seed data lives in the root `scripts/seeds/` directory, not `backend/scripts/`, to keep it accessible regardless of stack (it could be used by other tools).

---

### Running the seed

```python
def main() -> None:
    logger.info("Starting stock seed", seed_file=str(SEED_FILE))
    if not SEED_FILE.exists():
        logger.error("Seed file not found", path=str(SEED_FILE))
        sys.exit(1)
    stock_seed_loader.load_from_file(str(SEED_FILE))
    logger.info("Stock seed completed successfully")

if __name__ == "__main__":
    main()
```

**`if __name__ == "__main__":`** — Python runs this block only when the script is executed directly (`python seed_stocks.py`), not when it's imported as a module. Standard Python idiom for scripts.

**`sys.exit(1)`** — Exits with error code 1 (failure). Useful for shell scripts that check exit codes: `make seed && echo "success" || echo "failed"`.
