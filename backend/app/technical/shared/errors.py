class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500, detail: object = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail


class ValidationError(AppError):
    def __init__(self, message: str, detail: object = None) -> None:
        super().__init__("VALIDATION_ERROR", message, 400, detail)


class NotFoundError(AppError):
    def __init__(self, resource: str, id: str | None = None) -> None:
        msg = f"{resource} '{id}' not found" if id else f"{resource} not found"
        super().__init__("NOT_FOUND", msg, 404)


class MCPUnavailableError(AppError):
    def __init__(self, provider: str, capability: str) -> None:
        super().__init__(
            "MCP_UNAVAILABLE",
            f"Provider {provider} does not support capability: {capability}",
            503,
            {"provider": provider, "capability": capability},
        )


class MCPBlockedError(AppError):
    def __init__(self, provider: str, tool: str, reason: str) -> None:
        super().__init__(
            "MCP_BLOCKED",
            f"Tool {tool} on {provider} is blocked: {reason}",
            403,
            {"provider": provider, "tool": tool, "reason": reason},
        )


class LLMNotConfiguredError(AppError):
    def __init__(self) -> None:
        super().__init__("LLM_NOT_CONFIGURED", "LLM provider is not configured", 503)


class DataUnavailableError(AppError):
    def __init__(self, symbol: str, data_type: str) -> None:
        super().__init__(
            "DATA_UNAVAILABLE",
            f"Data unavailable for {symbol}: {data_type}",
            404,
            {"symbol": symbol, "dataType": data_type},
        )
