"""Abstract base class that all agents must inherit from."""

from abc import ABC, abstractmethod
from typing import Any

from app.enums.agent_types import AgentType


class BaseAgent(ABC):
    """Contract for all agents in the system."""

    def __init__(self, agent_type: AgentType) -> None:
        self.agent_type = agent_type

    @abstractmethod
    def process(self, message: str, history: list[dict[str, str]], **kwargs: Any) -> str:
        """Run the agent and return the assistant reply."""

    @abstractmethod
    def validate_input(self, message: str) -> None:
        """Validate the incoming user message."""

    @abstractmethod
    def get_system_prompt(self, **kwargs: Any) -> str:
        """Return the system prompt string for this agent."""
