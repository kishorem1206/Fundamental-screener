import time
from datetime import date

from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.services.nifty_index_ingestion_service import nifty_index_ingestion_service
from app.technical.services.stock_index_classification_service import stock_index_classification_service
from app.logger import logger


class NiftyIndexAgent:
    """
    Agent for Nifty index data ingestion and stock classification queries.

    Task types:
      NIFTY_SEED_CATALOG    — idempotently seed index_categories + nifty_indices rows
      NIFTY_INGEST          — full ingestion run (downloads CSVs, diffs, commits)
      NIFTY_DRY_RUN         — same as NIFTY_INGEST but never commits to DB
      NIFTY_INGEST_STATUS   — last ingestion run status
      NIFTY_STOCK_INDICES   — which Nifty indices does stock X belong to?
      NIFTY_INDEX_STOCKS    — which stocks are in index Y?
      NIFTY_LIST_INDICES    — list all known Nifty indices
      NIFTY_INDEX_INTERSECTION — stocks common to two indices
    """

    agent_id = "NiftyIndexAgent"
    task_types = [
        "NIFTY_SEED_CATALOG",
        "NIFTY_INGEST",
        "NIFTY_DRY_RUN",
        "NIFTY_INGEST_STATUS",
        "NIFTY_STOCK_INDICES",
        "NIFTY_INDEX_STOCKS",
        "NIFTY_LIST_INDICES",
        "NIFTY_INDEX_INTERSECTION",
    ]

    def handle(self, task: AgentTask) -> AgentResult:
        start = time.time()
        log = logger.bind(agent=self.agent_id, task_id=task.task_id, task_type=task.task_type)

        try:
            payload = task.payload or {}

            if task.task_type == "NIFTY_SEED_CATALOG":
                data = nifty_index_ingestion_service.seed_catalog()
                log.info("Catalog seeded", **data)
                return self._success(task, data, start)

            if task.task_type == "NIFTY_INGEST":
                index_ids = payload.get("index_ids")
                data = nifty_index_ingestion_service.ingest(dry_run=False, index_ids=index_ids)
                log.info("Ingestion complete", status=data.get("totals"))
                return self._success(task, data, start)

            if task.task_type == "NIFTY_DRY_RUN":
                index_ids = payload.get("index_ids")
                data = nifty_index_ingestion_service.ingest(dry_run=True, index_ids=index_ids)
                log.info("Dry run complete")
                return self._success(task, data, start)

            if task.task_type == "NIFTY_INGEST_STATUS":
                data = nifty_index_ingestion_service.last_run_status()
                return self._success(task, data or {"message": "No ingestion runs found"}, start)

            if task.task_type == "NIFTY_STOCK_INDICES":
                symbol = payload.get("symbol", "").strip().upper()
                if not symbol:
                    raise ValueError("payload.symbol is required")
                as_of_str = payload.get("as_of")
                as_of = date.fromisoformat(as_of_str) if as_of_str else None
                category = payload.get("category")
                data = stock_index_classification_service.stock_indices(
                    symbol=symbol, as_of=as_of, category=category
                )
                log.info("Stock indices queried", symbol=symbol)
                return self._success(task, data, start)

            if task.task_type == "NIFTY_INDEX_STOCKS":
                index_code = payload.get("index_code", "").strip().lower()
                if not index_code:
                    raise ValueError("payload.index_code is required")
                as_of_str = payload.get("as_of")
                as_of = date.fromisoformat(as_of_str) if as_of_str else None
                data = stock_index_classification_service.index_constituents(
                    index_code=index_code, as_of=as_of
                )
                log.info("Index stocks queried", index_code=index_code)
                return self._success(task, data, start)

            if task.task_type == "NIFTY_LIST_INDICES":
                category = payload.get("category")
                data = stock_index_classification_service.list_indices(category=category)
                log.info("Listed indices", count=len(data))
                return self._success(task, data, start)

            if task.task_type == "NIFTY_INDEX_INTERSECTION":
                index_a = payload.get("index_a", "").strip()
                index_b = payload.get("index_b", "").strip()
                if not index_a or not index_b:
                    raise ValueError("payload.index_a and payload.index_b are required")
                data = stock_index_classification_service.index_intersection(index_a, index_b)
                log.info("Index intersection computed", index_a=index_a, index_b=index_b)
                return self._success(task, data, start)

            raise ValueError(f"Unknown task type: {task.task_type}")

        except Exception as err:
            log.error("NiftyIndexAgent task failed", error=str(err))
            return self._failure(task, err, start)

    def _success(self, task: AgentTask, data: object, start: float) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="SUCCESS",
            data=data,
            errors=[],
            warnings=[],
            provenance=[],
            duration_ms=(time.time() - start) * 1000,
        )

    def _failure(self, task: AgentTask, err: Exception, start: float) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="FAILED",
            data=None,
            errors=[AgentError(code="INTERNAL_ERROR", message=str(err))],
            warnings=[],
            provenance=[],
            duration_ms=(time.time() - start) * 1000,
        )


nifty_index_agent = NiftyIndexAgent()
