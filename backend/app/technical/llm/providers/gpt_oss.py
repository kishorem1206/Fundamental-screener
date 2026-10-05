import re
import time
import httpx
from app.technical.llm.types import LLMCompletionOptions, LLMCompletionResult
from app.technical.shared.errors import LLMNotConfiguredError
from app.config import config
from app.logger import logger

_RETRY_AFTER_RE = re.compile(r"try again in\s+([\d.]+)s", re.IGNORECASE)
_MAX_RETRIES = 3


def _parse_retry_after(response: httpx.Response) -> float:
    """Extract wait seconds from Groq 429 response (header or body)."""
    header = response.headers.get("retry-after") or response.headers.get("x-ratelimit-reset-tokens")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    try:
        body = response.json()
        msg = body.get("error", {}).get("message", "")
        m = _RETRY_AFTER_RE.search(msg)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return 10.0  # safe fallback


class GPTOSSProvider:
    provider_id = "gpt-oss"

    def __init__(self) -> None:
        self.model = config.llm_model or "gpt-4o-mini"
        self._api_key = config.llm_api_key
        self._api_base = config.llm_api_base_url or "https://api.openai.com/v1"

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def complete(self, options: LLMCompletionOptions) -> LLMCompletionResult:
        if not self.is_configured():
            raise LLMNotConfiguredError()

        messages = []
        if options.system_prompt:
            messages.append({"role": "system", "content": options.system_prompt})
        messages.extend({"role": m.role, "content": m.content} for m in options.messages)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": options.temperature if options.temperature is not None else 0.1,
            "max_tokens": options.max_tokens if options.max_tokens is not None else 2048,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        last_error: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            start = time.time()
            with httpx.Client() as client:
                response = client.post(
                    f"{self._api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                )

            if response.status_code == 429:
                wait = _parse_retry_after(response) + 1.0  # +1s buffer
                logger.warning("LLM rate limited, retrying", attempt=attempt, wait_s=round(wait, 1))
                time.sleep(wait)
                last_error = RuntimeError(f"LLM API error {response.status_code}: {response.text}")
                continue

            if not response.is_success:
                raise RuntimeError(f"LLM API error {response.status_code}: {response.text}")

            data = response.json()
            duration_ms = (time.time() - start) * 1000

            return LLMCompletionResult(
                content=data["choices"][0]["message"]["content"] if data.get("choices") else "",
                model=data.get("model", self.model),
                provider=self.provider_id,
                input_tokens=data.get("usage", {}).get("prompt_tokens"),
                output_tokens=data.get("usage", {}).get("completion_tokens"),
                duration_ms=duration_ms,
            )

        raise last_error or RuntimeError("LLM request failed after retries")
