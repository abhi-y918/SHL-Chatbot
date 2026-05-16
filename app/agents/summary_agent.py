"""SummaryAgent: handles assessment comparisons and conversation summaries."""

from typing import Any

from app.core.base_agent import BaseAgent
from app.core.decorators import log_execution
from app.core.exceptions import ValidationError
from app.enums.agent_types import AgentType
from app.prompts.summary_prompt import SummaryPrompt
from app.services.llm_service import LLMService


class SummaryAgent(BaseAgent):
    """Produces comparisons and summaries using SummaryPrompt."""

    def __init__(self) -> None:
        super().__init__(agent_type=AgentType.SUMMARY)
        self._llm = LLMService()
        self._prompt = SummaryPrompt()

    @log_execution
    def process(self, message: str, history: list[dict[str, str]], **kwargs: Any) -> str:
        """Run the summary agent."""
        self.validate_input(message)
        system_prompt = self.get_system_prompt()
        return self._llm.invoke(system_prompt, history)

    def validate_input(self, message: str) -> None:
        """Ensure message is not empty."""
        if not message or not message.strip():
            raise ValidationError("Blank message")

    def get_system_prompt(self, **kwargs: Any) -> str:
        """Return the summary prompt."""
        return self._prompt.build(dict(kwargs))
