"""
Uday AI — Chat Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    """Send a message to the AI."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: uuid.UUID | None = None
    attachments: list[str] | None = None  # File IDs for RAG context
    model_override: str | None = None  # Override default LLM


class ConversationCreate(BaseModel):
    """Create a new conversation."""
    title: str = Field(default="New Conversation", max_length=500)


# ── Response Schemas ──────────────────────────────────────────────────

class MessageResponse(BaseModel):
    """A single message."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    agent_name: str | None = None
    tool_calls: dict | None = None
    citations: dict | None = None
    token_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Conversation metadata."""
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: str | None = None

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """Conversation with all messages."""
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    """Full chat response (non-streaming)."""
    message: MessageResponse
    conversation_id: uuid.UUID
    agent_actions: list[dict[str, Any]] = []


# ── WebSocket Schemas ─────────────────────────────────────────────────

class WSIncoming(BaseModel):
    """WebSocket incoming message."""
    type: str  # message, stop, ping
    content: str | None = None
    metadata: dict | None = None


class WSOutgoing(BaseModel):
    """WebSocket outgoing message."""
    type: str  # token, agent_status, message_complete, error, pong
    content: str | None = None
    agent_name: str | None = None
    metadata: dict | None = None
