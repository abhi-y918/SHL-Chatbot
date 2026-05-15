"""SummaryAgent: condenses conversation history into bullet-point summaries."""

from langchain_core.messages import BaseMessage, HumanMessage

from app.core.base_agent import BaseAgent
from app.core.decorators import log_execution, validate_session
from app.core.exceptions import ValidationError
from app.enums.agent_types import AgentType
from app.prompts.summary_prompt import SummaryPrompt
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

_logger = get_logger(__name__)

_MIN_HISTORY_TURNS = 1


class SummaryAgent(BaseAgent):
    """Produces a concise summary of the conversation using SummaryPrompt."""

    def __init__(self) -> None:
        """Initialise with LLM service and summary prompt builder."""
        super().__init__(agent_type=AgentType.SUMMARY)
        self._llm = LLMService()
        self._prompt = SummaryPrompt()

    @validate_session
    @log_execution
    def process(
        self,
        session_id: str,
        message: str,
        history: list[BaseMessage],
    ) -> str:
        """Summarise the conversation history.

        Args:
            session_id: Active session identifier.
            message: Trigger message (e.g. "summarize our chat").
            history: Full conversation history to summarise.

        Returns:
            Bullet-point summary string.
        """
        self.validate_input(message)
        context = {
            "session_id": session_id,
            "turn_count": str(len(history)),
        }
        system_prompt = self.get_system_prompt(**context)
        payload = [*history, HumanMessage(content="Please summarise the conversation above.")]
        return self._llm.invoke(system_prompt=system_prompt, messages=payload)

    def validate_input(self, message: str, **kwargs: object) -> None:
        """Ensure message is not empty.

        Args:
            message: Trigger message text.

        Raises:
            ValidationError: If the message is blank.
        """
        if not message or not message.strip():
            raise ValidationError("Blank message", "SummaryAgent requires non-empty input")

    def get_system_prompt(self, **context: str) -> str:
        """Build and return the summary system prompt.

        Args:
            **context: Must include 'session_id' and 'turn_count'.

        Returns:
            Formatted system prompt string.
        """
        return self._prompt.build(dict(context))
