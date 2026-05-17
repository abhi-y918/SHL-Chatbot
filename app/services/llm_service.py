"""OpenRouter LLM client using the OpenAI SDK."""

from openai import OpenAI

from app.config import get_settings
from app.core.decorators import log_execution, retry
from app.core.exceptions import LLMError
from app.utils.logger import get_logger

_logger = get_logger(__name__)


class LLMService:
    """Wrapper around the OpenAI SDK configured for OpenRouter."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=20.0,  # 20s timeout per request to stay within 30s limit
        )
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens

    @retry(max_attempts=2, delay=1.0)
    @log_execution
    def invoke(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        """Send chat completion request and return the reply text."""
        full_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=full_messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise LLMError("LLM invocation failed", str(exc)) from exc
