"""LLM client — two configurations share this same class:

- `llm_client` (`primary="groq"`, the default): Groq (gpt-oss-20b) primary,
  local Ollama (llama3.2:3b) fallback. Groq's rate limit (429) was hit
  repeatedly throughout this project — every extraction call already has to
  survive Groq's own SDK-level retry-with-backoff, which still sometimes
  stalls a whole pipeline stage for minutes when several calls collide
  (2026-09 sessions). The fallback only triggers on an actual rate-limit
  error, not any failure — a malformed prompt or schema bug should surface
  as a real error, not silently degrade to a much smaller model.

- `local_llm_client` (`primary="local"`, added 2026-09-13 for the Llama
  Report Interpretation Architecture — see `Sector md files/Summary.md`):
  local Ollama primary, Groq fallback — the user explicitly chose local
  Llama as the primary interpretation engine for that pipeline (free,
  private, no rate limits), accepting weaker prose quality than gpt-oss-20b
  as the tradeoff. Here the fallback direction's failure condition is
  necessarily broader than `RateLimitError`: Ollama doesn't return OpenAI
  rate-limit errors, it just fails to connect or times out if the daemon
  isn't running — so *any* exception from the local primary triggers
  fail-over to Groq, unlike the Groq-primary config where only a genuine
  rate limit does (a malformed prompt there should still surface as a real
  error, not silently swap models).

Callers should treat a fallback-served answer as lower-confidence than a
primary one — `last_used_fallback` is exposed (same pattern as the
pre-existing `last_token_count`) so a caller that cares can check it.
"""
import json

from openai import OpenAI, RateLimitError

from app.config import config
from app.logger import logger


class LLMClient:
    def __init__(self, primary: str = "groq"):
        self._primary_name = primary

        groq_client = OpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_api_base_url,
            # The SDK's default retry-with-backoff on 429 is exactly what
            # caused the multi-minute pipeline stalls observed repeatedly
            # this project. One quick retry, then fail over instead of
            # waiting through Groq's full backoff sequence.
            max_retries=1,
        )
        ollama_client = None
        if config.llm_fallback_enabled:
            ollama_client = OpenAI(
                api_key="ollama",  # unused by Ollama's OpenAI-compat endpoint, SDK requires a non-empty string
                base_url=config.llm_fallback_base_url,
            )

        if primary == "local":
            if ollama_client is None:
                raise ValueError("LLMClient(primary='local') requires llm_fallback_enabled (Ollama) to be configured")
            self._client, self._model = ollama_client, config.llm_fallback_model
            self._fallback_client, self._fallback_model = groq_client, config.llm_model
            # See module docstring: any failure on a local primary fails over,
            # not just a rate limit (Ollama has no rate-limit concept here).
            self._fallback_exceptions: tuple[type[BaseException], ...] = (Exception,)
        else:
            self._client, self._model = groq_client, config.llm_model
            self._fallback_client, self._fallback_model = ollama_client, config.llm_fallback_model
            self._fallback_exceptions = (RateLimitError,)

        self.last_used_fallback = False
        self.last_token_count = None

    def chat(self, system_prompt: str, user_prompt: str, json_mode: bool = False,
              max_tokens: int | None = None) -> str:
        kwargs = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": config.llm_temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self._client.chat.completions.create(
                model=self._model, max_tokens=max_tokens or config.llm_max_tokens, **kwargs,
            )
            self.last_token_count = (response.usage.total_tokens if response.usage else None)
            self.last_used_fallback = False
            return response.choices[0].message.content or ""
        except self._fallback_exceptions as e:
            if self._fallback_client is None:
                logger.error("LLM call failed, no fallback configured", error=str(e), model=self._model)
                raise
            logger.warning("LLM primary failed, falling back",
                            primary_model=self._model, fallback_model=self._fallback_model, error=str(e))
            try:
                response = self._fallback_client.chat.completions.create(
                    model=self._fallback_model, max_tokens=max_tokens or config.llm_max_tokens, **kwargs,
                )
                self.last_token_count = (response.usage.total_tokens if response.usage else None)
                self.last_used_fallback = True
                return response.choices[0].message.content or ""
            except Exception as fallback_error:
                logger.error("LLM fallback call also failed", error=str(fallback_error), model=self._fallback_model)
                raise
        except Exception as e:
            logger.error("LLM call failed", error=str(e), model=self._model)
            raise

    def chat_json(self, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> dict:
        raw = self.chat(system_prompt, user_prompt, json_mode=True, max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse JSON from LLM response: {raw[:200]}")


llm_client = LLMClient()
local_llm_client = LLMClient(primary="local")
