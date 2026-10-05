# backend/app/infrastructure/redis/client.py — Beginner Explanation

> **Source file:** `backend/app/infrastructure/redis/client.py`

---

## 1. What is this file?

Provides helper functions for reading and writing data to Redis — an in-memory key-value store used as a cache. Values stored here are accessed in microseconds vs milliseconds for PostgreSQL.

Equivalent to TypeScript's Redis client (using ioredis).

---

## 2. Why Redis?

When a route like `/stocks` is called repeatedly with the same filters, we'd be running the same SQL query over and over. Redis lets us cache the result after the first query and return it instantly for subsequent identical requests.

```
First request → SQL query → store in Redis with TTL → return result
Next requests → read from Redis → return result (no SQL)
After TTL expires → SQL query again → refresh Redis
```

---

## 3. Line-by-line explanation

### Creating the client

```python
_redis: redis.Redis | None = None

def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            config.redis_url,
            decode_responses=True,
        )
    return _redis
```

**`redis.from_url()`** — Creates a Redis client from a connection string like `redis://localhost:6379`. Parses host, port, database, and password from the URL.

**`decode_responses=True`** — Redis natively stores bytes. This flag makes the client automatically decode bytes to Python strings on reads. Without it, you'd get `b"value"` (bytes) instead of `"value"` (string).

---

### Key prefixing

```python
def _key(k: str) -> str:
    return f"{config.redis_key_prefix}{k}"
```

All our Redis keys are prefixed with `screener:` (from config). So `cache_get("universes")` actually reads the Redis key `screener:universes`.

**Why prefix?** — Redis is often shared between multiple services (or environments). Prefixing prevents key collisions. If a future service also stores `"universes"` in Redis, they don't overwrite each other.

---

### `cache_get`

```python
def cache_get(key: str) -> str | None:
    try:
        return get_redis().get(_key(key))
    except Exception:
        return None
```

Returns the cached string value, or `None` if the key doesn't exist or Redis is unavailable.

**`try/except`** — If Redis is down, we return `None` (cache miss). The calling code then falls back to the database. The app degrades gracefully without crashing.

---

### `cache_set`

```python
def cache_set(key: str, value: str, ttl_seconds: int = 300) -> None:
    try:
        get_redis().setex(_key(key), ttl_seconds, value)
    except Exception:
        pass
```

**`setex`** — "SET with EXpiry". Stores the value and schedules automatic deletion after `ttl_seconds`. Default TTL is 300 seconds (5 minutes).

**Storing JSON**: The caller is responsible for serializing to JSON before calling `cache_set` and deserializing after `cache_get`. This keeps the Redis client simple.

---

### `cache_del`

```python
def cache_del(key: str) -> None:
    try:
        get_redis().delete(_key(key))
    except Exception:
        pass
```

Deletes a key immediately. Used to invalidate cache when data changes.

---

### Health check

```python
def check_redis_health() -> bool:
    try:
        get_redis().ping()
        return True
    except Exception:
        return False
```

**`ping()`** — Redis responds with `"PONG"`. If it fails (Redis down, connection refused), `ping()` raises an exception and we return `False`.

Used by the `/health` endpoint.

---

## 4. Usage pattern (not yet in Phase 1 routes, but designed for it)

```python
cached = cache_get("universes:all")
if cached:
    return json.loads(cached)

result = classification_service.list_universes()
cache_set("universes:all", json.dumps([asdict(r) for r in result]))
return result
```
