# backend/app/config.py — Beginner Explanation

> **Source file:** `backend/app/config.py`

---

## 1. What is this file?

This file defines the `Settings` class — a Pydantic-based config object that reads all environment variables from the `.env` file and exposes them as typed Python attributes.

Equivalent to the TypeScript `config.ts` which used Zod to validate `process.env`.

---

## 2. Why use `pydantic-settings`?

| TypeScript (was) | Python (now) |
|-----------------|--------------|
| `import "dotenv/config"` | Built into `pydantic-settings` |
| `z.string().default("...")` | `field: str = "..."` |
| `z.coerce.number()` | `field: int = ...` (auto-coerced) |
| `EnvSchema.parse(process.env)` | `Settings()` |

**`pydantic-settings`** reads the `.env` file automatically when `env_file=".env"` is in `model_config`. No need to call `load_dotenv()` separately.

---

## 5. Line-by-line explanation

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
```

**`BaseSettings`** — A Pydantic base class specifically for config. It reads from environment variables and `.env` files automatically.

**`env_file=".env"`** — Loads `backend/.env` (a symlink to the root `.env`). Python reads it when `Settings()` is instantiated.

**`case_sensitive=False`** — Allows `DATABASE_URL` in `.env` to match `database_url: str` in the class. Without this, the names must match exactly.

**`extra="ignore"`** — If `.env` has variables not in `Settings`, just ignore them (don't throw an error).

---

```python
    database_url: str = "postgresql://screener:screener@localhost:5433/screener"
    database_pool_min: int = 2
    database_pool_max: int = 10
```

**Type annotations as validation**: `database_url: str` means the value must be a string. `database_pool_min: int = 2` means: read `DATABASE_POOL_MIN` from env, convert to int, default to 2 if missing.

Pydantic automatically coerces `"2"` (a string from .env) to `2` (an integer). No need for `z.coerce.number()`.

---

```python
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]
```

**`@property`** — A computed value that runs as a method but is accessed like an attribute (`config.cors_origins_list`). The `.env` stores `CORS_ORIGINS=http://localhost:5173,http://localhost:3000` as a string; this property splits it into a Python list.

---

```python
config = Settings()
```

Creates one instance at module load time. All other modules import this single `config` object.

---

## 6. How `.env` values map to config

```
# .env file              → config attribute
DATABASE_URL=...         → config.database_url
DATABASE_POOL_MIN=2      → config.database_pool_min (int)
API_PORT=3001            → config.api_port (int)
LOG_PRETTY=true          → config.log_pretty (bool)
```

Pydantic handles all the type conversions automatically.

---

## 7. Simple mental model

`Settings` is like a **typed form** for your environment variables. Instead of reading `os.environ["DATABASE_URL"]` everywhere (which returns `None` with no warning if missing), you define the fields once and get:
- Type checking
- Default values
- Automatic `.env` loading
- A single `config` object accessible everywhere
