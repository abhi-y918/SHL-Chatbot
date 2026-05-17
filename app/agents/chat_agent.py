
from typing import Any

from app.core.base_agent import BaseAgent
from app.core.decorators import log_execution
from app.core.exceptions import ValidationError
from app.enums.agent_types import AgentType
from app.prompts.chat_prompt import ChatPrompt
from app.services.llm_service import LLMService


class ChatAgent(BaseAgent):
    """Handles free-form conversational turns for SHL assessment selection."""

    def __init__(self) -> None:
        super().__init__(agent_type=AgentType.CHAT)
        self._llm = LLMService()
        self._prompt = ChatPrompt()

    @log_execution
    def process(self, message: str, history: list[dict[str, str]], **kwargs: Any) -> str:
        """Run the chat agent for a single user turn."""
        self.validate_input(message)
        catalog_context = kwargs.get("catalog_context", "")
        system_prompt = self.get_system_prompt(catalog_context=catalog_context)
        return self._llm.invoke(system_prompt, history)

    def validate_input(self, message: str) -> None:
        """Ensure message is not empty."""
        if not message or not message.strip():
            raise ValidationError("Blank message", "ChatAgent requires non-empty input")

    def get_system_prompt(self, **kwargs: Any) -> str:
        """Build and return the chat system prompt."""
        return self._prompt.build(dict(kwargs))
