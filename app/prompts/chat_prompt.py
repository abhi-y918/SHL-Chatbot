"""Chat agent system prompt builder."""

from app.prompts.base_prompt import BasePrompt

_CHAT_TEMPLATE = """\
You are a helpful, concise, and friendly AI assistant.
User context:
  - Session ID: {session_id}
  - User name: {user_name}

Respond in plain text. Be direct and accurate. If you are unsure, say so.\
"""


class ChatPrompt(BasePrompt):
    """Builds the system prompt for the ChatAgent."""

    def build(self, context: dict[str, str]) -> str:
        """Render the chat prompt with the provided context.

        Args:
            context: Must contain 'session_id' and optionally 'user_name'.

        Returns:
            Formatted system prompt string.
        """
        return _CHAT_TEMPLATE.format(
            session_id=context.get("session_id", "unknown"),
            user_name=context.get("user_name", "User"),
        )
