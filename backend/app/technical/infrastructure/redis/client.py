import json
import redis
from app.config import config
from app.logger import logger

# The technical screener keeps the key prefix it had as a separate app, so its
# cached scans survive the move and never collide with the fundamental "fa:" keys.
_KEY_PREFIX = "screener:"

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            config.redis_url,
            decode_responses=True,
        )
    return _redis_client


def check_redis_health() -> dict:
    try:
        r = get_redis()
        pong = r.ping()
        return {"status": "ok"} if pong else {"status": "error", "detail": "No PONG"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None


def cache_get(key: str) -> object | None:
    r = get_redis()
    prefixed = _KEY_PREFIX + key
    raw = r.get(prefixed)
    if raw is None:
        return None
    return json.loads(raw)


def cache_set(key: str, value: object, ttl_seconds: int) -> None:
    r = get_redis()
    prefixed = _KEY_PREFIX + key
    r.set(prefixed, json.dumps(value), ex=ttl_seconds)


def cache_del(key: str) -> None:
    r = get_redis()
    prefixed = _KEY_PREFIX + key
    r.delete(prefixed)
