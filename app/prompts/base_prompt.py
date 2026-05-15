"""Abstract base prompt that all concrete prompts must implement."""

from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """Contract for all prompt builders.

    Each subclass constructs a system prompt string from a context dict.
    """

    @abstractmethod
    def build(self, context: dict[str, str]) -> str:
        """Build and return a formatted system prompt.

        Args:
            context: Key-value pairs injected into the prompt template.

        Returns:
            Fully rendered system prompt string.
        """
