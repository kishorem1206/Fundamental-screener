from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.screening.dsl import ScreenDSL
from app.technical.services.screening_service import screening_service
from app.logger import logger


class FilterAgent:
    agent_id = "filter_agent"
    task_types = ["RUN_SCREEN"]

    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "RUN_SCREEN":
            return self._run_screen(task)
        return self._failure(task, "UNKNOWN_TASK", f"Unknown task type: {task.task_type}")

    def _run_screen(self, task: AgentTask) -> AgentResult:
        try:
            payload = task.payload or {}
            dsl = ScreenDSL.model_validate(payload)
            result = screening_service.run(dsl)
            return self._success(task, result)
        except ValueError as e:
            return self._failure(task, "VALIDATION_ERROR", str(e))
        except Exception as e:
            logger.error("FilterAgent: screen failed", error=str(e))
            return self._failure(task, "SCREEN_FAILED", str(e))

    def _success(self, task: AgentTask, data) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="SUCCESS",
            data=data,
        )

    def _failure(self, task: AgentTask, code: str, message: str) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="FAILED",
            data=None,
            errors=[AgentError(code=code, message=message)],
        )


filter_agent = FilterAgent()
