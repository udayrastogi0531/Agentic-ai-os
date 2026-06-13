"""
Nidhi — File Routes (RAG)

Upload, list, delete, and query documents.
"""

from __future__ import annotations

import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.security.rate_limiter import RateLimiter
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.file import (
    FileResponse,
    FileListResponse,
    FileQuery,
    FileQueryResponse,
    CitationResponse,
)
from app.rag.ingest import ingest_file, SUPPORTED_TYPES
from app.rag.chunker import chunk_document
from app.rag.retriever import rag_retriever
from app.rag.citation import format_citations, format_citation_response
from app.llm.provider import get_llm

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/files", tags=["Files / RAG"])


@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for RAG",
    dependencies=[Depends(RateLimiter(requests=10, window_seconds=3600, name="upload"))],
)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Upload a file (PDF, DOCX, TXT, Image) for RAG question answering."""
    # Validate file type
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Supported: {list(SUPPORTED_TYPES.keys())}",
        )

    # Save file by streaming in chunks
    doc_id = uuid.uuid4()
    filename = f"{doc_id}{suffix}"
    upload_dir = settings.upload_path / str(user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename

    max_size = settings.max_upload_size_mb * 1024 * 1024
    total_bytes = 0

    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(65536)  # 64KB chunk
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_size:
                    buffer.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Max: {settings.max_upload_size_mb}MB",
                    )
                buffer.write(chunk)
                
                # Log progress every 1MB
                if (total_bytes // (1024 * 1024)) > ((total_bytes - len(chunk)) // (1024 * 1024)):
                    logger.info(f"Uploading {file.filename}: {total_bytes / (1024 * 1024):.1f}MB written")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        file_path.unlink(missing_ok=True)
        logger.error(f"Stream upload failed for {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )

    # Create DB record
    document = Document(
        id=doc_id,
        user_id=user.id,
        filename=filename,
        original_filename=file.filename or "unknown",
        file_type=SUPPORTED_TYPES[suffix],
        file_size=total_bytes,
        storage_path=str(file_path),
        status="processing",
    )
    db.add(document)
    await db.flush()

    # Process document
    try:
        file_type, pages = await ingest_file(file_path, file.filename or "")
        chunks = chunk_document(pages)

        # Store chunks in DB and ChromaDB
        chunk_dicts = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            db_chunk = DocumentChunk(
                id=uuid.UUID(chunk_id),
                document_id=doc_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                embedding_id=chunk_id,
                metadata_=chunk.metadata,
            )
            db.add(db_chunk)
            chunk_dicts.append({
                "id": chunk_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
            })

        # Store embeddings in ChromaDB
        rag_retriever.store_chunks(
            chunks=chunk_dicts,
            document_id=str(doc_id),
            user_id=str(user.id),
        )

        document.chunk_count = len(chunks)
        document.status = "ready"
        await db.flush()

        logger.info(f"Document processed: {file.filename} → {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        # Clean up physical file on failure to prevent disk leaks
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        document.status = "error"
        document.metadata_ = {"error": str(e)}
        await db.flush()

    return FileResponse.model_validate(document)


@router.get(
    "",
    response_model=FileListResponse,
    summary="List uploaded files",
)
async def list_files(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List all uploaded documents."""
    stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    docs = list(result.scalars().all())

    return FileListResponse(
        files=[FileResponse.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file",
)
async def delete_file(
    file_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a file and its chunks."""
    stmt = select(Document).where(
        Document.id == file_id,
        Document.user_id == user.id,
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="File not found.")

    # Delete from ChromaDB
    rag_retriever.delete_document_chunks(str(file_id))

    # Delete physical file
    try:
        Path(document.storage_path).unlink(missing_ok=True)
    except Exception:
        pass
    # Delete from DB (cascade deletes chunks)
    await db.delete(document)
    await db.flush()


@router.get(
    "/{file_id}/download",
    summary="Download a file",
)
async def download_file(
    file_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Download a file's physical content."""
    stmt = select(Document).where(
        Document.id == file_id,
        Document.user_id == user.id,
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="File not found.")

    file_path = Path(document.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical file is missing.")

    from fastapi.responses import FileResponse as FastAPIFileResponse
    return FastAPIFileResponse(
        path=str(file_path),
        filename=document.original_filename,
        media_type="application/octet-stream"
    )


@router.post(
    "/{file_id}/query",
    response_model=FileQueryResponse,
    summary="Query a document",
)
async def query_file(
    file_id: uuid.UUID,
    data: FileQuery,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Ask a question about an uploaded document."""
    # Verify document exists
    stmt = select(Document).where(
        Document.id == file_id,
        Document.user_id == user.id,
        Document.status == "ready",
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found or still processing.")

    # Search for relevant chunks with hybrid and re-ranking pipeline
    from app.rag.hybrid import combine_dense_and_sparse
    from app.rag.reranker import rerank_chunks

    # Retrieve more candidates from vector search to re-rank
    candidates = rag_retriever.search_chunks(
        query=data.question,
        user_id=str(user.id),
        document_id=str(file_id),
        top_k=data.top_k * 4,
    )

    # Perform hybrid combine
    hybrid_candidates = combine_dense_and_sparse(candidates, data.question)

    # Perform Cross-Encoder re-ranking
    chunks = rerank_chunks(data.question, hybrid_candidates, top_k=data.top_k)

    if not chunks:
        return FileQueryResponse(
            answer="I couldn't find relevant information in this document.",
            citations=[],
            confidence=0.0,
        )

    # Format context and citations
    doc_names = {str(file_id): document.original_filename}
    context, citations = format_citations(chunks, doc_names)

    # Generate answer with LLM
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = get_llm(temperature=0.2)
    messages = [
        SystemMessage(content=(
            "You are a document Q&A assistant. Answer the question based ONLY on the "
            "provided document context. If the answer is not in the context, say so. "
            "Cite sources using [Source N] format."
        )),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {data.question}"),
    ]

    response = await llm.ainvoke(messages)
    answer = response.content + format_citation_response(citations)

    avg_relevance = sum(c.relevance_score for c in citations) / len(citations) if citations else 0

    return FileQueryResponse(
        answer=answer,
        citations=[
            CitationResponse(
                document_id=uuid.UUID(c.document_id),
                document_name=c.document_name,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                content=c.content_snippet,
                relevance_score=c.relevance_score,
            )
            for c in citations
        ],
        confidence=avg_relevance,
    )
