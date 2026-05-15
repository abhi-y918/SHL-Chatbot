"""OpenRouter LLM client wrapper using LangChain-OpenAI."""

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.core.decorators import log_execution, retry
from app.core.exceptions import LLMError
from app.utils.logger import get_logger

_logger = get_logger(__name__)
_settings = get_settings()


def _build_client() -> ChatOpenAI:
    """Instantiate the OpenRouter-backed ChatOpenAI client.

    Returns:
        Configured ChatOpenAI instance.
    """
    return ChatOpenAI(
        model=_settings.llm_model,
        openai_api_key=_settings.openrouter_api_key,
        openai_api_base=_settings.openrouter_base_url,
        temperature=_settings.llm_temperature,
        max_tokens=_settings.llm_max_tokens,
    )


class LLMService:
    """Thin wrapper around the OpenRouter LLM providing retry and logging."""

    def __init__(self) -> None:
        """Initialise the LLM client."""
        self._client = _build_client()

    @retry(max_attempts=3, delay=2.0)
    @log_execution
    def invoke(self, system_prompt: str, messages: list[BaseMessage]) -> str:
        """Send a message list to the LLM and return the reply text.

        Args:
            system_prompt: System instructions injected at position 0.
            messages: Conversation history (HumanMessage / AIMessage turns).

        Returns:
            Assistant reply as a plain string.

        Raises:
            LLMError: If the LLM call fails after all retries.
        """
        try:
            full_messages: list[BaseMessage] = [SystemMessage(content=system_prompt), *messages]
            response = self._client.invoke(full_messages)
            return str(response.content)
        except Exception as exc:
            raise LLMError("LLM invocation failed", str(exc)) from exc
