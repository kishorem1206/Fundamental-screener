import uuid
import asyncio
from datetime import datetime, timezone
from typing import TypeVar, Callable, Awaitable


def generate_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def build_cache_key(
    provider: str,
    symbol: str,
    data_type: str,
    params: dict | None = None,
    date: str | None = None,
) -> str:
    params = params or {}
    param_str = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
    parts = [provider, symbol, data_type]
    if param_str:
        parts.append(param_str)
    if date:
        parts.append(date)
    return ":".join(parts).upper()


def chunk(lst: list, size: int) -> list[list]:
    return [lst[i : i + size] for i in range(0, len(lst), size)]


T = TypeVar("T")


async def p_limit(
    tasks: list[Callable[[], Awaitable[T]]],
    concurrency: int,
) -> list[T]:
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(task: Callable[[], Awaitable[T]]) -> T:
        async with semaphore:
            return await task()

    return list(await asyncio.gather(*[bounded(t) for t in tasks]))
