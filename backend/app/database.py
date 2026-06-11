"""
Uday AI — Database Configuration

Async SQLAlchemy engine, session factory, and ChromaDB client.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ══════════════════════════════════════════════════════════════════════
# PostgreSQL — Async SQLAlchemy
# ══════════════════════════════════════════════════════════════════════

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (development only — use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")


async def close_db() -> None:
    """Dispose of the database engine."""
    await engine.dispose()
    logger.info("Database engine disposed.")


# ══════════════════════════════════════════════════════════════════════
# ChromaDB — Vector Database
# ══════════════════════════════════════════════════════════════════════

def get_chroma_client() -> chromadb.ClientAPI:
    """Get a ChromaDB client (persistent local storage)."""
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=not settings.is_production,
        ),
    )


# Pre-defined collection names
CHROMA_COLLECTIONS = {
    "memories": "user_memories",
    "documents": "document_chunks",
    "notes": "note_embeddings",
    "conversations": "conversation_history",
}


def get_or_create_collection(
    client: chromadb.ClientAPI,
    collection_key: str,
) -> chromadb.Collection:
    """Get or create a ChromaDB collection by key."""
    name = CHROMA_COLLECTIONS.get(collection_key, collection_key)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
