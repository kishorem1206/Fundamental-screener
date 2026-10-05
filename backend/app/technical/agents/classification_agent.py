import time
from dataclasses import asdict
from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.services.classification_service import classification_service, StockListFilters
from app.logger import logger


class ClassificationAgent:
    agent_id = "ClassificationAgent"
    task_types = ["LIST_STOCKS", "GET_STOCK"]

    def handle(self, task: AgentTask) -> AgentResult:
        start = time.time()
        log = logger.bind(agent=self.agent_id, task_id=task.task_id, task_type=task.task_type)

        try:
            if task.task_type == "LIST_STOCKS":
                payload = task.payload or {}
                raw_filters = payload.get("filters", {})
                filters = StockListFilters(
                    universe_id=raw_filters.get("universeId"),
                    sector=raw_filters.get("sector"),
                    macro_sector=raw_filters.get("macroSector"),
                    market_cap_category=raw_filters.get("marketCapCategory"),
                    limit=raw_filters.get("limit", 100),
                    offset=raw_filters.get("offset", 0),
                )
                data = classification_service.list_stocks(filters)
                log.info("Listed stocks", count=len(data))
                return self._success(task, [asdict(s) for s in data], start)

            if task.task_type == "GET_STOCK":
                payload = task.payload or {}
                stock_id = payload["stockId"]
                data = classification_service.get_stock(stock_id)
                log.info("Got stock", stock_id=stock_id)
                return self._success(task, asdict(data), start)

            raise ValueError(f"Unknown task type: {task.task_type}")

        except Exception as err:
            log.error("ClassificationAgent task failed", error=str(err))
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


classification_agent = ClassificationAgent()
