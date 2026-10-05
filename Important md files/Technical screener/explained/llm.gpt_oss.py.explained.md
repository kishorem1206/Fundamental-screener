# backend/app/llm/providers/gpt_oss.py — Beginner Explanation

> **Source file:** `backend/app/llm/providers/gpt_oss.py`

---

## 1. What is this file?

Defines `GPTOSSProvider` — the LLM integration that calls any OpenAI-compatible REST API. It is currently configured to call **Groq's free API** (`https://api.groq.com/openai/v1`) with the `openai/gpt-oss-20b` model, but the same class works with Ollama, OpenAI, or any provider that implements the standard `/v1/chat/completions` endpoint.

---

## 2. OpenAI-compatible API

The OpenAI Chat Completions API has become an industry standard. Many providers implement the same endpoint, same request format, same response format:

```
POST {api_base}/v1/chat/completions
Authorization: Bearer {api_key}
{
  "model": "...",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0.1,
  "max_tokens": 2048
}
```

`GPTOSSProvider` works with Groq, Ollama, OpenAI, etc. by accepting a configurable `LLM_API_BASE_URL` from `.env`.

---

## 3. Rate limit retry logic

Groq's free tier has a **Tokens Per Minute (TPM) limit of 8,000**. A large screening context (50 stocks with RSI data) can easily consume 4,000–5,000 tokens in one request. When two such requests arrive within a minute, the second one gets a **429 Too Many Requests** error.

The provider handles this automatically with up to 3 retries:

```python
_MAX_RETRIES = 3

for attempt in range(1, _MAX_RETRIES + 1):
    response = client.post(...)

    if response.status_code == 429:
        wait = _parse_retry_after(response) + 1.0  # +1s buffer
        logger.warning("LLM rate limited, retrying", attempt=attempt, wait_s=wait)
        time.sleep(wait)
        continue  # retry

    if not response.is_success:
        raise RuntimeError(...)  # non-retryable error

    return LLMCompletionResult(...)  # success

raise last_error  # all retries exhausted
```

---

## 4. `_parse_retry_after()` — extracting the wait time

Groq tells you exactly how long to wait. The function checks three places:

```python
def _parse_retry_after(response):
    # 1. Standard HTTP header: Retry-After: 8
    header = response.headers.get("retry-after") or response.headers.get("x-ratelimit-reset-tokens")
    if header:
        return float(header)

    # 2. Groq error body: "Please try again in 7.762499999s"
    body = response.json()
    msg = body["error"]["message"]
    m = re.search(r"try again in\s+([\d.]+)s", msg)
    if m:
        return float(m.group(1))

    # 3. Safe fallback
    return 10.0
```

The regex `r"try again in\s+([\d.]+)s"` matches Groq's exact error message format and captures the decimal seconds (e.g. `7.762`). The caller adds 1 extra second as a buffer before retrying.

---

## 5. `complete()` method — full flow

```python
def complete(self, options: LLMCompletionOptions) -> LLMCompletionResult:
    # Build the messages list
    messages = []
    if options.system_prompt:
        messages.append({"role": "system", "content": options.system_prompt})
    messages.extend({"role": m.role, "content": m.content} for m in options.messages)

    # Try up to _MAX_RETRIES times
    for attempt in range(1, _MAX_RETRIES + 1):
        start = time.time()
        response = client.post(url, headers=..., json=payload, timeout=60.0)

        if response.status_code == 429:
            wait = _parse_retry_after(response) + 1.0
            time.sleep(wait)
            continue

        if not response.is_success:
            raise RuntimeError(f"LLM API error {response.status_code}: {response.text}")

        data = response.json()
        return LLMCompletionResult(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.model),
            provider=self.provider_id,
            input_tokens=data["usage"]["prompt_tokens"],
            output_tokens=data["usage"]["completion_tokens"],
            duration_ms=(time.time() - start) * 1000,
        )
```

**`timeout=60.0`** — aborts if the API takes more than 60 seconds. LLM inference can be slow, especially for large contexts.

**`data["choices"][0]["message"]["content"]`** — the standard OpenAI response path: `choices` is a list, take the first item, get its `message`, get the `content` string.

---

## 6. Configuration (from `.env`)

```
LLM_PROVIDER=gpt-oss
LLM_MODEL=openai/gpt-oss-20b
LLM_API_KEY=gsk_...         ← Groq API key
LLM_API_BASE_URL=https://api.groq.com/openai/v1
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.1
```

The `.env` must be in `backend/` (not the project root) for `pydantic-settings` to load it when running from `cd backend && make dev`.
