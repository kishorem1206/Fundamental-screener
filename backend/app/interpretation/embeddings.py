"""Local embedding client — Concall Intelligence System, Stage C2.

The concall doc specifies EmbeddingGemma; that's not pulled locally (only
`qwen3-embedding` and `llama3.2:3b` are, confirmed via `ollama list`).
Using `qwen3-embedding` instead — already installed, no new download, and
embedding-quality differences matter far less here than the Llama
narrative-quality tradeoff did, since retrieval/similarity is a more
forgiving task than generation. Swapping to a pulled `embeddinggemma` later
is a one-line config change (`config.embedding_model`), not a rewrite.

Deliberately NOT reusing `app/llm/client.py::LLMClient` — that wraps the
OpenAI-compatible `/v1/chat/completions` surface; embeddings use Ollama's
own `/api/embeddings` endpoint, a different shape entirely.
"""
from __future__ import annotations

import requests

from app.config import config
from app.logger import logger


def embed_text(text: str) -> list[float] | None:
    """Never raises — logs and returns None on failure (Ollama down, empty
    input), matching every other ingestion path's contract. Callers must
    skip storing a chunk whose embedding came back None, not substitute a
    zero vector (a zero vector would silently corrupt similarity search
    for every other real chunk)."""
    if not text or not text.strip():
        return None
    try:
        r = requests.post(
            f"{config.ollama_base_url}/api/embeddings",
            json={"model": config.embedding_model, "prompt": text},
            timeout=30,
        )
        r.raise_for_status()
        embedding = r.json().get("embedding")
    except Exception as e:
        logger.warning("embeddings: embed_text failed", error=str(e), text_preview=text[:80])
        return None

    if not embedding or len(embedding) != config.embedding_dims:
        logger.warning("embeddings: unexpected embedding shape", got=len(embedding) if embedding else 0,
                        expected=config.embedding_dims)
        return None
    return embedding
