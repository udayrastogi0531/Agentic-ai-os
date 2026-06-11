"""
Uday AI — Hybrid Search Combiner

Combines Dense Semantic Search (vector distance) with Sparse Keyword Search (BM25 Okapi)
using a weighted linear combination.
"""

from __future__ import annotations

import math
import logging
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


class LocalBM25Scorer:
    """Okapi BM25 implementation for local keyword relevance computation."""

    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(documents)
        self.doc_lens = [len(doc.split()) for doc in documents]
        self.avg_doc_len = sum(self.doc_lens) / max(1, self.corpus_size)
        self.doc_freqs: list[Counter[str]] = []
        self.idf: dict[str, float] = {}

        # Tokenize and compute frequencies
        all_words = set()
        for doc in documents:
            freq = Counter(doc.lower().split())
            self.doc_freqs.append(freq)
            all_words.update(freq.keys())

        # Compute IDF
        for word in all_words:
            doc_count = sum(1 for freq in self.doc_freqs if word in freq)
            # Standard BM25 IDF formulation
            self.idf[word] = math.log((self.corpus_size - doc_count + 0.5) / (doc_count + 0.5) + 1.0)

    def compute_score(self, query: str, index: int) -> float:
        """Score a specific document in the corpus against the query."""
        score = 0.0
        query_words = query.lower().split()
        freq = self.doc_freqs[index]
        d_len = self.doc_lens[index]

        for word in query_words:
            if word in freq:
                word_freq = freq[word]
                idf = self.idf.get(word, 0.0)
                num = word_freq * (self.k1 + 1)
                den = word_freq + self.k1 * (1 - self.b + self.b * (d_len / self.avg_doc_len))
                score += idf * (num / den)
        return score


def combine_dense_and_sparse(
    dense_results: list[dict[str, Any]],
    query: str,
    alpha: float = 0.7,  # weight given to dense search
) -> list[dict[str, Any]]:
    """
    Combines dense similarity scores with BM25 sparse scores.

    Args:
        dense_results: Retrieved document chunks from ChromaDB with 'relevance_score'.
        query: User search query.
        alpha: Weight coefficient in range [0, 1] for dense scoring.

    Returns:
        Combined list of document chunks sorted by hybrid score.
    """
    if not dense_results:
        return []

    # Extract texts for sparse corpus indexing
    corpus = [chunk.get("content", "") for chunk in dense_results]
    bm25 = LocalBM25Scorer(corpus)

    # Calculate raw BM25 scores
    sparse_scores = [bm25.compute_score(query, idx) for idx in range(len(dense_results))]
    max_sparse = max(sparse_scores) if sparse_scores else 0.0
    min_sparse = min(sparse_scores) if sparse_scores else 0.0
    sparse_range = max_sparse - min_sparse

    for idx, chunk in enumerate(dense_results):
        dense_score = chunk.get("relevance_score", 0.5)

        # Normalize BM25 score to [0, 1] range
        raw_sparse = sparse_scores[idx]
        normalized_sparse = (
            (raw_sparse - min_sparse) / sparse_range if sparse_range > 0.0 else 0.5
        )

        # Compute weighted hybrid score
        hybrid_score = (alpha * dense_score) + ((1.0 - alpha) * normalized_sparse)
        chunk["relevance_score"] = round(hybrid_score, 4)

    return sorted(dense_results, key=lambda c: c["relevance_score"], reverse=True)
