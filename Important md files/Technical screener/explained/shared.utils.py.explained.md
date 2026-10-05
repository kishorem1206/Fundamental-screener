# backend/app/shared/utils.py — Beginner Explanation

> **Source file:** `backend/app/shared/utils.py`

---

## 1. What is this file?

Small utility functions used across the backend: ID generation, timestamps, cache key building, and chunking lists.

Equivalent to TypeScript's `utils.ts`.

---

## 2. The utilities

### `generate_id()`

```python
def generate_id() -> str:
    return str(uuid.uuid4())
```

Generates a random UUID like `"a3f8b2c1-4d5e-6789-abcd-ef0123456789"`. Used to assign unique IDs to agent tasks.

**`uuid.uuid4()`** — UUID version 4: entirely random. No dependency on timestamp or machine ID. Virtually guaranteed to be unique (2^122 possible values).

---

### `now_iso()`

```python
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
```

Returns the current UTC time in ISO 8601 format: `"2026-08-22T10:30:00.123456Z"`.

**`+ "Z"`** — Appends the UTC timezone indicator. `datetime.utcnow()` returns a naive datetime (no timezone info), so we append `"Z"` (UTC) manually. A frontend seeing this string knows it's in UTC.

Used for `created_at` timestamps in `AgentTask`.

---

### `today_date()`

```python
def today_date() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")
```

Returns today's date as `"2026-08-22"`. Used for cache keys that include the date (so cached data is invalidated at midnight).

---

### `build_cache_key()`

```python
def build_cache_key(*parts: str) -> str:
    return ":".join(part.lower() for part in parts if part)
```

Builds a Redis cache key from multiple parts:
```python
build_cache_key("stocks", "NSE", "INFY")
# → "stocks:nse:infy"

build_cache_key("universes", "nifty50", "members")
# → "universes:nifty50:members"
```

**`*parts: str`** — Accepts any number of string arguments. The `*` means "collect all positional args into a tuple".

**`if part`** — Skips empty strings (prevents `"stocks::nse"` from a `None` filter).

**`.lower()`** — Normalizes to lowercase so `"NSE"` and `"nse"` hit the same cache key.

---

### `chunk()`

```python
def chunk(lst: list, size: int) -> list[list]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]
```

Splits a list into smaller lists of the given size:
```python
chunk([1, 2, 3, 4, 5], 2)
# → [[1, 2], [3, 4], [5]]
```

Used when processing large batches — e.g., fetching market data for 50 stocks by calling the API 10 stocks at a time.

**`range(0, len(lst), size)`** — Generates indices `0, size, 2*size, ...` up to the list length.

**`lst[i:i + size]`** — Python slice notation: take elements from index `i` to `i + size` (exclusive).

---

### `p_limit()` — concurrency limiter

```python
async def p_limit(n: int, fns: list) -> list:
    semaphore = asyncio.Semaphore(n)

    async def run(fn):
        async with semaphore:
            return await fn()

    return await asyncio.gather(*[run(fn) for fn in fns])
```

Runs multiple async tasks concurrently, but limits to `n` at a time.

```python
# Run 10 API calls concurrently (max 3 at once):
results = await p_limit(3, [
    lambda: fetch_quote("INFY"),
    lambda: fetch_quote("TCS"),
    lambda: fetch_quote("HDFC"),
    # ... 7 more
])
```

**`asyncio.Semaphore(n)`** — A counter-based lock. Only `n` coroutines can hold it at once; others wait.

**`async with semaphore:`** — Acquires the semaphore (decrements counter), runs the task, releases it (increments counter). If `n` coroutines are already running, `await` waits here until one finishes.

**`asyncio.gather(*...)`** — Runs all tasks concurrently and collects results in order.

Equivalent to TypeScript's `pLimit()` from the `p-limit` npm package.
