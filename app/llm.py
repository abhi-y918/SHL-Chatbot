"""OpenRouter LLM client using the OpenAI SDK."""

import json
import logging

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around the OpenAI SDK configured for OpenRouter."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens

    def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> str:
        """Send a chat completion request and return the assistant reply.

        Args:
            system_prompt: System instructions for the model.
            messages: Conversation history as [{"role": ..., "content": ...}].

        Returns:
            Raw assistant response text.
        """
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
            content = response.choices[0].message.content or ""
            logger.debug("LLM response length: %d chars", len(content))
            return content
        except Exception:
            logger.exception("LLM call failed")
            raise
