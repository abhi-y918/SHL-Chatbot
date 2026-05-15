"""Pure utility functions with no side-effects."""

import uuid


def generate_session_id() -> str:
    """Generate a globally unique session identifier.

    Returns:
        A UUID4 hex string.
    """
    return uuid.uuid4().hex


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate *text* to *max_chars* characters appending an ellipsis if needed.

    Args:
        text: Source string.
        max_chars: Maximum character count before truncation.

    Returns:
        Possibly-truncated string.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


def sanitize_input(text: str) -> str:
    """Strip leading/trailing whitespace and collapse internal runs.

    Args:
        text: Raw user input.

    Returns:
        Sanitised string.
    """
    return " ".join(text.split())
