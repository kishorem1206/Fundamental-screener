# backend/app/llm/types.py — Beginner Explanation

> **Source file:** `backend/app/llm/types.py`

---

## 1. What is this file?

Defines data structures for LLM interactions: messages, completion options, completion results, and the `LLMProvider` Protocol (interface).

---

## 2. The data structures

### `LLMMessage`

```python
@dataclass
class LLMMessage:
    role: str   # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: str | None = None
    name: str | None = None
```

One message in a conversation. Follows the OpenAI message format.

**`role`** values:
- `"system"` — Instruction to the LLM (e.g., "You are a stock analysis assistant")
- `"user"` — What the user typed
- `"assistant"` — What the LLM replied
- `"tool"` — Result of a tool call returned to the LLM

**`tool_call_id`** — When role is `"tool"`, links this result back to the specific tool call the LLM made.

---

### `LLMCompletionOptions`

```python
@dataclass
class LLMCompletionOptions:
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: list[dict] | None = None
    tool_choice: str | dict | None = None
    stream: bool = False
```

**`temperature`** — Controls randomness. `0.0` = deterministic (same input → same output), `1.0` = creative/random. For financial data analysis, lower temperature (0.3-0.5) is better.

**`tools`** — List of MCP tool definitions to give the LLM. When provided, the LLM can respond with "call this tool" instead of generating text.

**`max_tokens`** — Maximum length of the response. 4096 tokens ≈ 3000 words.

---

### `LLMCompletionResult`

```python
@dataclass
class LLMCompletionResult:
    content: str
    tool_calls: list[dict] | None
    finish_reason: str  # "stop" | "tool_calls" | "length" | "content_filter"
    usage: dict | None
    model: str
```

**`finish_reason`** tells you why the LLM stopped generating:
- `"stop"` — Natural end of response
- `"tool_calls"` — LLM wants to call a tool (handle the tool call, then continue)
- `"length"` — Hit `max_tokens` limit (response may be truncated)
- `"content_filter"` — Content filtered by the API provider

**`usage`** — Token counts: `{"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}`. Used for cost tracking.

---

### `LLMProvider` Protocol

```python
class LLMProvider(Protocol):
    def complete(
        self,
        messages: list[LLMMessage],
        options: LLMCompletionOptions | None = None,
    ) -> LLMCompletionResult: ...
```

Any class with a `complete()` method matching this signature is an `LLMProvider`. `GPTOSSProvider` implements it. Future providers (Anthropic Claude, Google Gemini) would implement the same interface without changing any calling code.

---

## 3. Tool calling flow (Phase 3 preview)

```
User: "What's the RSI for INFY?"
    ↓
LLM receives the question with tool definitions
    ↓
LLM responds: finish_reason="tool_calls", tool_calls=[{name: "get_quotes", args: {symbol: "INFY"}}]
    ↓
Orchestrator calls Kite MCP: get_quotes(symbol="INFY")
    ↓
Gets: {last_price: 1842.5, ...}
    ↓
Sends result back to LLM as role="tool" message
    ↓
LLM responds: "INFY is trading at ₹1842.50. The RSI (14) is currently 58.3, indicating..."
    ↓
Return to user
```
