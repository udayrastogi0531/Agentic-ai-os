"""
Nidhi — Chat Routes

REST endpoints for conversations and messages.
Streaming is handled separately via WebSocket.
"""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    MessageResponse,
)
from app.services.chat_service import (
    create_conversation,
    list_conversations,
    get_conversation,
    delete_conversation,
    process_message,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Conversations ─────────────────────────────────────────────────────

@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    summary="List conversations",
)
async def list_user_conversations(
    page: int = 1,
    per_page: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List all conversations for the current user."""
    items, total = await list_conversations(db, user.id, page, per_page)
    return items


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
)
async def create_new_conversation(
    data: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new conversation."""
    conv = await create_conversation(db, user.id, data.title)
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        status=conv.status,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation with messages",
)
async def get_conversation_detail(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a conversation with all its messages."""
    conv = await get_conversation(db, conversation_id, user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return conv


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
)
async def delete_user_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Soft-delete a conversation."""
    success = await delete_conversation(db, conversation_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )


# ── Send Message ──────────────────────────────────────────────────────

@router.post(
    "/send",
    response_model=ChatResponse,
    summary="Send a message (non-streaming)",
)
async def send_message(
    data: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Send a message and receive a complete AI response.

    For streaming responses, use the WebSocket endpoint instead.
    """
    try:
        conversation, user_msg, ai_msg = await process_message(
            db=db,
            user=user,
            conversation_id=data.conversation_id,
            message_text=data.message,
            model_override=data.model_override,
        )

        return ChatResponse(
            message=MessageResponse.model_validate(ai_msg),
            conversation_id=conversation.id,
            agent_actions=[],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Chat processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your message.",
        )
