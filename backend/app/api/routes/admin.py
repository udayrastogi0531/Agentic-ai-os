"""
Uday AI — Admin Routes

Agent monitoring, logs, and analytics for the admin panel.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.agent_log import AgentLog
from app.models.memory import Memory
from app.models.conversation import Conversation, Message
from app.llm.provider import get_available_providers

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/analytics", summary="Dashboard analytics")
async def get_analytics(
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Get system-wide analytics for the admin dashboard."""
    # Total conversations
    total_convs = (
        await db.execute(select(func.count()).select_from(Conversation))
    ).scalar() or 0

    # Total messages
    total_msgs = (
        await db.execute(select(func.count()).select_from(Message))
    ).scalar() or 0

    # Total memories
    total_memories = (
        await db.execute(select(func.count()).select_from(Memory))
    ).scalar() or 0

    # Agent usage stats
    agent_stats_stmt = (
        select(AgentLog.agent_name, func.count(), func.avg(AgentLog.duration_ms))
        .group_by(AgentLog.agent_name)
    )
    agent_result = await db.execute(agent_stats_stmt)
    agent_stats = [
        {
            "agent": row[0],
            "total_calls": row[1],
            "avg_duration_ms": round(float(row[2] or 0), 1),
        }
        for row in agent_result.all()
    ]

    return {
        "total_conversations": total_convs,
        "total_messages": total_msgs,
        "total_memories": total_memories,
        "agent_stats": agent_stats,
        "llm_providers": get_available_providers(),
    }


@router.get("/logs", summary="Agent execution logs")
async def get_logs(
    agent_name: str | None = None,
    status_filter: str | None = None,
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Get recent agent execution logs."""
    stmt = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)

    if agent_name:
        stmt = stmt.where(AgentLog.agent_name == agent_name)
    if status_filter:
        stmt = stmt.where(AgentLog.status == status_filter)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            "id": str(log.id),
            "agent_name": log.agent_name,
            "action": log.action,
            "status": log.status,
            "duration_ms": log.duration_ms,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/agents", summary="Agent status")
async def get_agent_status(
    user: User = Depends(get_current_admin),
):
    """Get the status of all agents."""
    agents = [
        {"name": "planner", "display_name": "🧠 Planner Agent", "status": "active"},
        {"name": "memory", "display_name": "💾 Memory Agent", "status": "active"},
        {"name": "research", "display_name": "🔍 Research Agent", "status": "active"},
        {"name": "coding", "display_name": "💻 Coding Agent", "status": "active"},
        {"name": "browser", "display_name": "🌐 Browser Agent", "status": "active"},
        {"name": "file", "display_name": "📁 File Agent", "status": "active"},
        {"name": "calendar", "display_name": "📅 Calendar Agent", "status": "pending_setup"},
        {"name": "gmail", "display_name": "📧 Gmail Agent", "status": "pending_setup"},
        {"name": "notes", "display_name": "📝 Notes Agent", "status": "active"},
        {"name": "task", "display_name": "✅ Task Agent", "status": "active"},
    ]
    return {"agents": agents, "total": len(agents)}
