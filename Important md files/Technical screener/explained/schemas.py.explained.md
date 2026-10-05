# backend/app/shared/schemas.py — Beginner Explanation

> **Source file:** `backend/app/shared/schemas.py`

---

## 1. What is this file?

Defines **Pydantic models** for the data structures that agents and the LLM system pass around: `AgentTask`, `AgentResult`, `AgentError`, `DataProvenance`, and DSL (Domain-Specific Language) expression types.

Equivalent to TypeScript's `schemas.ts` which used Zod schemas.

---

## 2. Pydantic vs Zod

| Zod (was) | Pydantic v2 (now) |
|-----------|-------------------|
| `z.object({...})` | `class MyModel(BaseModel):` |
| `z.string()` | `field: str` |
| `z.string().optional()` | `field: str \| None = None` |
| `z.literal("HIGH", "NORMAL", "LOW")` | `Literal["HIGH", "NORMAL", "LOW"]` |
| `z.string().default(uuid)` | `Field(default_factory=lambda: str(uuid.uuid4()))` |
| `.parse(data)` | `MyModel(**data)` or `MyModel.model_validate(data)` |

---

## 3. `AgentTask`

```python
class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str
    parent_task_id: str | None = None
    from_agent: str
    to_agent: str
    task_type: str
    payload: Any = None
    priority: Literal["HIGH", "NORMAL", "LOW"] = "NORMAL"
    created_at: str
    deadline: str | None = None
```

An `AgentTask` is the message one agent sends to another through the message bus. Think of it as an envelope: `from_agent` is the sender, `to_agent` is the recipient, `task_type` is the subject, `payload` is the content.

**`Field(default_factory=...)`** — `default_factory` is called each time an instance is created (not once at class load time). This ensures each task gets a unique UUID.

**`str | None = None`** — Python 3.10+ union type. Means the field can be a string OR None, and defaults to None if omitted.

**`Literal["HIGH", "NORMAL", "LOW"]`** — The value must be exactly one of these three strings. Pydantic raises a validation error if you pass anything else.

---

## 4. `AgentResult`

```python
class AgentResult(BaseModel):
    task_id: str
    correlation_id: str
    agent: str
    status: Literal["SUCCESS", "PARTIAL", "FAILED", "UNKNOWN"]
    data: Any
    errors: list[AgentError] = []
    warnings: list[str] = []
    provenance: list[DataProvenance] = []
    duration_ms: float | None = None
```

The response an agent sends back after handling a task.

**`errors: list[AgentError] = []`** — A list field with a default empty list. Pydantic creates a fresh list for each instance (not a shared reference).

**`data: Any`** — The actual result data. Type is `Any` because different agents return different shapes (a list of stocks, a universe, etc.).

---

## 5. DSL expressions

```python
class DSLAndExpression(BaseModel):
    and_: list["DSLExpression"] = Field(..., alias="and")

class DSLOrExpression(BaseModel):
    or_: list["DSLExpression"] = Field(..., alias="or")
```

**`alias="and"`** — `and` and `or` are Python keywords so they can't be Python attribute names. The alias tells Pydantic: when parsing JSON `{"and": [...]}`, store it in `self.and_`. When serializing, use `"and"` as the JSON key.

**`"DSLExpression"` (string forward reference)** — `DSLExpression` is a union type defined below that refers back to `DSLAndExpression`. Since Python sees the class before `DSLExpression` is defined, we use a string to defer evaluation.

---

## 6. `BaseModel` basics

```python
# Create from keyword args
task = AgentTask(
    correlation_id="abc-123",
    from_agent="route_handler",
    to_agent="universe_agent",
    task_type="LIST_UNIVERSES",
    created_at="2026-08-22T10:00:00Z",
)

# Create from dict (like JSON parsing)
task = AgentTask.model_validate(some_dict)

# Serialize to dict
task.model_dump()

# Serialize to JSON string
task.model_dump_json()
```

Pydantic validates all fields on creation and raises `ValidationError` (Pydantic's own, not ours) if any value is invalid.
