from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    node_env: str = "development"
    api_port: int = 3002
    api_host: str = "0.0.0.0"

    database_url: str = "postgresql://screener:screener@localhost:5433/screener"
    database_pool_min: int = 2
    database_pool_max: int = 10

    redis_url: str = "redis://localhost:6379"
    redis_key_prefix: str = "fa:"

    llm_provider: str = "gpt-oss"  # read by app/technical/llm/factory.py
    llm_model: str = "openai/gpt-oss-20b"
    llm_api_key: str = ""
    llm_api_base_url: str = "https://api.groq.com/openai/v1"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1

    # Local Ollama fallback — used only when the primary (Groq) call hits a
    # rate limit (429), not for other failure modes (a malformed prompt
    # should surface as a real error, not silently degrade to a weaker
    # model). See app/llm/client.py's module docstring.
    llm_fallback_enabled: bool = True
    llm_fallback_base_url: str = "http://localhost:11434/v1"
    llm_fallback_model: str = "llama3.2:3b"

    # Concall Intelligence System, Stage C2 — Ollama's native (non-OpenAI-
    # compat) API for embeddings. The doc calls for "EmbeddingGemma"
    # specifically; `qwen3-embedding` is what's actually pulled locally
    # (confirmed via `ollama list`), used instead rather than pulling a new
    # model. See app/interpretation/embeddings.py's module docstring.
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "qwen3-embedding"
    embedding_dims: int = 4096

    log_level: str = "INFO"
    log_pretty: bool = True

    minio_endpoint: str = "localhost:9092"
    minio_access_key: str = "screener"
    minio_secret_key: str = "screener123"
    minio_bucket: str = "fa-documents"
    minio_secure: bool = False

    cors_origins: str = "http://localhost:5174,http://localhost:3000"
    reports_dir: str = "./reports"

    # Screener.in login (optional) — anonymous scraping only ever returns the
    # free "Key Points" preview (its first section); the remaining sections
    # live behind a login-gated wiki page. When these are set,
    # screener_client.py logs in via Playwright first and fetches the full
    # commentary page instead of the truncated preview. Left blank, ingestion
    # silently falls back to the anonymous preview — never raises.
    screener_email: str = ""
    screener_password: str = ""

    # IndianAPI.in (stock.indianapi.in) — Free plan. Only used for analyst
    # rating distribution and market-wide movers, not covered elsewhere.
    indianapi_key: str = ""

    # Gemini (Google AI) — 2026-09-15 evaluation: user wants to compare
    # against the Groq gpt-oss-20b primary (`app/llm/client.py::llm_client`)
    # for extraction-style calls. Accessed via Google's OpenAI-compatible
    # endpoint so it's a drop-in LLMClient config, not a new SDK dependency.
    gemini_api_key: str = ""
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-3.8-flash"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


config = Settings()
