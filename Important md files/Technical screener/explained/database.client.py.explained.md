# backend/app/infrastructure/database/client.py — Beginner Explanation

> **Source file:** `backend/app/infrastructure/database/client.py`

---

## 1. What is this file?

Manages the database connection: creates the SQLAlchemy engine (connection pool), provides sessions for queries, and exposes health check + cleanup functions.

Equivalent to TypeScript's database client that managed the pg connection pool.

---

## 2. SQLAlchemy engine vs session

| Concept | Analogy | SQLAlchemy object |
|---------|---------|-------------------|
| Connection pool | A pool of phone lines to the DB | `Engine` |
| One connection checkout | Picking up a phone line | `Session` |
| A query | A phone call | `session.query(...)` or `session.execute(...)` |
| Commit | Finalizing what you said | `session.commit()` |
| Rollback | Hanging up without sending | `session.rollback()` |

---

## 3. Line-by-line explanation

### Lazy singleton engine

```python
_engine: Engine | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.database_url,
            pool_size=config.database_pool_min,
            max_overflow=config.database_pool_max - config.database_pool_min,
            pool_pre_ping=True,
        )
    return _engine
```

**`global _engine`** — Declares that `_engine` refers to the module-level variable, not a local one.

**Lazy initialization** — The engine is only created when `get_engine()` is first called. If no database queries are made, no connection is opened.

**`pool_pre_ping=True`** — Before using a connection from the pool, SQLAlchemy sends a lightweight ping (`SELECT 1`). If the connection is stale (e.g., PostgreSQL restarted), it's discarded and a new one is created. Prevents `connection is closed` errors.

**`pool_size`** — Minimum connections always kept alive. From `.env`: `DATABASE_POOL_MIN=2`.

**`max_overflow`** — Extra connections allowed above `pool_size` during spikes. We calculate it as `max - min`.

---

### Session factory

```python
_session_factory: sessionmaker | None = None

def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory
```

**`sessionmaker`** — A factory that creates `Session` objects on demand. Think of it as a Session class with pre-configured settings.

**`expire_on_commit=False`** — By default, SQLAlchemy expires all object attributes after `commit()`, forcing a fresh DB read on next access. Setting this to False means we can still read `stock.symbol` after committing without another query. Better for our service layer which returns dataclasses.

---

### `get_db()`

```python
def get_db() -> Session:
    factory = get_session_factory()
    return factory()
```

Creates a new `Session` (checks out a connection from the pool). Each service method calls this, then closes the session in a `try/finally`.

---

### Health check

```python
def check_database_health() -> bool:
    try:
        db = get_db()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False
```

Used by the `/health` endpoint to verify the database is reachable.

---

### Cleanup

```python
def close_database() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
```

Called on shutdown (from `lifespan` in `main.py`). `dispose()` closes all connections in the pool and the engine itself. Without this, PostgreSQL shows active connections even after the server exits.

---

## 4. Usage pattern in services

```python
def list_universes() -> list[UniverseRow]:
    db = get_db()
    try:
        rows = db.query(Universe).all()
        return [UniverseRow(...) for r in rows]
    finally:
        db.close()  # Always release the connection back to the pool
```

The `finally` block guarantees `db.close()` runs even if an exception is thrown. Without it, connections would leak and the pool would eventually be exhausted.
