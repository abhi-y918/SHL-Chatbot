"""SHL Assessment Agent — orchestrates retrieval + LLM for each request."""

import json
import logging
import re

from app.llm import LLMClient
from app.models import ChatMessage, ChatResponse, Recommendation
from app.prompts import build_system_prompt, format_catalog_context
from app.retriever import AssessmentRetriever

logger = logging.getLogger(__name__)


class SHLAgent:
    """Stateless agent: each call receives full conversation, returns a response."""

    def __init__(self, retriever: AssessmentRetriever) -> None:
        self._retriever = retriever
        self._llm = LLMClient()

    def handle(self, messages: list[ChatMessage]) -> ChatResponse:
        """Process a full conversation and return the next agent reply.

        Steps:
          1. Build a search query from the conversation context.
          2. Retrieve relevant assessments from ChromaDB.
          3. Build system prompt with catalog context.
          4. Call LLM with system prompt + conversation history.
          5. Parse the structured JSON response.
          6. Validate recommendations against the catalog.
        """
        search_query = self._build_search_query(messages)
        retrieved = self._retriever.search(search_query)
        catalog_context = format_catalog_context(retrieved)
        system_prompt = build_system_prompt(catalog_context)

        llm_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        raw_response = self._llm.chat(system_prompt, llm_messages)
        return self._parse_response(raw_response)

    def _build_search_query(self, messages: list[ChatMessage]) -> str:
        """Extract a search query from the conversation history.

        Combines the last user message with key context from earlier turns
        to get the best retrieval results.
        """
        user_messages = [m.content for m in messages if m.role == "user"]
        if not user_messages:
            return ""

        # Use last 3 user messages for context, weighted toward the latest
        recent = user_messages[-3:]
        return " ".join(recent)

    def _parse_response(self, raw: str) -> ChatResponse:
        """Parse the LLM's JSON response into a ChatResponse.

        Handles common LLM output quirks: markdown fences, trailing commas, etc.
        """
        cleaned = self._extract_json(raw)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON, returning raw as reply")
            return ChatResponse(
                reply=raw.strip(),
                recommendations=[],
                end_of_conversation=False,
            )

        recommendations = self._parse_recommendations(
            data.get("recommendations", [])
        )

        return ChatResponse(
            reply=data.get("reply", raw.strip()),
            recommendations=recommendations,
            end_of_conversation=bool(data.get("end_of_conversation", False)),
        )

    def _extract_json(self, text: str) -> str:
        """Strip markdown code fences and extract the JSON object."""
        # Remove ```json ... ``` wrappers
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()

        # Find the outermost JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return text

    def _parse_recommendations(
        self, raw_recs: list,
    ) -> list[Recommendation]:
        """Validate and filter recommendations against the catalog."""
        if not raw_recs:
            return []

        valid: list[Recommendation] = []
        for rec in raw_recs:
            if not isinstance(rec, dict):
                continue
            name = rec.get("name", "")
            url = rec.get("url", "")
            test_type = rec.get("test_type", "K")

            if not name or not url:
                continue

            # Only include if the URL exists in our catalog
            if self._retriever.validate_url(url):
                valid.append(Recommendation(
                    name=name, url=url, test_type=test_type
                ))
            else:
                logger.warning("Filtered hallucinated URL: %s", url)

        return valid[:10]  # Cap at 10 per spec
