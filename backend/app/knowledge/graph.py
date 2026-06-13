"""
Nidhi — Knowledge Graph Operations Service
"""

from __future__ import annotations

import uuid
import logging
from typing import Any
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import GraphNode, GraphEdge

logger = logging.getLogger(__name__)


async def add_node(
    db: AsyncSession,
    user_id: uuid.UUID,
    label: str,
    node_type: str,
    properties: dict[str, Any] | None = None
) -> GraphNode:
    """Create a new node in the user's Knowledge Graph."""
    node = GraphNode(
        id=uuid.uuid4(),
        user_id=user_id,
        label=label,
        type=node_type,
        properties=properties or {}
    )
    db.add(node)
    await db.flush() # Flush to assign database states/ids without full commit
    logger.info(f"Created Graph Node: {label} ({node_type})")
    return node


async def add_edge(
    db: AsyncSession,
    source_id: uuid.UUID,
    target_id: uuid.UUID,
    relationship_type: str,
    weight: float = 1.0
) -> GraphEdge:
    """Create a relationship edge between two nodes in the user's Knowledge Graph."""
    edge = GraphEdge(
        id=uuid.uuid4(),
        source_id=source_id,
        target_id=target_id,
        relationship_type=relationship_type,
        weight=weight
    )
    db.add(edge)
    await db.flush()
    logger.info(f"Created Graph Edge: {source_id} -[{relationship_type}]-> {target_id}")
    return edge


async def get_user_graph(
    db: AsyncSession,
    user_id: uuid.UUID
) -> dict[str, list[dict]]:
    """Retrieve all nodes and edges belonging to a user's Knowledge Graph."""
    # Retrieve nodes
    nodes_stmt = select(GraphNode).where(GraphNode.user_id == user_id)
    nodes_result = await db.execute(nodes_stmt)
    nodes = list(nodes_result.scalars().all())

    node_ids = {n.id for n in nodes}
    if not node_ids:
        return {"nodes": [], "edges": []}

    # Retrieve edges connecting these nodes
    edges_stmt = select(GraphEdge).where(
        or_(
            GraphEdge.source_id.in_(node_ids),
            GraphEdge.target_id.in_(node_ids)
        )
    )
    edges_result = await db.execute(edges_stmt)
    edges = list(edges_result.scalars().all())

    return {
        "nodes": [
            {
                "id": str(n.id),
                "label": n.label,
                "type": n.type,
                "properties": n.properties,
                "created_at": n.created_at.isoformat()
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": str(e.id),
                "source_id": str(e.source_id),
                "target_id": str(e.target_id),
                "relationship_type": e.relationship_type,
                "weight": e.weight,
                "created_at": e.created_at.isoformat()
            }
            for e in edges
        ]
    }


async def query_graph_context(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str
) -> str:
    """
    Search the Knowledge Graph for nodes matching the query,
    traverse their relationships, and format a descriptive context block for the LLM.
    """
    if not query:
        return ""

    # Fetch all nodes for the user
    nodes_stmt = select(GraphNode).where(GraphNode.user_id == user_id)
    nodes_result = await db.execute(nodes_stmt)
    nodes = list(nodes_result.scalars().all())

    if not nodes:
        return ""

    # Simple fuzzy search on label and property values
    query_lower = query.lower()
    matched_nodes = []
    for node in nodes:
        # Check label
        if query_lower in node.label.lower() or query_lower in node.type.lower():
            matched_nodes.append(node)
            continue
        # Check properties JSON values
        prop_match = False
        for val in node.properties.values():
            if isinstance(val, str) and query_lower in val.lower():
                prop_match = True
                break
        if prop_match:
            matched_nodes.append(node)

    if not matched_nodes:
        return ""

    matched_ids = {n.id for n in matched_nodes}

    # Fetch all edges connecting to matched nodes to construct the subgraph
    edges_stmt = select(GraphEdge).where(
        or_(
            GraphEdge.source_id.in_(matched_ids),
            GraphEdge.target_id.in_(matched_ids)
        )
    )
    edges_result = await db.execute(edges_stmt)
    edges = list(edges_result.scalars().all())

    # Map nodes by ID for formatting
    node_map = {n.id: n for n in nodes}

    # Formulate structured text context
    context_lines = ["### Knowledge Graph Connections:"]
    
    # 1. Match Node Properties description
    context_lines.append("#### Identified Entities:")
    for node in matched_nodes:
        props = ", ".join(f"{k}: '{v}'" for k, v in node.properties.items())
        props_str = f" ({props})" if props else ""
        context_lines.append(f"- **{node.label}** ({node.type}){props_str}")

    # 2. Match Edge Relations description
    if edges:
        context_lines.append("\n#### Relationships:")
        for edge in edges:
            source = node_map.get(edge.source_id)
            target = node_map.get(edge.target_id)
            if source and target:
                context_lines.append(
                    f"- **{source.label}** ({source.type}) "
                    f"--[{edge.relationship_type}]--> "
                    f"**{target.label}** ({target.type})"
                )

    return "\n".join(context_lines)
