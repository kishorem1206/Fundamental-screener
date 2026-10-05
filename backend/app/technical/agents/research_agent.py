"""
ResearchAgent — stub for Phase 9 (news, FII/DII, analyst ratings).

Currently returns a structured stub response so callers can integrate
against the interface now and the real implementation arrives later.

Task type: RESEARCH_STOCK
"""
from app.technical.shared.schemas import AgentTask, AgentResult, AgentError


class ResearchAgent:
    agent_id = "research_agent"
    task_types = ["RESEARCH_STOCK"]

    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "RESEARCH_STOCK":
            payload = task.payload or {}
            symbol = payload.get("symbol", "UNKNOWN")
            return AgentResult(
                task_id=task.task_id,
                correlation_id=task.correlation_id,
                agent=self.agent_id,
                status="PARTIAL",
                data={
                    "symbol": symbol,
                    "status": "stub",
                    "message": "ResearchAgent is a stub — full implementation arrives in Phase 9 (news, FII/DII, analyst ratings).",
                    "available_in": "Phase 9",
                },
                warnings=["Research data not yet available"],
            )
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="FAILED",
            data=None,
            errors=[AgentError(code="UNKNOWN_TASK", message=f"Unknown task: {task.task_type}")],
        )


research_agent = ResearchAgent()
