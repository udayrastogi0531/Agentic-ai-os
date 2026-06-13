"""
Nidhi — Document Chunk Re-ranker

Re-ranks retrieved document chunks against the user query for high-precision retrieval.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from app.memory.embeddings import _get_embedding_model, cosine_similarity

logger = logging.getLogger(__name__)

_cross_encoder = None


@lru_cache(maxsize=1)
def _get_cross_encoder():
    """Lazy-load the sentence-transformers CrossEncoder if available."""
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers.cross_encoder import CrossEncoder
            logger.info("Loading Cross-Encoder model: cross-encoder/ms-marco-MiniLM-L-6-v2")
            _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
            logger.info("✅ Cross-Encoder model loaded successfully.")
        except Exception as e:
            logger.warning(f"Cross-Encoder failed to initialize: {e}. Falling back to cosine similarity embeddings.")
            _cross_encoder = None
    return _cross_encoder


def rerank_chunks(query: str, chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    """
    Re-rank a list of retrieved document chunks against the search query.

    Args:
        query: Search query text.
        chunks: List of chunk dictionaries containing 'content'.
        top_k: Number of sorted chunks to return.

    Returns:
        The top_k sorted chunks with enriched 'relevance_score'.
    """
    if not chunks:
        return []

    encoder = _get_cross_encoder()

    if encoder is not None:
        try:
            # Pair query with each chunk content
            pairs = [[query, chunk.get("content", "")] for chunk in chunks]
            scores = encoder.predict(pairs)

            # Assign scores to chunks
            for idx, score in enumerate(scores):
                # Normalize cross-encoder logit scores into [0, 1] range using sigmoid
                normalized_score = float(1.0 / (1.0 + math.exp(-score)))
                chunks[idx]["relevance_score"] = normalized_score
        except Exception as e:
            logger.warning(f"CrossEncoder prediction failed: {e}. Falling back to cosine similarity ranking.")
            _apply_cosine_fallback(query, chunks)
    else:
        _apply_cosine_fallback(query, chunks)

    # Sort chunks by relevance score descending
    sorted_chunks = sorted(chunks, key=lambda c: c.get("relevance_score", 0.0), reverse=True)
    return sorted_chunks[:top_k]


def _apply_cosine_fallback(query: str, chunks: list[dict[str, Any]]) -> None:
    """Fallback ranking logic using embeddings cosine similarity."""
    try:
        model = _get_embedding_model()
        query_vector = model.encode(query, normalize_embeddings=True).tolist()

        for chunk in chunks:
            chunk_content = chunk.get("content", "")
            chunk_vector = model.encode(chunk_content, normalize_embeddings=True).tolist()
            chunk["relevance_score"] = cosine_similarity(query_vector, chunk_vector)
    except Exception as e:
        logger.error(f"Cosine fallback ranking failed: {e}")
        # If everything fails, maintain relative order with neutral scores
        for chunk in chunks:
            chunk["relevance_score"] = chunk.get("relevance_score", 0.5)
import math
