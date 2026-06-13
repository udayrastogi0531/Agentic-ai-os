"""
Nidhi AI OS — Goals API Routes
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.goal import Goal, Milestone
from app.llm.provider import get_llm

router = APIRouter(prefix="/goals", tags=["goals"])


# ── Schemas ─────────────────────────────────────────────────────────────

class MilestoneCreate(BaseModel):
    title: str
    due_date: str | None = None


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    category: str = "personal"
    target_date: str | None = None
    milestones: list[MilestoneCreate] = []


class MilestoneUpdate(BaseModel):
    id: str
    title: str
    is_completed: bool


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    progress: int | None = None
    status: str | None = None
    target_date: str | None = None
    milestones: list[MilestoneUpdate] | None = None


# ── Helpers ─────────────────────────────────────────────────────────────

def goal_to_dict(goal: Goal) -> dict:
    return {
        "id": str(goal.id),
        "title": goal.title,
        "description": goal.description,
        "category": goal.category,
        "progress": goal.progress,
        "status": goal.status,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "created_at": goal.created_at.isoformat(),
        "updated_at": goal.updated_at.isoformat(),
        "milestones": [
            {
                "id": str(m.id),
                "title": m.title,
                "is_completed": m.is_completed,
                "due_date": m.due_date.isoformat() if m.due_date else None,
            }
            for m in goal.milestones
        ]
    }


# ── Routes ──────────────────────────────────────────────────────────────

@router.get("")
async def get_goals(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all goals for the current user."""
    stmt = (
        select(Goal)
        .where(Goal.user_id == current_user.id)
        .options(selectinload(Goal.milestones))
        .order_by(Goal.created_at.desc())
    )
    res = await db.execute(stmt)
    goals = res.scalars().all()
    return {"goals": [goal_to_dict(g) for g in goals]}


@router.post("")
async def create_goal(
    data: GoalCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new goal along with milestones."""
    target_dt = None
    if data.target_date:
        try:
            target_dt = datetime.fromisoformat(data.target_date)
        except ValueError:
            pass

    goal = Goal(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        category=data.category,
        progress=0,
        status="active",
        target_date=target_dt,
    )
    db.add(goal)

    for m_data in data.milestones:
        due_dt = None
        if m_data.due_date:
            try:
                due_dt = datetime.fromisoformat(m_data.due_date)
            except ValueError:
                pass
        milestone = Milestone(
            id=uuid.uuid4(),
            goal_id=goal.id,
            title=m_data.title,
            is_completed=False,
            due_date=due_dt,
        )
        db.add(milestone)

    await db.commit()
    await db.refresh(goal)

    # Fetch with selectinload to ensure milestones are populated
    stmt = select(Goal).where(Goal.id == goal.id).options(selectinload(Goal.milestones))
    res = await db.execute(stmt)
    goal_loaded = res.scalar_one()

    return goal_to_dict(goal_loaded)


@router.put("/{goal_id}")
async def update_goal(
    goal_id: uuid.UUID,
    data: GoalUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update goal properties and milestone check states."""
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id).options(selectinload(Goal.milestones))
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    if data.title is not None:
        goal.title = data.title
    if data.description is not None:
        goal.description = data.description
    if data.category is not None:
        goal.category = data.category
    if data.status is not None:
        goal.status = data.status
    if data.target_date is not None:
        try:
            goal.target_date = datetime.fromisoformat(data.target_date) if data.target_date else None
        except ValueError:
            pass

    # Update Milestones
    if data.milestones is not None:
        for m_update in data.milestones:
            m_id = uuid.UUID(m_update.id)
            # Find the milestone
            for m in goal.milestones:
                if m.id == m_id:
                    m.is_completed = m_update.is_completed
                    m.title = m_update.title

        # Auto-calculate progress
        if goal.milestones:
            completed = sum(1 for m in goal.milestones if m.is_completed)
            goal.progress = int((completed / len(goal.milestones)) * 100)
        else:
            goal.progress = 0

    if data.progress is not None and data.milestones is None:
        goal.progress = data.progress

    goal.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(goal)
    return goal_to_dict(goal)


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a goal."""
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    await db.delete(goal)
    await db.commit()
    return {"message": "Goal deleted successfully"}


@router.post("/{goal_id}/evaluate")
async def evaluate_goal(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Asks Nidhi to evaluate the goal progress, generate analysis roadmap."""
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id).options(selectinload(Goal.milestones))
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    milestones_str = "\n".join(f"- {m.title} ({'Done' if m.is_completed else 'Pending'})" for m in goal.milestones)

    prompt = f"""You are **Nidhi**, the warm career and goal progress coach.
Analyze the following goal and evaluate progress for Uday:

Goal Title: {goal.title}
Goal Description: {goal.description or 'No description'}
Category: {goal.category}
Current Progress: {goal.progress}% complete
Status: {goal.status}

Milestones:
{milestones_str}

Please generate:
1. A brief Hinglish feedback review (be warm, encouraging, call him by nickname if applicable).
2. Actionable advice on how to clear the pending milestones.
3. Suggest 2-3 specific skills or tech stacks to study to make this goal succeed.

Keep it in markdown format. Let's make it beautiful.
"""
    try:
        llm = get_llm(temperature=0.7)
        response = await llm.ainvoke(prompt)
        return {"evaluation": response.content}
    except Exception as e:
        return {"evaluation": f"Sorry, Nidhi is currently busy analyzing another plan. (Error: {str(e)})"}
