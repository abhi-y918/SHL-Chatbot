"""SHL catalog loader, processor, and ChromaDB indexer."""

import json
import logging

import chromadb
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


def _compute_test_type(keys: list[str]) -> str:
    codes = [KEY_TO_TYPE[k] for k in keys if k in KEY_TO_TYPE]
    return ",".join(dict.fromkeys(codes)) if codes else "K"


def _process_entry(entry: dict) -> dict:
    keys = entry.get("keys", [])
    return {
        "entity_id": entry.get("entity_id", ""),
        "name": entry.get("name", ""),
        "url": entry.get("link", ""),
        "description": entry.get("description", ""),
        "test_type": _compute_test_type(keys),
        "keys": ", ".join(keys),
        "job_levels": ", ".join(entry.get("job_levels", [])),
        "languages": ", ".join(entry.get("languages", [])),
        "duration": entry.get("duration", ""),
        "remote": entry.get("remote", ""),
        "adaptive": entry.get("adaptive", ""),
    }


def _build_doc_text(item: dict) -> str:
    return (
        f"Assessment: {item['name']}\n"
        f"Description: {item['description']}\n"
        f"Category: {item['keys']}\nType: {item['test_type']}\n"
        f"Job Levels: {item['job_levels']}\nDuration: {item['duration']}\n"
        f"Languages: {item['languages']}\n"
        f"Remote: {item['remote']}\nAdaptive: {item['adaptive']}"
    )


class CatalogService:
    """Fetches the SHL catalog, indexes it into ChromaDB in-memory."""

    def __init__(self) -> None:
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name="shl_assessments", metadata={"hnsw:space": "cosine"},
        )
        self._url_set: set[str] = set()
        self._catalog: list[dict] = []

    def initialize(self) -> None:
        """Fetch catalog and index into ChromaDB."""
        raw = self._fetch()
        entries = [_process_entry(e) for e in raw if e.get("status") == "ok"]
        self._catalog = entries

        docs, ids, metas = [], [], []
        for e in entries:
            docs.append(_build_doc_text(e))
            ids.append(e["entity_id"])
            self._url_set.add(e["url"])
            metas.append({
                "name": e["name"], "url": e["url"],
                "test_type": e["test_type"], "keys": e["keys"],
                "job_levels": e["job_levels"], "duration": e["duration"],
                "remote": e["remote"], "adaptive": e["adaptive"],
            })
        self._collection.add(documents=docs, ids=ids, metadatas=metas)
        logger.info("Indexed %d assessments into ChromaDB", len(entries))

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        """Semantic search for assessments."""
        k = top_k or get_settings().retrieval_top_k
        results = self._collection.query(
            query_texts=[query], n_results=min(k, self._collection.count()),
        )
        out: list[dict] = []
        if results["metadatas"]:
            for i, meta in enumerate(results["metadatas"][0]):
                desc = results["documents"][0][i] if results["documents"] else ""
                out.append({**meta, "description": desc})
        return out

    def validate_url(self, url: str) -> bool:
        """Check if a URL exists in the catalog."""
        return url in self._url_set

    def _fetch(self) -> list[dict]:
        """Download the SHL catalog JSON."""
        url = get_settings().catalog_url
        logger.info("Fetching catalog from %s", url)
        resp = httpx.get(url, timeout=30.0)
        resp.raise_for_status()
        return json.loads(resp.text, strict=False)
