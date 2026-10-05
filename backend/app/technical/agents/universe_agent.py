import time
from dataclasses import asdict
from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.services.classification_service import classification_service
from app.logger import logger


class UniverseAgent:
    agent_id = "UniverseAgent"
    task_types = ["LIST_UNIVERSES", "GET_UNIVERSE_STOCKS"]

    def handle(self, task: AgentTask) -> AgentResult:
        start = time.time()
        log = logger.bind(agent=self.agent_id, task_id=task.task_id, task_type=task.task_type)

        try:
            if task.task_type == "LIST_UNIVERSES":
                data = classification_service.list_universes()
                log.info("Listed universes", count=len(data))
                return self._success(task, [asdict(u) for u in data], start)

            if task.task_type == "GET_UNIVERSE_STOCKS":
                payload = task.payload or {}
                universe_id = payload["universeId"]
                limit = payload.get("limit", 500)
                offset = payload.get("offset", 0)
                data = classification_service.get_universe_stocks(universe_id, limit, offset)
                log.info("Got universe stocks", universe_id=universe_id, count=len(data))
                return self._success(task, [asdict(s) for s in data], start)

            raise ValueError(f"Unknown task type: {task.task_type}")

        except Exception as err:
            log.error("UniverseAgent task failed", error=str(err))
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


universe_agent = UniverseAgent()
