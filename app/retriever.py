"""ChromaDB-backed assessment retriever — in-memory collection."""

import logging

import chromadb

from app.catalog import build_document_text, load_and_process_catalog
from app.config import get_settings

logger = logging.getLogger(__name__)


class AssessmentRetriever:
    """Manages the ChromaDB in-memory collection of SHL assessments.

    Call .initialize() once at startup to fetch the catalog and build the index.
    Call .search() per request to find relevant assessments.
    """

    def __init__(self) -> None:
        self._client = chromadb.Client()  # in-memory
        self._collection = self._client.get_or_create_collection(
            name="shl_assessments",
            metadata={"hnsw:space": "cosine"},
        )
        self._catalog_lookup: dict[str, dict] = {}

    def initialize(self) -> None:
        """Fetch catalog and index all assessments into ChromaDB."""
        entries = load_and_process_catalog()

        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict] = []

        for entry in entries:
            doc_text = build_document_text(entry)
            eid = entry["entity_id"]

            documents.append(doc_text)
            ids.append(eid)
            metadatas.append({
                "name": entry["name"],
                "url": entry["url"],
                "test_type": entry["test_type"],
                "keys": entry["keys"],
                "job_levels": entry["job_levels"],
                "duration": entry["duration"],
                "remote": entry["remote"],
                "adaptive": entry["adaptive"],
            })

            self._catalog_lookup[entry["name"].lower()] = entry
            self._catalog_lookup[eid] = entry

        self._collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )
        logger.info(
            "Indexed %d assessments into ChromaDB", self._collection.count()
        )

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        """Search for assessments relevant to the query.

        Args:
            query: Natural-language search text derived from conversation.
            top_k: Number of results to return (default from config).

        Returns:
            List of dicts with assessment details, ordered by relevance.
        """
        k = top_k or get_settings().retrieval_top_k
        results = self._collection.query(
            query_texts=[query],
            n_results=min(k, self._collection.count()),
        )

        assessments: list[dict] = []
        if not results["metadatas"]:
            return assessments

        for i, meta in enumerate(results["metadatas"][0]):
            doc_text = (
                results["documents"][0][i] if results["documents"] else ""
            )
            distance = (
                results["distances"][0][i]
                if results["distances"]
                else 1.0
            )
            assessments.append({
                **meta,
                "description": doc_text,
                "relevance_score": round(1 - distance, 4),
            })

        return assessments

    def validate_url(self, url: str) -> bool:
        """Check if a URL exists in the indexed catalog."""
        for entry in self._catalog_lookup.values():
            if entry.get("url") == url:
                return True
        return False

    def get_all_names(self) -> list[str]:
        """Return all assessment names in the catalog."""
        seen: set[str] = set()
        names: list[str] = []
        for entry in self._catalog_lookup.values():
            name = entry.get("name", "")
            if name and name not in seen:
                seen.add(name)
                names.append(name)
        return sorted(names)
