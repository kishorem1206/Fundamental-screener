"""A small direct client for NSE's MCP servers (JSON-RPC over HTTP).

The `mcp` library's streamable-HTTP client fails against these servers (they
answer plain JSON and reject the session-close call), so this speaks the three
messages needed itself: initialize, notifications/initialized, tools/call.

NSE throttles a burst of calls for about a minute (requests then hang), so
calls are spaced `MIN_INTERVAL` apart across threads and a timed-out call
waits and retries with a fresh session.
"""
from __future__ import annotations

import json
import threading
import time

import httpx

from app.logger import logger

BHAVCOPY = "https://mcp.nseindia.in/bhavcopy/cm/mcp"
MARKET = "https://mcp.nseindia.in/cmmkt/mcp"
MIN_INTERVAL = 1.5
_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
_INIT = {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "equity-research", "version": "0.1"}}

_lock = threading.Lock()
_next_slot = 0.0


def _wait_turn() -> None:
    global _next_slot
    with _lock:
        now = time.monotonic()
        slot = max(now, _next_slot)
        _next_slot = slot + MIN_INTERVAL
    time.sleep(max(0.0, slot - now))


class NseMcpError(RuntimeError):
    pass


class NseMcp:
    def __init__(self, url: str, timeout: float = 12.0):
        self.url, self.timeout = url, timeout
        self._http = httpx.Client(timeout=timeout)
        self._sid: str | None = None
        self._id = 0
        self._guard = threading.Lock()

    def _post(self, body: dict) -> httpx.Response:
        headers = {**_HEADERS, **({"Mcp-Session-Id": self._sid} if self._sid else {})}
        return self._http.post(self.url, json=body, headers=headers)

    def _open(self) -> None:
        self._sid = None
        r = self._post({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": _INIT})
        r.raise_for_status()
        self._sid = r.headers.get("Mcp-Session-Id")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    @staticmethod
    def _body(r: httpx.Response) -> dict:
        text = r.text
        if r.headers.get("content-type", "").startswith("text/event-stream"):
            text = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")][-1]
        return json.loads(text)

    def _rpc(self, method: str, params: dict) -> dict:
        last: Exception | None = None
        for attempt in range(3):
            _wait_turn()
            try:
                with self._guard:
                    if self._sid is None:
                        self._open()
                    self._id += 1
                    r = self._post({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
                if r.status_code in (400, 404) and "session" in r.text.lower():
                    self._sid = None  # session expired: open a new one and retry
                    continue
                r.raise_for_status()
                out = self._body(r)
                if "error" in out:
                    raise NseMcpError(str(out["error"]))
                return out["result"]
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:  # incl. 502/504 from NSE's gateway
                last = exc
                self._sid = None
                logger.warning("nse mcp call timed out; waiting out the throttle", method=method, attempt=attempt)
                # the first fetch of a symbol can hang while NSE's server loads it (a quick retry then
                # succeeds); a real throttle lasts about a minute
                time.sleep((8, 65, 0)[attempt])
        raise NseMcpError(f"NSE MCP did not answer ({self.url}): {last}")

    def tools(self) -> list[dict]:
        return self._rpc("tools/list", {}).get("tools", [])

    def call(self, tool: str, **arguments):
        """A tool's answer, parsed as JSON when it is JSON."""
        result = self._rpc("tools/call", {"name": tool, "arguments": arguments})
        text = "\n".join(c.get("text", "") for c in result.get("content", []))
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text
        if isinstance(data, dict) and data.get("error"):
            raise NseMcpError(str(data["error"]))
        return data


bhavcopy = NseMcp(BHAVCOPY)
market = NseMcp(MARKET)
