"""
Nidhi — File Schemas (RAG)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────

class FileQuery(BaseModel):
    """Query a document."""
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


# ── Response Schemas ──────────────────────────────────────────────────

class FileResponse(BaseModel):
    """Uploaded file info."""
    id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    """List of uploaded files."""
    files: list[FileResponse]
    total: int


class CitationResponse(BaseModel):
    """A citation from RAG retrieval."""
    document_id: uuid.UUID
    document_name: str
    chunk_index: int
    page_number: int | None = None
    content: str
    relevance_score: float


class FileQueryResponse(BaseModel):
    """Answer to a document question."""
    answer: str
    citations: list[CitationResponse]
    confidence: float
