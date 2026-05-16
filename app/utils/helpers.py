"""Pure utility functions."""

import json
import re
import uuid


def generate_session_id() -> str:
    """Generate a UUID4 hex session identifier."""
    return uuid.uuid4().hex


def sanitize_input(text: str) -> str:
    """Strip and collapse whitespace."""
    return " ".join(text.split())


def extract_json(text: str) -> str:
    """Strip markdown code fences and extract the JSON object."""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def safe_json_parse(text: str) -> dict:
    """Parse JSON from LLM output with fallback."""
    cleaned = extract_json(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"reply": text.strip(), "recommendations": [], "end_of_conversation": False}
