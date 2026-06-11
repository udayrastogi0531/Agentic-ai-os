"""
Uday AI — Cognitive Memory Consolidation & Knowledge Graph Extraction Engine

Analyzes episodic conversation logs, consolidates long-term facts,
resolves contradictions, and extracts entity-relationship structures for the Knowledge Graph.
"""

from __future__ import annotations

import uuid
import logging
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage

from app.llm.provider import get_llm
from app.memory.manager import MemoryManager
from app.models.conversation import Message
from app.knowledge.graph import add_node, add_edge, get_user_graph

logger = logging.getLogger(__name__)


# ── Structured Output Schemas ──────────────────────────────────────────

class ExtractedMemory(BaseModel):
    fact: str = Field(description="A distinct, concise personal fact or preference about the user")
    category: str = Field(description="Category of the fact: profile, goals, tasks, interests, relations")
    importance: float = Field(description="Estimated importance score from 1.0 (low) to 5.0 (critical)")


class ObsoleteMemory(BaseModel):
    fact_id: str = Field(description="The exact UUID of the existing memory that is contradicted, outdated, or no longer true")
    reason: str = Field(description="Reason why this memory is now obsolete")


class ExtractedNode(BaseModel):
    label: str = Field(description="Name/label of the entity (e.g., 'Agentic OS', 'Sarah', 'Python')")
    type: str = Field(description="Type of node: project, goal, skill, relationship")
    properties: dict[str, str] = Field(default_factory=dict, description="Key-value attributes")


class ExtractedEdge(BaseModel):
    source_label: str = Field(description="Label of the source entity")
    target_label: str = Field(description="Label of the target entity")
    relationship_type: str = Field(description="Type: member_of, works_on, interacts_with, requires")


class ConsolidationResult(BaseModel):
    new_memories: list[ExtractedMemory] = Field(default_factory=list, description="New permanent user facts extracted")
    obsolete_memories: list[ObsoleteMemory] = Field(default_factory=list, description="Existing memories to remove/update")
    new_nodes: list[ExtractedNode] = Field(default_factory=list, description="Knowledge Graph entities to create")
    new_edges: list[ExtractedEdge] = Field(default_factory=list, description="Knowledge Graph relationships to link")


# ── System Prompt ──────────────────────────────────────────────────────

CONSOLIDATION_SYSTEM_PROMPT = """You are the **Memory Consolidation & Knowledge Graph Extraction Agent** for Uday AI, a personal AI Operating System.
Your job is to analyze the recent conversation history between the user and Uday AI, compare it with existing long-term user memories, and extract updates.

Existing User Memories:
{existing_memories}

Analyze the recent messages below and identify:
1. **New Memories**: Long-term personal facts, goals, or preferences (e.g., "User's wife's name is Sarah", "User prefers dark mode UI"). Ignore ephemeral statements like "hello" or transient chat queries.
2. **Obsolete Memories**: Identify if any of the "Existing User Memories" are now contradicted, changed, or obsolete based on the new messages. Return their exact UUID.
3. **Knowledge Graph Entities (Nodes)**: Identify entities mentioned (e.g., Projects, Goals, Skills, Relationships).
4. **Knowledge Graph Links (Edges)**: Identify relationships between these entities (e.g. Project "Uday AI" requires Skill "Python", User knows Relationship "Sarah" (wife)).

Be highly selective. Only extract facts and entities that have long-term relevance.
"""


# ── Engine Core ────────────────────────────────────────────────────────

