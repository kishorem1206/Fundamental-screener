import time
from app.technical.shared.schemas import AgentTask, AgentResult
from app.technical.agents.registry import agent_registry
from app.logger import logger


class AgentMessageBus:
    def dispatch(self, task: AgentTask) -> AgentResult:
        agent = agent_registry.get(task.to_agent)
        log = logger.bind(
            correlation_id=task.correlation_id,
            task_id=task.task_id,
            to_agent=task.to_agent,
            task_type=task.task_type,
        )

        log.debug("Dispatching task")
        start = time.time()

        try:
            result = agent.handle(task)
            duration_ms = (time.time() - start) * 1000
            log.info("Task completed", status=result.status, duration_ms=duration_ms)
            return result
        except Exception as err:
            duration_ms = (time.time() - start) * 1000
            log.error("Task failed", error=str(err), duration_ms=duration_ms)
            raise


agent_message_bus = AgentMessageBus()
