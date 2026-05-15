"""Abstract base class that all agents must inherit from."""

from abc import ABC, abstractmethod

from langchain_core.messages import BaseMessage

from app.enums.agent_types import AgentType


class BaseAgent(ABC):
    """Contract for all agents in the system.

    Subclasses must implement:
        - process(): run the agent logic and return a reply string.
        - validate_input(): assert preconditions on the incoming message.
        - get_system_prompt(): return the system prompt string for this agent.
    """

    def __init__(self, agent_type: AgentType) -> None:
        """Initialise with the concrete agent type enum value."""
        self.agent_type = agent_type

    @abstractmethod
    def process(
        self,
        session_id: str,
        message: str,
        history: list[BaseMessage],
    ) -> str:
        """Run the agent and return the assistant reply.

        Args:
            session_id: Caller's session identifier.
            message: Latest user message.
            history: Prior conversation turns.

        Returns:
            Assistant reply text.
        """

    @abstractmethod
    def validate_input(self, message: str) -> None:
        """Validate the incoming user message.

        Args:
            message: Raw user message text.

        Raises:
            ValidationError: If the message fails validation.
        """

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt string for this agent.

        Returns:
            Formatted system prompt.
        """
