import dataclasses
from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.scoring.engine import ScoreCriterion, score_stock
from app.logger import logger


class ScoringAgent:
    agent_id = "scoring_agent"
    task_types = ["SCORE_STOCK"]

    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "SCORE_STOCK":
            return self._score_stock(task)
        return self._failure(task, "UNKNOWN_TASK", f"Unknown task: {task.task_type}")

    def _score_stock(self, task: AgentTask) -> AgentResult:
        payload = task.payload or {}
        indicators = payload.get("indicators", {})
        raw_criteria = payload.get("criteria")  # optional list of criterion dicts

        criteria = None
        if raw_criteria:
            try:
                criteria = [ScoreCriterion(**c) for c in raw_criteria]
            except Exception as e:
                return self._failure(task, "VALIDATION_ERROR", f"Invalid criteria: {e}")

        try:
            result = score_stock(indicators, criteria)
            return self._success(task, dataclasses.asdict(result))
        except Exception as e:
            logger.error("ScoringAgent failed", error=str(e))
            return self._failure(task, "SCORING_FAILED", str(e))

    def _success(self, task: AgentTask, data) -> AgentResult:
        return AgentResult(task_id=task.task_id, correlation_id=task.correlation_id,
                           agent=self.agent_id, status="SUCCESS", data=data)

    def _failure(self, task: AgentTask, code: str, message: str) -> AgentResult:
        return AgentResult(task_id=task.task_id, correlation_id=task.correlation_id,
                           agent=self.agent_id, status="FAILED", data=None,
                           errors=[AgentError(code=code, message=message)])


scoring_agent = ScoringAgent()