async def consolidate_conversation_memory(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    last_n_messages: int = 15
) -> dict[str, Any]:
    """
    Examines the recent conversation logs, runs LLM consolidation,
    updates PostgreSQL semantic memory, and populates the Knowledge Graph.
    """
    logger.info(f"[Memory Consolidation] Starting consolidation worker for conversation {conversation_id}...")
    
    # 1. Fetch recent messages
    msg_stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(last_n_messages)
    )
    msg_result = await db.execute(msg_stmt)
    messages = list(reversed(list(msg_result.scalars().all())))
    
    if not messages:
        logger.info("[Memory Consolidation] No messages found to consolidate.")
        return {}

    # Format dialogue log
    dialogue_log = "\n".join(
        f"{'User' if m.role == 'user' else 'Uday AI'}: {m.content}"
        for m in messages
    )

    # 2. Retrieve existing memories
    memory_mgr = MemoryManager(db)
    existing_list, _ = await memory_mgr.list_memories(user_id=user_id, page=1, per_page=50)
    existing_memories_formatted = "\n".join(
        f"- ID: {m.id} | [{m.category}] {m.content}"
        for m in existing_list
    ) if existing_list else "No existing memories."

    # 3. Call structured LLM
    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(ConsolidationResult)
    
    system_content = CONSOLIDATION_SYSTEM_PROMPT.format(
        existing_memories=existing_memories_formatted
    )
    
    try:
        extraction = await structured_llm.ainvoke([
            SystemMessage(content=system_content),
            HumanMessage(content=f"Recent Conversation History:\n{dialogue_log}")
        ])
    except Exception as e:
        logger.error(f"[Memory Consolidation] LLM extraction failed: {e}", exc_info=True)
        return {"error": str(e)}

    results = {
        "memories_created": 0,
        "memories_deleted": 0,
        "nodes_created": 0,
        "edges_created": 0
    }

    # 4. Process obsolete memories (Delete)
    for obs in extraction.obsolete_memories:
        try:
            obs_uuid = uuid.UUID(obs.fact_id)
            deleted = await memory_mgr.delete_memory(memory_id=obs_uuid, user_id=user_id)
            if deleted:
                logger.info(f"[Memory Consolidation] Deleted obsolete memory {obs_uuid}: {obs.reason}")
                results["memories_deleted"] += 1
        except Exception as err:
            logger.warning(f"[Memory Consolidation] Error deleting memory {obs.fact_id}: {err}")

    # 5. Process new memories (Create)
    for new_mem in extraction.new_memories:
        # Avoid duplicate checks with simple substring scan of existing memories
        is_duplicate = any(
            new_mem.fact.lower() in m.content.lower() or m.content.lower() in new_mem.fact.lower()
            for m in existing_list
        )
        if not is_duplicate:
            try:
                await memory_mgr.create_memory(
                    user_id=user_id,
                    content=new_mem.fact,
                    category=new_mem.category,
                    importance=new_mem.importance
                )
                results["memories_created"] += 1
            except Exception as err:
                logger.error(f"[Memory Consolidation] Error creating memory: {err}")

    # 6. Process Knowledge Graph Nodes
    # Fetch user's current graph to prevent duplicate node labels
    current_graph = await get_user_graph(db, user_id)
    existing_nodes = {n["label"].lower(): n["id"] for n in current_graph["nodes"]}
    
    node_label_to_uuid = {}
    
    for node_data in extraction.new_nodes:
        lbl_lower = node_data.label.lower()
        if lbl_lower in existing_nodes:
            node_label_to_uuid[lbl_lower] = uuid.UUID(existing_nodes[lbl_lower])
        else:
            try:
                node = await add_node(
                    db=db,
                    user_id=user_id,
                    label=node_data.label,
                    node_type=node_data.type,
                    properties=node_data.properties
                )
                node_label_to_uuid[lbl_lower] = node.id
                results["nodes_created"] += 1
            except Exception as err:
                logger.error(f"[Memory Consolidation] Error creating graph node: {err}")

    # 7. Process Knowledge Graph Edges
    for edge_data in extraction.new_edges:
        src_lower = edge_data.source_label.lower()
        tgt_lower = edge_data.target_label.lower()
        
        src_uuid = node_label_to_uuid.get(src_lower)
        tgt_uuid = node_label_to_uuid.get(tgt_lower)
        
        # Fallback to current graph nodes if they weren't in node_label_to_uuid
        if not src_uuid and src_lower in existing_nodes:
            src_uuid = uuid.UUID(existing_nodes[src_lower])
        if not tgt_uuid and tgt_lower in existing_nodes:
            tgt_uuid = uuid.UUID(existing_nodes[tgt_lower])
            
        if src_uuid and tgt_uuid:
            try:
                # Add relationship edge
                await add_edge(
                    db=db,
                    source_id=src_uuid,
                    target_id=tgt_uuid,
                    relationship_type=edge_data.relationship_type
                )
                results["edges_created"] += 1
            except Exception as err:
                logger.error(f"[Memory Consolidation] Error creating graph edge: {err}")
        else:
            logger.warning(
                f"[Memory Consolidation] Skip edge: Source '{edge_data.source_label}' or "
                f"Target '{edge_data.target_label}' node not found."
            )

    logger.info(f"[Memory Consolidation] Consolidation completed: {results}")
    return results
