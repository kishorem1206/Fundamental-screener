# backend/app/agents/universe_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/universe_agent.py`

---

## 1. What is this file?

Defines `UniverseAgent` — the agent responsible for all universe-related tasks (`LIST_UNIVERSES`, `GET_UNIVERSE_STOCKS`). It receives an `AgentTask`, calls the classification service, and returns an `AgentResult`.

---

## 2. Agent role in the system

```
Universe Route
    ↓ builds AgentTask (task_type="LIST_UNIVERSES")
Message Bus
    ↓ finds UniverseAgent via registry
UniverseAgent.handle(task)
    ↓ calls ClassificationService.list_universes()
    ↓ wraps result in AgentResult
Route Handler
    ↓ returns JSON to browser
```

---

## 3. Line-by-line explanation

```python
class UniverseAgent:
    agent_id = "universe_agent"
```

**`agent_id`** — A class-level attribute (not instance-level). This is what `agent_registry.register(universe_agent)` uses as the key. It's also what route handlers put in `AgentTask(to_agent="universe_agent")`.

---

```python
    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "LIST_UNIVERSES":
            return self._list_universes(task)
        elif task.task_type == "GET_UNIVERSE_STOCKS":
            return self._get_universe_stocks(task)
        else:
            return self._failure(task, "UNKNOWN_TASK", f"Unknown task type: {task.task_type}")
```

**Dispatch by task type** — The agent is a handler for a specific set of task types. New task types can be added by adding an `elif` branch.

---

```python
    def _list_universes(self, task: AgentTask) -> AgentResult:
        try:
            universes = classification_service.list_universes()
            return self._success(task, [dataclasses.asdict(u) for u in universes])
        except Exception as e:
            logger.error("UniverseAgent: list_universes failed", error=str(e))
            return self._failure(task, "LIST_FAILED", str(e))
```

**`dataclasses.asdict(u)`** — Converts a `UniverseRow` dataclass to a plain Python dict. Necessary because `AgentResult.data` needs to be JSON-serializable, and raw dataclass instances are not.

---

### Helper methods

```python
    def _success(self, task: AgentTask, data: Any) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="SUCCESS",
            data=data,
        )

    def _failure(self, task: AgentTask, code: str, message: str) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="FAILED",
            data=None,
            errors=[AgentError(code=code, message=message)],
        )
```

These helpers reduce repetition. Every successful result has the same structure; every failure has the same structure. Without helpers, every `_list_*` method would repeat the same 7-line `AgentResult(...)` construction.

---

```python
universe_agent = UniverseAgent()
```

Module-level singleton, registered in `main.py` lifespan.

---

## 4. Why agents exist

Routes could call services directly:
```python
@router.get("/universes")
def get_universes():
    return classification_service.list_universes()
```

But the agent layer provides:
1. **Structured task tracking** — every operation has a `task_id`, `correlation_id`, `duration_ms`
2. **Consistent error wrapping** — all errors become `AgentResult(status="FAILED", errors=[...])`
3. **Ready for async** — when we add an LLM chat route, the LLM can dispatch tasks to agents using the same message bus, even from a different context

For Phase 1 it's admittedly more structure than strictly necessary, but it pays off in Phase 3 (LLM integration).
