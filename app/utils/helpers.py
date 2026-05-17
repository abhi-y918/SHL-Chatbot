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
    """Strip markdown code fences and extract the JSON object.

    Handles common LLM output patterns:
    - ```json ... ```
    - ``` ... ```
    - Raw JSON with leading/trailing text
    """
    # Remove markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    # Find the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def safe_json_parse(text: str) -> dict:
    """Parse JSON from LLM output with multiple fallback strategies."""
    if not text or not text.strip():
        return {"reply": "", "recommendations": [], "end_of_conversation": False}

    cleaned = extract_json(text)
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            # Normalize: ensure all required fields exist
            result.setdefault("reply", "")
            result.setdefault("recommendations", [])
            result.setdefault("end_of_conversation", False)
            # Coerce null to empty list
            if result["recommendations"] is None:
                result["recommendations"] = []
            return result
    except json.JSONDecodeError:
        pass

    # Fallback: try to fix common JSON issues
    try:
        # Fix trailing commas before closing braces/brackets
        fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
        result = json.loads(fixed)
        if isinstance(result, dict):
            result.setdefault("reply", "")
            result.setdefault("recommendations", [])
            result.setdefault("end_of_conversation", False)
            if result["recommendations"] is None:
                result["recommendations"] = []
            return result
    except json.JSONDecodeError:
        pass

    # Last resort: treat entire text as the reply
    return {"reply": text.strip(), "recommendations": [], "end_of_conversation": False}
