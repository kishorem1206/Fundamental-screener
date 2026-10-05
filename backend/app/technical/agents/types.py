from typing import Protocol
from app.technical.shared.schemas import AgentTask, AgentResult


class Agent(Protocol):
    agent_id: str
    task_types: list[str]

    def handle(self, task: AgentTask) -> AgentResult: ...
