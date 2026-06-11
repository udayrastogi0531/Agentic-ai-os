"""
Uday AI — Note Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────

class NoteCreate(BaseModel):
    """Create a note."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(default="")
    tags: list[str] | None = None
    category: str | None = None
    is_pinned: bool = False


class NoteUpdate(BaseModel):
    """Update a note."""
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = None
    tags: list[str] | None = None
    category: str | None = None
    is_pinned: bool | None = None


class NoteSearch(BaseModel):
    """Search notes semantically."""
    query: str = Field(..., min_length=1, max_length=1000)
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


# ── Response Schemas ──────────────────────────────────────────────────

class NoteResponse(BaseModel):
    """A single note."""
    id: uuid.UUID
    title: str
    content: str
    tags: list[str] | None = None
    category: str | None = None
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime
    relevance_score: float | None = None  # From semantic search

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Note list."""
    notes: list[NoteResponse]
    total: int
