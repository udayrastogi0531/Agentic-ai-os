"""
Uday AI — Smart Document Chunking

Splits document text into semantically meaningful chunks
with configurable overlap for optimal RAG retrieval.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A document chunk with metadata."""
    content: str
    chunk_index: int
    page_number: int | None = None
    metadata: dict | None = None


def chunk_document(
    pages: list[str],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Chunk]:
    """
    Split document pages into overlapping chunks.

    Args:
        pages: List of page texts.
        chunk_size: Target characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        List of Chunk objects with metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []
    global_idx = 0

    for page_num, page_text in enumerate(pages, start=1):
        if not page_text.strip():
            continue

        splits = splitter.split_text(page_text)

        for split in splits:
            all_chunks.append(
                Chunk(
                    content=split,
                    chunk_index=global_idx,
                    page_number=page_num,
                    metadata={
                        "page_number": page_num,
                        "chunk_size": len(split),
                        "word_count": len(split.split()),
                    },
                )
            )
            global_idx += 1

    logger.info(
        f"Chunked {len(pages)} pages into {len(all_chunks)} chunks "
        f"(size={chunk_size}, overlap={chunk_overlap})"
    )
    return all_chunks
