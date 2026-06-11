"""
Uday AI — Memory Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────

class MemoryCreate(BaseModel):
    """Manually create a memory."""
    content: str = Field(..., min_length=1, max_length=5000)
    category: str = Field(
        default="fact",
        pattern="^(preference|goal|fact|event|relationship|habit|skill)$",
    )
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict | None = None


class MemorySearch(BaseModel):
    """Semantic memory search."""
    query: str = Field(..., min_length=1, max_length=1000)
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=50)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)


# ── Response Schemas ──────────────────────────────────────────────────

class MemoryResponse(BaseModel):
    """A single memory."""
    id: uuid.UUID
    category: str
    content: str
    summary: str | None = None
    importance: float
    access_count: int = 0
    metadata: dict | None = None
    created_at: datetime
    last_accessed: datetime
    relevance_score: float | None = None  # From semantic search

    model_config = {"from_attributes": True}


class MemoryListResponse(BaseModel):
    """Paginated memory list."""
    memories: list[MemoryResponse]
    total: int
    page: int = 1
    per_page: int = 20


class MemoryStats(BaseModel):
    """Memory statistics for admin panel."""
    total_memories: int
    by_category: dict[str, int]
    avg_importance: float
    most_accessed: list[MemoryResponse]
