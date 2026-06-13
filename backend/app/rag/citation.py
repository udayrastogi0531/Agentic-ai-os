"""
Nidhi — Citation Tracking

Formats and tracks citations from RAG retrieval for trustworthy responses.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """A source citation from RAG retrieval."""
    document_id: str
    document_name: str
    chunk_index: int
    page_number: int | None
    content_snippet: str
    relevance_score: float


def format_citations(
    chunks: list[dict],
    document_names: dict[str, str],
) -> tuple[str, list[Citation]]:
    """
    Format RAG chunks into a citation context string and citation list.

    Args:
        chunks: Retrieved chunks from RAG retriever.
        document_names: Mapping of document_id → filename.

    Returns:
        Tuple of (formatted_context_for_llm, list_of_citations).
    """
    if not chunks:
        return "", []

    context_parts = []
    citations = []

    for i, chunk in enumerate(chunks, start=1):
        doc_id = chunk.get("document_id", "unknown")
        doc_name = document_names.get(doc_id, "Unknown Document")
        page = chunk.get("page_number")

        # Build context for LLM
        page_str = f", Page {page}" if page else ""
        context_parts.append(
            f"[Source {i}: {doc_name}{page_str}]\n{chunk['content']}"
        )

        # Build citation object
        citations.append(Citation(
            document_id=doc_id,
            document_name=doc_name,
            chunk_index=chunk.get("chunk_index", 0),
            page_number=page,
            content_snippet=chunk["content"][:200],
            relevance_score=chunk.get("relevance_score", 0.0),
        ))

    context = "\n\n---\n\n".join(context_parts)
    return context, citations


def format_citation_response(citations: list[Citation]) -> str:
    """Format citations for display in the response."""
    if not citations:
        return ""

    lines = ["\n\n---\n📚 **Sources:**"]
    seen = set()

    for c in citations:
        key = (c.document_name, c.page_number)
        if key in seen:
            continue
        seen.add(key)

        page_str = f", Page {c.page_number}" if c.page_number else ""
        lines.append(f"- {c.document_name}{page_str}")

    return "\n".join(lines)
