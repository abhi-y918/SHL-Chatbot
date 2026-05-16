"""Agent type enumeration."""

from enum import Enum


class AgentType(str, Enum):
    """Supported agent types in the system."""

    CHAT = "chat"
    SUMMARY = "summary"
