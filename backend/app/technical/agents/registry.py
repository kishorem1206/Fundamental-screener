from app.technical.shared.schemas import AgentTask, AgentResult


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict = {}

    def register(self, agent) -> None:
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str):
        agent = self._agents.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent not registered: {agent_id}")
        return agent

    def has(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def list_registered(self) -> list[str]:
        return list(self._agents.keys())


agent_registry = AgentRegistry()
