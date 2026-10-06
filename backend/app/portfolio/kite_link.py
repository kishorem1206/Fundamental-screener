"""A long-lived, read-only connection from this backend to Zerodha's hosted
Kite MCP server (https://mcp.kite.trade/mcp).

Kite logs in per MCP session: `login_url()` opens a session and returns
Kite's login link; once the user has logged in with that link, the same
session can read holdings. The session lives in one background thread with
its own event loop, so it survives between requests until the backend
restarts (then the user logs in again).

Only reading tools can be called. Order placement, modification and
cancellation are refused here whatever the caller asks — the technical
screener's V1 rule (no order execution), kept for the whole app.
"""
from __future__ import annotations

import asyncio
import json
import threading
from concurrent.futures import Future

from app.logger import logger

URL = "https://mcp.kite.trade/mcp"
READ_ONLY = {"login", "get_profile", "get_holdings", "get_mf_holdings", "get_margins", "get_positions", "get_ltp", "get_quotes"}


class KiteLink:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._session = None
        self._ready = threading.Event()
        self._stop: asyncio.Event | None = None
        self._lock = threading.Lock()
        self.error: str | None = None

    def _start(self) -> None:
        with self._lock:
            if self._loop and self._session:
                return
            self._ready.clear()
            self.error = None
            threading.Thread(target=self._run, name="kite-mcp", daemon=True).start()
        if not self._ready.wait(45) or self._session is None:
            raise RuntimeError(self.error or "could not reach Kite's MCP server")

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._hold())
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            logger.warning("kite mcp session ended", error=str(exc))
        finally:
            self._session = None
            self._ready.set()

    async def _hold(self) -> None:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        self._stop = asyncio.Event()
        async with streamable_http_client(URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                self._session = session
                self._ready.set()
                await self._stop.wait()

    def call(self, tool: str, args: dict | None = None, timeout: float = 60) -> str:
        if tool not in READ_ONLY:
            raise PermissionError(f"'{tool}' is not a read-only Kite tool; this app never places or changes orders")
        self._start()
        fut: Future = asyncio.run_coroutine_threadsafe(self._session.call_tool(tool, args or {}), self._loop)
        result = fut.result(timeout)
        text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
        if getattr(result, "isError", False) or text.startswith("Failed") or "log in first" in text.lower():
            raise LookupError(text or f"Kite {tool} failed")
        return text

    def call_json(self, tool: str, args: dict | None = None):
        text = self.call(tool, args)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = min([i for i in (text.find("["), text.find("{")) if i >= 0], default=-1)
            if start < 0:
                raise LookupError(f"Kite {tool} returned no data: {text[:200]}")
            return json.loads(text[start:])

    def login_url(self) -> str:
        import re

        text = self.call("login")
        m = re.search(r"https://[^\s)\]\"']+", text)
        if not m:
            raise LookupError(f"Kite did not return a login link: {text[:200]}")
        return m.group(0)

    def logged_in(self) -> dict | None:
        try:
            return self.call_json("get_profile")
        except Exception:  # noqa: BLE001 — not logged in, or no session yet
            return None

    def close(self) -> None:
        if self._loop and self._stop:
            self._loop.call_soon_threadsafe(self._stop.set)


kite = KiteLink()
