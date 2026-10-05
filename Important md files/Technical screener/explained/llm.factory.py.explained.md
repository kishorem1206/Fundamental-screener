# backend/app/llm/factory.py — Beginner Explanation

> **Source file:** `backend/app/llm/factory.py`

---

## 1. What is this file?

Creates the LLM (Large Language Model) provider instance based on the `LLM_PROVIDER` config value. Currently only supports `gpt_oss` (OpenAI-compatible APIs like OpenAI, Azure OpenAI, or local models via Ollama).

Equivalent to TypeScript's `llm/factory.ts`.

---

## 2. The factory pattern

A **factory** is a function that creates an object based on a configuration value, hiding the construction details:

```python
# Without factory (caller must know all providers):
if config.llm_provider == "gpt_oss":
    provider = GPTOSSProvider(config.llm_api_key, config.llm_api_base_url, ...)
elif config.llm_provider == "anthropic":
    provider = AnthropicProvider(...)
# ...

# With factory (caller just calls the factory):
provider = create_llm_provider()
```

Callers only see `llm_provider` (the final object), not the construction logic.

---

## 3. Line-by-line explanation

```python
def _create_provider() -> LLMProvider:
    match config.llm_provider:
        case "gpt_oss":
            return GPTOSSProvider(
                api_key=config.llm_api_key or "",
                api_base_url=config.llm_api_base_url or "https://api.openai.com/v1",
                model=config.llm_model or "gpt-4o",
            )
        case _:
            logger.warning(
                "Unknown LLM provider, defaulting to gpt_oss",
                provider=config.llm_provider,
            )
            return GPTOSSProvider(
                api_key=config.llm_api_key or "",
                api_base_url=config.llm_api_base_url or "https://api.openai.com/v1",
                model=config.llm_model or "gpt-4o",
            )
```

**`match config.llm_provider:`** — Python 3.10+ structural pattern matching. Equivalent to `switch` in TypeScript.

**`case "gpt_oss":`** — Matches the string `"gpt_oss"` exactly.

**`case _:`** — The wildcard/default case. Matches anything not caught by previous cases. Equivalent to `default:` in a switch statement.

**`config.llm_api_key or ""`** — If `config.llm_api_key` is `None` (not set in `.env`), use empty string. The provider itself raises `LLMNotConfiguredError` if the API key is actually needed but empty.

---

```python
llm_provider = _create_provider()
```

Called once at module load time. All code imports and uses this singleton:
```python
from app.llm.factory import llm_provider
result = llm_provider.complete(messages, options)
```

---

## 4. Currently unused (Phase 1)

The LLM provider is wired up but not called in Phase 1 (no chat routes yet). It's created at startup so:
1. We verify the configuration is valid early (fails fast if `LLM_PROVIDER` is set to something unknown)
2. Phase 3 (chat routes) can import and use it without changes

---

## 5. OpenAI-compatible APIs

`gpt_oss` (OSS = Open Standard) supports any API that follows the OpenAI format:
- OpenAI itself (`https://api.openai.com/v1`)
- Azure OpenAI
- Local models via Ollama (`http://localhost:11434/v1`)
- Anthropic (with OpenAI compatibility layer)

Change `LLM_API_BASE_URL` in `.env` to point to any compatible provider.
