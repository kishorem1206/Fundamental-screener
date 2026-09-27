import json
import redis as redis_lib
from app.config import config
from app.logger import logger

_redis_client = None


def _get_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis_lib.from_url(config.redis_url, decode_responses=True)
        except Exception as e:
            logger.warning("Redis connection failed", error=str(e))
    return _redis_client


def cache_get(key: str) -> str | None:
    try:
        client = _get_client()
        if client is None:
            return None
        full_key = f"{config.redis_key_prefix}{key}"
        return client.get(full_key)
    except Exception:
        return None


def cache_set(key: str, value: str, ttl_seconds: int = 3600) -> None:
    try:
        client = _get_client()
        if client is None:
            return
        full_key = f"{config.redis_key_prefix}{key}"
        client.setex(full_key, ttl_seconds, value)
    except Exception:
        pass


def cache_get_json(key: str):
    raw = cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def cache_set_json(key: str, value, ttl_seconds: int = 3600) -> None:
    try:
        cache_set(key, json.dumps(value), ttl_seconds)
    except Exception:
        pass


def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.close()
        except Exception:
            pass
        _redis_client = None
