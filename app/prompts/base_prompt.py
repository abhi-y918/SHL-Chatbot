"""Abstract base prompt."""

from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """Contract for prompt builders."""

    @abstractmethod
    def build(self, context: dict[str, str]) -> str:
        """Build and return formatted system prompt."""
