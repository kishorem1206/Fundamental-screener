from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import config
from app.logger import logger
from app.routes import health, stocks, fundamental, banking_data, screening, governance, valuation, sectors, sources, analyst_consensus, documents, company_summary, yfinance_extended, segments, market_movers, broker_reports, brands, concall, premium, history_charts, pl_intelligence, balance_sheet_intelligence, cash_flow_intelligence, quarterly_intelligence, bank_roe, company_scores, quick_scores
from app.mcp.server import mcp_asgi_app, mcp_server
from app.infrastructure.database.client import close_database
from app.infrastructure.redis.client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Fundamental Screener API started", port=config.api_port, env=config.node_env)
    # The MCP session manager runs its own task group for the life of the
    # process — app.mount() does NOT auto-start a mounted sub-app's lifespan,
    # so without this every MCP request fails with "Task group is not
    # initialized" (confirmed the hard way while building Stage 1).
    async with mcp_server.session_manager.run():
        yield
    logger.info("Shutting down")
    close_database()
    close_redis()


app = FastAPI(
    title="Fundamental Screener API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(fundamental.router)
app.include_router(banking_data.router)
app.include_router(screening.router)
app.include_router(governance.router)
app.include_router(valuation.router)
app.include_router(sectors.router)
app.include_router(sources.router)
app.include_router(analyst_consensus.router)
app.include_router(documents.router)
app.include_router(company_summary.router)
app.include_router(yfinance_extended.router)
app.include_router(segments.router)
app.include_router(market_movers.router)
app.include_router(broker_reports.router)
app.include_router(brands.router)
app.include_router(concall.router)
app.include_router(premium.router)
app.include_router(history_charts.router)
app.include_router(pl_intelligence.router)
app.include_router(balance_sheet_intelligence.router)
app.include_router(cash_flow_intelligence.router)
app.include_router(quarterly_intelligence.router)
app.include_router(bank_roe.router)
app.include_router(company_scores.router)
app.include_router(quick_scores.router)

# Architecture v2 Stage 1: MCP interface layer, mounted here rather than run
# as a separate process — see app/mcp/server.py's module docstring.
app.mount("/mcp", mcp_asgi_app())
