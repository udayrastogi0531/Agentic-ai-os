"""
Uday AI — Memory Retriever

Semantic search over ChromaDB for memory retrieval.
Combines vector similarity with metadata filtering.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import chromadb

from app.database import get_chroma_client, get_or_create_collection
from app.memory.embeddings import generate_embedding

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """Handles semantic memory storage and retrieval via ChromaDB."""

    def __init__(self):
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            self._client = get_chroma_client()
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._collection = get_or_create_collection(self.client, "memories")
        return self._collection

    def store_memory(
        self,
        memory_id: str,
        content: str,
        user_id: str,
        category: str,
        importance: float = 0.5,
        metadata: dict | None = None,
    ) -> str:
        """
        Store a memory embedding in ChromaDB.

        Args:
            memory_id: Unique memory ID (UUID string).
            content: Memory text content.
            user_id: Owner user ID.
            category: Memory category.
            importance: Importance score (0-1).
            metadata: Additional metadata.

        Returns:
            The embedding ID.
        """
        embedding = generate_embedding(content)

        doc_metadata = {
            "user_id": user_id,
            "category": category,
            "importance": importance,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }

        self.collection.upsert(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[doc_metadata],
        )

        logger.debug(f"Stored memory embedding: {memory_id}")
        return memory_id

    def search_memories(
        self,
        query: str,
        user_id: str,
        category: str | None = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> list[dict]:
        """
        Semantic search for relevant memories.

        Args:
            query: Search query text.
            user_id: Filter by user.
            category: Optional category filter.
            limit: Max results.
            min_importance: Minimum importance threshold.

        Returns:
            List of memory results with scores.
        """
        query_embedding = generate_embedding(query)

        # Build where filter
        where_filter: dict = {"user_id": user_id}
        if category:
            where_filter["category"] = category

        # Build where with importance filter
        where_conditions = {"$and": [{"user_id": user_id}]}
        if category:
            where_conditions["$and"].append({"category": category})
        if min_importance > 0:
            where_conditions["$and"].append(
                {"importance": {"$gte": min_importance}}
            )

        # Simplify if only one condition
        if len(where_conditions["$and"]) == 1:
            where_conditions = where_conditions["$and"][0]

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_conditions,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

        memories = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                # ChromaDB returns cosine distance, convert to similarity
                similarity = 1 - distance

                memories.append({
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "relevance_score": round(similarity, 4),
                })

        return memories

    def delete_memory(self, memory_id: str) -> None:
        """Delete a memory embedding from ChromaDB."""
        try:
            self.collection.delete(ids=[memory_id])
            logger.debug(f"Deleted memory embedding: {memory_id}")
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")

    def get_memory_count(self, user_id: str) -> int:
        """Get the total number of memories for a user."""
        try:
            result = self.collection.get(
                where={"user_id": user_id},
                include=[],
            )
            return len(result["ids"]) if result["ids"] else 0
        except Exception:
            return 0


# Singleton retriever instance
memory_retriever = MemoryRetriever()
