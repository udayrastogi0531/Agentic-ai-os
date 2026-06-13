"""
Nidhi — Memory Routes

REST endpoints for memory management and semantic search.
"""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.memory import (
    MemoryCreate,
    MemorySearch,
    MemoryResponse,
    MemoryListResponse,
    MemoryStats,
)
from app.memory.manager import MemoryManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memories", tags=["Memory"])


@router.get(
    "",
    response_model=MemoryListResponse,
    summary="List memories",
)
async def list_memories(
    category: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List user's memories with optional category filter."""
    mgr = MemoryManager(db)
    memories, total = await mgr.list_memories(
        user_id=user.id,
        category=category,
        page=page,
        per_page=per_page,
    )

    return MemoryListResponse(
        memories=[MemoryResponse.model_validate(m) for m in memories],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a memory",
)
async def create_memory(
    data: MemoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Manually create a new memory."""
    mgr = MemoryManager(db)
    memory = await mgr.create_memory(
        user_id=user.id,
        content=data.content,
        category=data.category,
        importance=data.importance,
        metadata=data.metadata,
    )
    return MemoryResponse.model_validate(memory)


@router.post(
    "/search",
    response_model=list[MemoryResponse],
    summary="Search memories semantically",
)
async def search_memories(
    data: MemorySearch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Semantic search over memories using natural language."""
    mgr = MemoryManager(db)
    results = await mgr.search_memories(
        user_id=user.id,
        query=data.query,
        category=data.category,
        limit=data.limit,
        min_importance=data.min_importance,
    )

    return [
        MemoryResponse(
            id=uuid.UUID(r["id"]),
            category=r["category"],
            content=r["content"],
            summary=r.get("summary"),
            importance=r["importance"],
            access_count=r.get("access_count", 0),
            created_at=r["created_at"],
            last_accessed=r["created_at"],  # Simplified
            relevance_score=r.get("relevance_score"),
        )
        for r in results
    ]


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
)
async def delete_memory(
    memory_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a specific memory."""
    mgr = MemoryManager(db)
    success = await mgr.delete_memory(memory_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found.",
        )


@router.get(
    "/stats",
    response_model=MemoryStats,
    summary="Get memory statistics",
)
async def get_memory_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get memory statistics for the dashboard."""
    mgr = MemoryManager(db)
    stats = await mgr.get_memory_stats(user.id)
    return MemoryStats(
        total_memories=stats["total_memories"],
        by_category=stats["by_category"],
        avg_importance=stats["avg_importance"],
        most_accessed=[],
    )
