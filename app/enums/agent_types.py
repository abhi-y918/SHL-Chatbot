"""Agent type enumeration."""

from enum import Enum


class AgentType(str, Enum):
    """Defines all supported agent types in the system."""

    CHAT = "chat"
    SUMMARY = "summary"
