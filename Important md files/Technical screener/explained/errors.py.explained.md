# backend/app/shared/errors.py — Beginner Explanation

> **Source file:** `backend/app/shared/errors.py`

---

## 1. What is this file?

Defines the error class hierarchy for the application. All custom errors extend `AppError`, which carries a human-readable message, a machine-readable code, and an HTTP status code.

Equivalent to TypeScript's `errors.ts`.

---

## 2. The class hierarchy

```
Exception (Python built-in)
  └── AppError                   — base for all app errors (generic 500)
        ├── ValidationError      — 400 Bad Request
        ├── NotFoundError        — 404 Not Found
        ├── MCPUnavailableError  — 503 Service Unavailable
        ├── MCPBlockedError      — 403 Forbidden (V1 write block)
        ├── LLMNotConfiguredError— 503 Service Unavailable
        └── DataUnavailableError — 404 Not Found
```

---

## 3. Key concepts

### `AppError`

```python
class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
```

**`super().__init__(message)`** — Calls Python's built-in `Exception.__init__()` to set the error message. Without this, `str(error)` wouldn't show the message.

**`self.message`, `self.code`, `self.status_code`** — Extra fields beyond what Python's base `Exception` has. `code` is a machine-readable string (like `"NOT_FOUND"`) that frontends can switch on without parsing the message string.

---

### `NotFoundError`

```python
class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            status_code=404,
        )
```

Usage: `raise NotFoundError("Stock", "NSE:XYZ")`

Message produced: `"Stock not found: NSE:XYZ"`

The `__init__` signature is different from `AppError` — it takes `resource` and `identifier` and formats the message automatically. The caller doesn't need to know about the code or status.

---

### `MCPBlockedError`

```python
class MCPBlockedError(AppError):
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"Tool '{tool_name}' is blocked in V1 (read-only mode)",
            code="MCP_BLOCKED",
            status_code=403,
        )
```

V1 security constraint: write tools (like `place_order`) are blocked. This error is raised by the Kite MCP adapter when the agent tries to call a blocked tool.

---

## 4. How errors flow through the app

```
Route handler calls a service
    ↓
Service calls another function
    ↓
Function raises NotFoundError("Stock", "NSE:XYZ")
    ↓
Error propagates up (Python exception bubbling)
    ↓
FastAPI catches it via @app.exception_handler(AppError)
    ↓
Returns JSON: {"error": "NOT_FOUND", "message": "Stock not found: NSE:XYZ", ...}
with HTTP status 404
```

No `try/except` needed in routes — the global exception handler takes care of everything.

---

## 5. Python inheritance pattern

```python
class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400)
```

**`super().__init__(...)`** — Every subclass calls `super().__init__()` to initialize the parent class (`AppError`). This sets `self.message`, `self.code`, `self.status_code` on the instance.
