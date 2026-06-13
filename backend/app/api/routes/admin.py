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
    from app.models.graph import GraphNode, GraphEdge
    from app.llm.router import SmartModelRouter

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

    # Total graph nodes
    total_nodes = (
        await db.execute(select(func.count()).select_from(GraphNode))
    ).scalar() or 0

    # Total graph edges
    total_edges = (
        await db.execute(select(func.count()).select_from(GraphEdge))
    ).scalar() or 0

    # Graph node types distribution
    node_types_res = await db.execute(
        select(GraphNode.type, func.count()).group_by(GraphNode.type)
    )
    node_types = {row[0]: row[1] for row in node_types_res.all() if row[0]}

    # Graph edge relationships distribution
    edge_types_res = await db.execute(
        select(GraphEdge.relationship_type, func.count()).group_by(GraphEdge.relationship_type)
    )
    edge_relationships = {row[0]: row[1] for row in edge_types_res.all() if row[0]}

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
        "knowledge_graph": {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_types": node_types,
            "edge_relationships": edge_relationships
        },
        "model_router_stats": SmartModelRouter.stats
    }


@router.get("/router/stats", summary="Model router stats")
async def get_router_stats(
    user: User = Depends(get_current_admin),
):
    """Retrieve detailed model routing telemetry."""
    from app.llm.router import SmartModelRouter
    return SmartModelRouter.stats

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


@router.get("/metrics", summary="Prometheus metrics telemetry")
async def get_metrics(
    db: AsyncSession = Depends(get_db_session),
):
    """Return system metrics in Prometheus exposition format."""
    import os
    import psutil
    from fastapi.responses import PlainTextResponse
    from app.llm.router import SmartModelRouter
    from app.models.document import Document, DocumentChunk

    # Memory usage
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_percent = process.memory_percent()

    # DB records counts
    total_convs = (await db.execute(select(func.count()).select_from(Conversation))).scalar() or 0
    total_msgs = (await db.execute(select(func.count()).select_from(Message))).scalar() or 0
    total_memories = (await db.execute(select(func.count()).select_from(Memory))).scalar() or 0
    total_docs = (await db.execute(select(func.count()).select_from(Document))).scalar() or 0
    total_chunks = (await db.execute(select(func.count()).select_from(DocumentChunk))).scalar() or 0

    # Agent calls counts
    agent_stats_stmt = select(AgentLog.agent_name, func.count()).group_by(AgentLog.agent_name)
    agent_result = await db.execute(agent_stats_stmt)
    agent_counts = {row[0]: row[1] for row in agent_result.all() if row[0]}

    lines = []

    # System Memory
    lines.append("# HELP udayai_memory_rss_bytes Resident Set Size (RSS) memory usage in bytes")
    lines.append("# TYPE udayai_memory_rss_bytes gauge")
    lines.append(f"udayai_memory_rss_bytes {mem_info.rss}")
    lines.append("# HELP udayai_memory_vms_bytes Virtual Memory Size (VMS) memory usage in bytes")
    lines.append("# TYPE udayai_memory_vms_bytes gauge")
    lines.append(f"udayai_memory_vms_bytes {mem_info.vms}")
    lines.append("# HELP udayai_memory_percent Memory usage percentage of the process")
    lines.append("# TYPE udayai_memory_percent gauge")
    lines.append(f"udayai_memory_percent {mem_percent:.4f}")

    # Model Router
    router_stats = SmartModelRouter.stats
    lines.append("# HELP udayai_router_requests_total Total number of LLM routing requests")
    lines.append("# TYPE udayai_router_requests_total counter")
    lines.append(f"udayai_router_requests_total {router_stats['total_requests']}")
    lines.append("# HELP udayai_router_fallbacks_total Total number of fallbacks triggered in router")
    lines.append("# TYPE udayai_router_fallbacks_total counter")
    lines.append(f"udayai_router_fallbacks_total {router_stats['fallbacks_triggered']}")

    for provider, count in router_stats["providers"].items():
        lines.append(f"udayai_router_provider_requests_total{{provider=\"{provider}\"}} {count}")
    for category, count in router_stats["categories"].items():
        lines.append(f"udayai_router_category_requests_total{{category=\"{category}\"}} {count}")

    # Agent Calls
    lines.append("# HELP udayai_agent_calls_total Total calls per agent type")
    lines.append("# TYPE udayai_agent_calls_total counter")
    for agent, count in agent_counts.items():
        lines.append(f"udayai_agent_calls_total{{agent=\"{agent}\"}} {count}")

    # System Entities
    lines.append("# HELP udayai_conversations_total Total number of conversations")
    lines.append("# TYPE udayai_conversations_total gauge")
    lines.append(f"udayai_conversations_total {total_convs}")
    lines.append("# HELP udayai_messages_total Total number of messages")
    lines.append("# TYPE udayai_messages_total gauge")
    lines.append(f"udayai_messages_total {total_msgs}")
    lines.append("# HELP udayai_memories_total Total number of consolidated memories")
    lines.append("# TYPE udayai_memories_total gauge")
    lines.append(f"udayai_memories_total {total_memories}")

    # RAG Chunks
    lines.append("# HELP udayai_rag_documents_total Total number of documents uploaded")
    lines.append("# TYPE udayai_rag_documents_total gauge")
    lines.append(f"udayai_rag_documents_total {total_docs}")
    lines.append("# HELP udayai_rag_chunks_total Total number of document chunks")
    lines.append("# TYPE udayai_rag_chunks_total gauge")
    lines.append(f"udayai_rag_chunks_total {total_chunks}")

    return PlainTextResponse("\n".join(lines) + "\n")
