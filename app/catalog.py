"""SHL product catalog loader and processor."""

import json
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

KEY_TO_TYPE: dict[str, str] = {
    "Knowledge & Skills": "K",
    "Personality & Behavior": "P",
    "Simulations": "S",
    "Ability & Aptitude": "A",
    "Biodata & Situational Judgment": "B",
    "Competencies": "C",
    "Development & 360": "D",
    "Assessment Exercises": "E",
}


def compute_test_type(keys: list[str]) -> str:
    """Map catalog 'keys' to short test-type codes (e.g. 'K', 'P,C')."""
    codes = []
    for k in keys:
        code = KEY_TO_TYPE.get(k)
        if code and code not in codes:
            codes.append(code)
    return ",".join(codes) if codes else "K"


def fetch_catalog() -> list[dict]:
    """Download the SHL product catalog JSON from the configured URL."""
    settings = get_settings()
    logger.info("Fetching catalog from %s", settings.catalog_url)
    resp = httpx.get(settings.catalog_url, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    logger.info("Fetched %d catalog entries", len(data))
    return data


def process_entry(entry: dict) -> dict:
    """Normalise a single catalog entry into a flat dict for indexing."""
    keys = entry.get("keys", [])
    test_type = compute_test_type(keys)
    job_levels = ", ".join(entry.get("job_levels", []))
    languages = ", ".join(entry.get("languages", []))

    return {
        "entity_id": entry.get("entity_id", ""),
        "name": entry.get("name", ""),
        "url": entry.get("link", ""),
        "description": entry.get("description", ""),
        "test_type": test_type,
        "keys": ", ".join(keys),
        "job_levels": job_levels,
        "languages": languages,
        "duration": entry.get("duration", ""),
        "remote": entry.get("remote", ""),
        "adaptive": entry.get("adaptive", ""),
    }


def build_document_text(item: dict) -> str:
    """Create a rich text document for ChromaDB embedding from a processed entry."""
    parts = [
        f"Assessment: {item['name']}",
        f"Description: {item['description']}",
        f"Category: {item['keys']}",
        f"Test Type: {item['test_type']}",
        f"Job Levels: {item['job_levels']}",
        f"Duration: {item['duration']}",
        f"Languages: {item['languages']}",
        f"Remote: {item['remote']}",
        f"Adaptive: {item['adaptive']}",
    ]
    return "\n".join(parts)


def load_and_process_catalog() -> list[dict]:
    """Fetch the catalog and return a list of processed entries."""
    raw = fetch_catalog()
    processed = [process_entry(e) for e in raw if e.get("status") == "ok"]
    logger.info("Processed %d valid catalog entries", len(processed))
    return processed
