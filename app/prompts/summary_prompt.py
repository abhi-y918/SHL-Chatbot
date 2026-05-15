"""Summary agent system prompt builder."""

from app.prompts.base_prompt import BasePrompt

_SUMMARY_TEMPLATE = """\
You are a precise summarisation AI.
Your task: produce a concise summary of the conversation below.
Session: {session_id}
Turn count: {turn_count}

Rules:
  - Use bullet points.
  - Maximum 5 bullets.
  - Each bullet ≤ 20 words.\
"""


class SummaryPrompt(BasePrompt):
    """Builds the system prompt for the SummaryAgent."""

    def build(self, context: dict[str, str]) -> str:
        """Render the summary prompt with the provided context.

        Args:
            context: Must contain 'session_id' and 'turn_count'.

        Returns:
            Formatted system prompt string.
        """
        return _SUMMARY_TEMPLATE.format(
            session_id=context.get("session_id", "unknown"),
            turn_count=context.get("turn_count", "0"),
        )
