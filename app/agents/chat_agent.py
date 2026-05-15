"""ChatAgent: handles general conversational requests."""

from langchain_core.messages import BaseMessage, HumanMessage

from app.core.base_agent import BaseAgent
from app.core.decorators import log_execution, validate_session
from app.core.exceptions import ValidationError
from app.enums.agent_types import AgentType
from app.prompts.chat_prompt import ChatPrompt
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

_logger = get_logger(__name__)


class ChatAgent(BaseAgent):
    """Handles free-form conversational turns using the ChatPrompt."""

    def __init__(self) -> None:
        """Initialise with LLM service and chat prompt builder."""
        super().__init__(agent_type=AgentType.CHAT)
        self._llm = LLMService()
        self._prompt = ChatPrompt()

    @validate_session
    @log_execution
    def process(
        self,
        session_id: str,
        message: str,
        history: list[BaseMessage],
    ) -> str:
        """Run the chat agent for a single user turn.

        Args:
            session_id: Active session identifier.
            message: Latest user message.
            history: Prior conversation turns.

        Returns:
            Assistant reply text.
        """
        self.validate_input(message)
        system_prompt = self.get_system_prompt(session_id=session_id)
        full_history = [*history, HumanMessage(content=message)]
        return self._llm.invoke(system_prompt=system_prompt, messages=full_history)

    def validate_input(self, message: str, **kwargs: object) -> None:
        """Ensure message is not empty.

        Args:
            message: Raw user message text.

        Raises:
            ValidationError: If the message is blank.
        """
        if not message or not message.strip():
            raise ValidationError("Blank message", "ChatAgent requires non-empty input")

    def get_system_prompt(self, **context: str) -> str:
        """Build and return the chat system prompt.

        Args:
            **context: Arbitrary key-value pairs forwarded to ChatPrompt.build().

        Returns:
            Formatted system prompt string.
        """
        return self._prompt.build(dict(context))
