"""
Uday AI — Note Routes
"""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get("", response_model=NoteListResponse, summary="List notes")
async def list_notes(
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Note).where(Note.user_id == user.id)
    if category:
        stmt = stmt.where(Note.category == category)
    stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc())

    result = await db.execute(stmt)
    notes = list(result.scalars().all())

    return NoteListResponse(
        notes=[NoteResponse.model_validate(n) for n in notes],
        total=len(notes),
    )


@router.post("", response_model=NoteResponse, status_code=201, summary="Create note")
async def create_note(
    data: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    note = Note(
        id=uuid.uuid4(),
        user_id=user.id,
        title=data.title,
        content=data.content,
        tags=data.tags or [],
        category=data.category,
        is_pinned=data.is_pinned,
    )
    db.add(note)
    await db.flush()
    return NoteResponse.model_validate(note)


@router.patch("/{note_id}", response_model=NoteResponse, summary="Update note")
async def update_note(
    note_id: uuid.UUID,
    data: NoteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Note).where(Note.id == note_id, Note.user_id == user.id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    await db.flush()
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", status_code=204, summary="Delete note")
async def delete_note(
    note_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Note).where(Note.id == note_id, Note.user_id == user.id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    await db.delete(note)
    await db.flush()
