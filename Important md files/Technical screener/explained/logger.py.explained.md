# backend/app/logger.py — Beginner Explanation

> **Source file:** `backend/app/logger.py`

---

## 1. What is this file?

This file sets up **structlog** — a structured logging library. It configures how log messages are formatted and creates the `logger` object that all other modules import and use.

Equivalent to the TypeScript `logger.ts` which configured Pino.

---

## 2. What is structured logging?

Regular logging: `print("Server started on port 3001")`

Structured logging: `logger.info("Server started", port=3001, env="development")`

Structured logging outputs **JSON in production** so log aggregation tools (Datadog, CloudWatch, Grafana Loki) can filter and query by field:

```json
{"level": "info", "event": "Server started", "port": 3001, "env": "development", "timestamp": "2026-08-22T10:00:00Z"}
```

---

## 3. Line-by-line explanation

```python
def _configure_logging() -> None:
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
```

**`getattr(logging, "DEBUG", logging.INFO)`** — Converts the string `"DEBUG"` from `.env` into the actual `logging.DEBUG` constant (integer 10). If the string is invalid, defaults to `logging.INFO`.

---

```python
    if config.log_pretty and config.node_env != "production":
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
```

**Development mode (pretty output):**
- `merge_contextvars` — merges any context set via `structlog.contextvars.bind_contextvars()` into each log event (e.g., correlation IDs)
- `add_log_level` — adds `"level": "info"` to each log event
- `ConsoleRenderer(colors=True)` — renders as colored human-readable text: `2026-08-22 INFO  Server started port=3001`

---

```python
    else:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
```

**Production mode (JSON output):**
- `TimeStamper(fmt="iso")` — adds ISO 8601 timestamp to each event
- `JSONRenderer()` — renders as one-line JSON

---

```python
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**`wrapper_class=make_filtering_bound_logger(log_level)`** — Creates a logger class that filters out messages below the configured level. If `log_level=INFO`, then `logger.debug(...)` calls are silently ignored.

**`logger_factory=PrintLoggerFactory()`** — Uses Python's `print()` to write logs (vs stdlib logging). Simpler, no buffering issues.

**`cache_logger_on_first_use=True`** — Performance optimization: structlog builds the processor chain once and reuses it.

---

```python
_configure_logging()

logger = structlog.get_logger("stock-screener")
```

**`_configure_logging()` at module level** — Runs once when this module is first imported by any file. This guarantees logging is configured before any log call.

**`logger`** — The module-level logger that all files import:
```python
from app.logger import logger
logger.info("Health check", status="ok")
```

---

## 4. Known issue avoided: `add_logger_name`

structlog's `structlog.stdlib.add_logger_name` processor requires a stdlib `logging.Logger` with a `.name` attribute. Since we use `PrintLoggerFactory` (which creates a `PrintLogger` without `.name`), adding `add_logger_name` would crash with `AttributeError: 'PrintLogger' object has no attribute 'name'`.

That's why `add_logger_name` is intentionally **not** in our processor list.
