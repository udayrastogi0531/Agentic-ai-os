"""
Uday AI — Embedding Utilities

Generates embeddings using sentence-transformers for semantic search.
Uses a singleton model instance for performance.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def _get_embedding_model():
    """Lazy-load the embedding model (singleton)."""
    embed_model_name = settings.embedding_model
    if embed_model_name == "nomic-embed-text" or "nomic" in embed_model_name.lower():
        from langchain_ollama import OllamaEmbeddings
        logger.info(f"Loading Ollama Embeddings model: {settings.ollama_embed_model} at {settings.ollama_base_url}")
        return OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embed_model,
        )
    else:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading sentence-transformer model: {embed_model_name}")
        return SentenceTransformer(embed_model_name)


def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for a single text string.

    Args:
        text: Input text to embed.

    Returns:
        List of floats representing the embedding vector.
    """
    model = _get_embedding_model()
    if hasattr(model, "embed_query"):
        return model.embed_query(text)
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts.

    Args:
        texts: List of input texts.

    Returns:
        List of embedding vectors.
    """
    model = _get_embedding_model()
    if hasattr(model, "embed_documents"):
        return model.embed_documents(texts)
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings.tolist()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
