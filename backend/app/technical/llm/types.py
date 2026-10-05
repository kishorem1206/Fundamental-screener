from typing import Literal, Protocol
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMCompletionOptions:
    messages: list[LLMMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    system_prompt: str | None = None


@dataclass
class LLMCompletionResult:
    content: str
    model: str
    provider: str
    input_tokens: int | None
    output_tokens: int | None
    duration_ms: float


class LLMProvider(Protocol):
    provider_id: str
    model: str

    def is_configured(self) -> bool: ...
    def complete(self, options: LLMCompletionOptions) -> LLMCompletionResult: ...
