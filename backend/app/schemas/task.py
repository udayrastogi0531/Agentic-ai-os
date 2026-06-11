"""
Uday AI — Task Schemas
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────

class TaskCreate(BaseModel):
    """Create a task."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high|urgent)$",
    )
    due_date: date | None = None
    category: str | None = None
    tags: list[str] | None = None


class TaskUpdate(BaseModel):
    """Update a task."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    priority: str | None = Field(
        None,
        pattern="^(low|medium|high|urgent)$",
    )
    status: str | None = Field(
        None,
        pattern="^(todo|in_progress|done|cancelled)$",
    )
    due_date: date | None = None
    category: str | None = None
    tags: list[str] | None = None


# ── Response Schemas ──────────────────────────────────────────────────

class TaskResponse(BaseModel):
    """A single task."""
    id: uuid.UUID
    title: str
    description: str | None = None
    priority: str
    status: str
    due_date: date | None = None
    category: str | None = None
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Task list."""
    tasks: list[TaskResponse]
    total: int
    stats: dict[str, int] | None = None  # {todo: 5, in_progress: 3, done: 10}
