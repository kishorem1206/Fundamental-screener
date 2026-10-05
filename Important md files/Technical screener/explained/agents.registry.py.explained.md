# backend/app/agents/registry.py — Beginner Explanation

> **Source file:** `backend/app/agents/registry.py`

---

## 1. What is this file?

Defines `AgentRegistry` — a simple lookup table that maps agent IDs to agent instances. When the message bus needs to dispatch a task to an agent, it calls `agent_registry.get(agent_id)` to find it.

Equivalent to TypeScript's `agentRegistry.ts`.

---

## 2. The Registry pattern

Think of this as a **phone book**:
- Registering an agent = adding a name + number to the phone book
- Getting an agent = looking up a number by name
- The message bus = the caller who uses the phone book

```python
agent_registry.register(universe_agent)    # Add to phone book
agent_registry.register(classification_agent)

agent = agent_registry.get("universe_agent")  # Look up
agent.handle(task)
```

---

## 3. Line-by-line explanation

```python
class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}
```

**`self._agents`** — A Python dict. Keys are agent ID strings (like `"universe_agent"`), values are agent instances. The underscore prefix `_` is Python convention for "private to this class".

---

```python
    def register(self, agent: Any) -> None:
        agent_id = agent.agent_id
        if agent_id in self._agents:
            logger.warning("Agent already registered, overwriting", agent_id=agent_id)
        self._agents[agent_id] = agent
        logger.info("Agent registered", agent_id=agent_id)
```

**`agent.agent_id`** — Every agent must have an `agent_id` attribute (set on the agent class). The registry uses this as the dict key.

---

```python
    def get(self, agent_id: str) -> Any:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent not registered: {agent_id}")
        return agent
```

**`dict.get(key)`** — Returns `None` if the key doesn't exist (vs `dict[key]` which raises `KeyError`). We check for `None` and raise a more descriptive `ValueError`.

---

```python
    def has(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def list_registered(self) -> list[str]:
        return list(self._agents.keys())
```

Utility methods. `in dict` checks key existence efficiently (O(1) dict lookup).

---

```python
agent_registry = AgentRegistry()
```

**Module-level singleton** — Created once when this module is first imported. All code that does `from app.agents.registry import agent_registry` gets the same instance.

---

## 4. When agents are registered

In `app/main.py`'s `lifespan` function:
```python
agent_registry.register(universe_agent)
agent_registry.register(classification_agent)
```

This runs on server startup, before any HTTP requests are handled.

---

## 5. Why a registry?

Without a registry, routes would directly import and call agents:
```python
from app.agents.universe_agent import universe_agent
result = universe_agent.handle(task)
```

With a registry, the message bus can dispatch to any agent without knowing which agents exist:
```python
agent = agent_registry.get(task.to_agent)
result = agent.handle(task)
```

This makes it easy to add new agents later: just register them in `lifespan` without changing any route code.
