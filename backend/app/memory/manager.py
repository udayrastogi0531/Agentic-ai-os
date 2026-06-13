"""
Nidhi — Memory Manager

High-level memory lifecycle management:
- Create memories (auto-categorize + embed)
- Retrieve relevant memories for a conversation
- Update importance and access tracking
- Delete memories
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory
from app.memory.embeddings import generate_embedding
from app.memory.retriever import memory_retriever
from app.memory.categorizer import categorize_memory, estimate_importance

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages the full lifecycle of user memories."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_memory(
        self,
        user_id: uuid.UUID,
        content: str,
        category: str | None = None,
        importance: float | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        """
        Create a new memory with auto-categorization and embedding.

        Args:
            user_id: Owner user.
            content: Memory text content.
            category: Optional category override (auto-detected if not provided).
            importance: Optional importance override (auto-estimated if not provided).
            metadata: Additional metadata.

        Returns:
            The created Memory instance.
        """
        # Auto-categorize if not specified
        if category is None:
            category = categorize_memory(content)

        # Auto-estimate importance if not specified
        if importance is None:
            importance = estimate_importance(content)

        memory_id = uuid.uuid4()

        # Create DB record
        memory = Memory(
            id=memory_id,
            user_id=user_id,
            category=category,
            content=content,
            importance=importance,
            metadata_=metadata or {},
            embedding_id=str(memory_id),
        )
        self.db.add(memory)
        await self.db.flush()

        # Store embedding in ChromaDB
        memory_retriever.store_memory(
            memory_id=str(memory_id),
            content=content,
            user_id=str(user_id),
            category=category,
            importance=importance,
            metadata=metadata,
        )

        logger.info(
            f"Created memory [{category}] (importance={importance:.2f}): "
            f"{content[:80]}..."
        )
        return memory

    async def search_memories(
        self,
        user_id: uuid.UUID,
        query: str,
        category: str | None = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> list[dict]:
        """
        Semantic search for memories relevant to a query.

        Returns enriched results with both ChromaDB scores and DB metadata.
        """
        # Semantic search in ChromaDB
        results = memory_retriever.search_memories(
            query=query,
            user_id=str(user_id),
            category=category,
            limit=limit,
            min_importance=min_importance,
        )

        if not results:
            return []

        # Fetch full records from PostgreSQL
        memory_ids = [uuid.UUID(r["id"]) for r in results]
        stmt = select(Memory).where(Memory.id.in_(memory_ids))
        db_result = await self.db.execute(stmt)
        db_memories = {str(m.id): m for m in db_result.scalars().all()}

        # Merge and enrich results
        enriched = []
        for result in results:
            db_memory = db_memories.get(result["id"])
            if db_memory:
                # Update access tracking
                db_memory.access_count += 1
                db_memory.last_accessed = datetime.now(timezone.utc)

                enriched.append({
                    "id": str(db_memory.id),
                    "category": db_memory.category,
                    "content": db_memory.content,
                    "summary": db_memory.summary,
                    "importance": db_memory.importance,
                    "access_count": db_memory.access_count,
                    "created_at": db_memory.created_at.isoformat(),
                    "relevance_score": result["relevance_score"],
                })

        await self.db.flush()
        return enriched

    async def get_context_memories(
        self,
        user_id: uuid.UUID,
        message: str,
        limit: int = 5,
    ) -> str:
        """
        Get a formatted string of relevant memories for LLM context injection.

        This is called before every LLM invocation to provide personality and context.
        """
        memories = await self.search_memories(
            user_id=user_id,
            query=message,
            limit=limit,
            min_importance=0.2,
        )

        if not memories:
            return ""

        lines = ["## Relevant Memories About This User:"]
        for m in memories:
            lines.append(
                f"- [{m['category']}] {m['content']} "
                f"(importance: {m['importance']:.1f}, "
                f"relevance: {m['relevance_score']:.2f})"
            )

        return "\n".join(lines)

    async def list_memories(
        self,
        user_id: uuid.UUID,
        category: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Memory], int]:
        """List memories with pagination."""
        stmt = select(Memory).where(Memory.user_id == user_id)
        count_stmt = select(func.count()).select_from(Memory).where(
            Memory.user_id == user_id
        )

        if category:
            stmt = stmt.where(Memory.category == category)
            count_stmt = count_stmt.where(Memory.category == category)

        # Get total count
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = (
            stmt.order_by(Memory.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        memories = list(result.scalars().all())

        return memories, total

    async def delete_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a memory from both PostgreSQL and ChromaDB."""
        stmt = select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        memory = result.scalar_one_or_none()

        if not memory:
            return False

        # Delete from ChromaDB
        memory_retriever.delete_memory(str(memory_id))

        # Delete from PostgreSQL
        await self.db.delete(memory)
        await self.db.flush()

        logger.info(f"Deleted memory: {memory_id}")
        return True

    async def get_memory_stats(self, user_id: uuid.UUID) -> dict:
        """Get memory statistics for the admin panel."""
        # Total count
        total = (
            await self.db.execute(
                select(func.count())
                .select_from(Memory)
                .where(Memory.user_id == user_id)
            )
        ).scalar() or 0

        # Count by category
        cat_stmt = (
            select(Memory.category, func.count())
            .where(Memory.user_id == user_id)
            .group_by(Memory.category)
        )
        cat_result = await self.db.execute(cat_stmt)
        by_category = {row[0]: row[1] for row in cat_result.all()}

        # Average importance
        avg_imp = (
            await self.db.execute(
                select(func.avg(Memory.importance)).where(
                    Memory.user_id == user_id
                )
            )
        ).scalar() or 0.0

        return {
            "total_memories": total,
            "by_category": by_category,
            "avg_importance": round(float(avg_imp), 2),
        }
