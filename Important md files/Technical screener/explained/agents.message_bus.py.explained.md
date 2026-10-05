# backend/app/agents/message_bus.py — Beginner Explanation

> **Source file:** `backend/app/agents/message_bus.py`

---

## 1. What is this file?

Defines `AgentMessageBus` — the dispatcher that receives tasks, finds the right agent from the registry, calls it, and logs the result.

Equivalent to TypeScript's `agentMessageBus.ts`.

---

## 2. The message bus concept

A **message bus** is a communication channel between components. Instead of route handlers directly calling agent methods, they send a task to the bus, which routes it to the correct agent:

```
Route handler
    ↓ creates AgentTask
Message Bus
    ↓ looks up agent by to_agent field
UniverseAgent (or ClassificationAgent, etc.)
    ↓ handles task
AgentResult
    ↓
Route handler gets the result
```

This decoupling means routes don't need to know which agent handles which task.

---

## 3. Line-by-line explanation

```python
class AgentMessageBus:
    def dispatch(self, task: AgentTask) -> AgentResult:
        start = time.time()
        log = logger.bind(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            from_agent=task.from_agent,
            to_agent=task.to_agent,
            task_type=task.task_type,
        )
```

**`logger.bind(...)`** — Creates a new logger with extra fields pre-attached. Every subsequent `log.info(...)` or `log.error(...)` call will include `task_id`, `correlation_id`, etc. automatically. This is structlog's equivalent of adding context to every log line.

---

```python
        try:
            log.info("Dispatching task")
            agent = agent_registry.get(task.to_agent)
            result = agent.handle(task)
            duration_ms = (time.time() - start) * 1000

            result.duration_ms = duration_ms
            log.info("Task completed", status=result.status, duration_ms=round(duration_ms, 2))
            return result
```

**`agent_registry.get(task.to_agent)`** — Looks up the agent by the `to_agent` field of the task (e.g., `"universe_agent"`).

**`agent.handle(task)`** — Calls the agent's main method with the task. Returns an `AgentResult`.

**`time.time()`** — Returns the current time in seconds (float). Subtracting two calls gives elapsed time in seconds; multiplying by 1000 converts to milliseconds.

---

```python
        except ValueError as e:
            # Agent not registered
            duration_ms = (time.time() - start) * 1000
            log.error("Agent not found", error=str(e))
            return AgentResult(
                task_id=task.task_id,
                correlation_id=task.correlation_id,
                agent=task.to_agent,
                status="FAILED",
                data=None,
                errors=[AgentError(code="AGENT_NOT_FOUND", message=str(e))],
                duration_ms=duration_ms,
            )
```

If `agent_registry.get()` raises `ValueError` (agent not registered), we return a failed `AgentResult` instead of letting the exception propagate. Routes can check `result.status == "FAILED"` and handle it cleanly.

---

## 4. Why synchronous?

The `dispatch` method is a regular `def` (not `async def`) because:
1. Our agents call synchronous SQLAlchemy methods
2. FastAPI runs sync route handlers in a thread pool automatically
3. Keeping everything sync avoids async complexity for a beginner learning Python

---

## 5. Module-level singleton

```python
agent_message_bus = AgentMessageBus()
```

One bus instance shared by all routes. Routes import and use it:
```python
from app.agents.message_bus import agent_message_bus

result = agent_message_bus.dispatch(task)
```
