"""
Nidhi — Task Routes
"""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse, summary="List tasks")
async def list_tasks(
    status_filter: str | None = None,
    priority: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Task).where(Task.user_id == user.id)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    stmt = stmt.order_by(Task.created_at.desc())

    result = await db.execute(stmt)
    tasks = list(result.scalars().all())

    # Stats
    stats_stmt = (
        select(Task.status, func.count())
        .where(Task.user_id == user.id)
        .group_by(Task.status)
    )
    stats_result = await db.execute(stats_stmt)
    stats = {row[0]: row[1] for row in stats_result.all()}

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=len(tasks),
        stats=stats,
    )


@router.post("", response_model=TaskResponse, status_code=201, summary="Create task")
async def create_task(
    data: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    task = Task(
        id=uuid.uuid4(),
        user_id=user.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        category=data.category,
        tags=data.tags or [],
    )
    db.add(task)
    await db.flush()
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse, summary="Update task")
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.flush()
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=204, summary="Delete task")
async def delete_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Task).where(Task.id == task_id, Task.user_id == user.id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    await db.delete(task)
    await db.flush()
