"""
Uday AI — RAG Retriever

Retrieves relevant document chunks from ChromaDB for question answering.
"""

from __future__ import annotations

import logging

import chromadb

from app.database import get_chroma_client, get_or_create_collection
from app.memory.embeddings import generate_embedding

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Document retrieval from ChromaDB for RAG Q&A."""

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
            self._collection = get_or_create_collection(self.client, "documents")
        return self._collection

    def store_chunks(
        self,
        chunks: list[dict],
        document_id: str,
        user_id: str,
    ) -> int:
        """
        Store document chunks in ChromaDB.

        Args:
            chunks: List of {id, content, metadata} dicts.
            document_id: Parent document ID.
            user_id: Owner user ID.

        Returns:
            Number of chunks stored.
        """
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        from app.memory.embeddings import generate_embeddings

        contents = [c["content"] for c in chunks]
        batch_embeddings = generate_embeddings(contents)

        for i, chunk in enumerate(chunks):
            chunk_id = chunk["id"]
            ids.append(chunk_id)
            embeddings.append(batch_embeddings[i])
            documents.append(chunk["content"])
            metadatas.append({
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": chunk.get("chunk_index", i),
                "page_number": chunk.get("page_number", 0),
            })

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Stored {len(ids)} chunks for document {document_id}")
        return len(ids)

    def search_chunks(
        self,
        query: str,
        user_id: str,
        document_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search for relevant document chunks.

        Args:
            query: Search query.
            user_id: Filter by user.
            document_id: Optional filter by specific document.
            top_k: Number of results.

        Returns:
            List of matching chunks with relevance scores.
        """
        query_embedding = generate_embedding(query)

        # Build where filter
        where_conditions: dict = {"user_id": user_id}
        if document_id:
            where_conditions = {
                "$and": [
                    {"user_id": user_id},
                    {"document_id": document_id},
                ]
            }

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_conditions,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []

        chunks = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                chunks.append({
                    "id": chunk_id,
                    "content": results["documents"][0][i],
                    "document_id": metadata.get("document_id", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "page_number": metadata.get("page_number"),
                    "relevance_score": round(similarity, 4),
                })

        return chunks

    def delete_document_chunks(self, document_id: str) -> None:
        """Delete all chunks for a document."""
        try:
            # ChromaDB doesn't support delete by metadata easily,
            # so we fetch IDs first
            results = self.collection.get(
                where={"document_id": document_id},
                include=[],
            )
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document chunks: {e}")


# Singleton
rag_retriever = RAGRetriever()
