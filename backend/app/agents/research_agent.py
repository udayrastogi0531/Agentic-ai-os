"""
Nidhi — Research Agent

Web search, multi-source research, source comparison, fact verification, and report generation.
Generates Markdown, PDF, and Structured JSON reports, saving them to the user's isolated workspace.
"""

from __future__ import annotations

import re
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

RESEARCH_PROMPT = """You are a Principal Research Analyst for Nidhi AI OS.
Your objective is to analyze the search queries and search results to synthesize a comprehensive, well-structured, and highly objective research dossier.

You MUST structure your report strictly matching this format:

# Research Dossier: [Insert Topic Title]

## 1. Executive Summary
Provide a concise overview of the findings and current consensus.

## 2. Detailed Analysis
Elaborate on the key themes and findings. Ensure clear headings and logical transitions.

## 3. Source Comparison Matrix
Analyze and compare what different sources claim. Detail alignments and contradictions:
- [Source title/URL] asserts: [Key claims]
- Detail where sources agree or diverge.

## 4. Fact Verification Check
Examine the validity of assertions:
- Fact: [Verified assertion] -> Confidence: [High/Medium/Low] -> Source: [Title/URL reference]
- Assumption: [Unverified assertion/claim] -> Confidence: [Low] -> Risk: [Reasoning]

## 5. Key Takeaways & Actionable Recommendations
Provide high-level takeaways and actionable guidelines.
"""


async def run_research_agent(state: AgentState) -> dict:
    """Run the research agent to perform search, comparison, verification, and file report generation."""
    messages = state.get("messages", [])
    latest = messages[-1].content if messages else ""
    user_id = state.get("user_id")

    logger.info(f"Research agent processing query: {latest[:80]}")

    # 1. Perform web search
    search_results = await _web_search(latest)

    # 2. Synthesize structured markdown research report
    response = await _synthesize_research(latest, search_results)

    # 3. Save report files and index in RAG
    if user_id:
        try:
            user_folder = Path(settings.upload_path) / str(user_id)
            user_folder.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # A. Save Markdown report
            md_filename = f"research_report_{timestamp}.md"
            md_path = user_folder / md_filename
            md_path.write_text(response, encoding="utf-8")
            await index_file_in_db_and_rag(user_id, md_path, md_filename, "txt")
            
            # B. Save PDF report
            pdf_filename = f"research_report_{timestamp}.pdf"
            pdf_path = user_folder / pdf_filename
            create_pdf_report(latest, response, search_results, pdf_path)
            await index_file_in_db_and_rag(user_id, pdf_path, pdf_filename, "pdf")
            
            # C. Save Structured JSON report
            json_filename = f"research_report_{timestamp}.json"
            json_path = user_folder / json_filename
            structured_data = {
                "topic": latest,
                "timestamp": datetime.now().isoformat(),
                "report_content": response,
                "sources": search_results
            }
            json_path.write_text(json.dumps(structured_data, indent=2), encoding="utf-8")
            await index_file_in_db_and_rag(user_id, json_path, json_filename, "txt")
            
            response = (
                f"{response}\n\n"
                f"📥 **Research Reports Generated & Indexed:**\n"
                f"- **Markdown Dossier**: `{md_filename}`\n"
                f"- **PDF Print Report**: `{pdf_filename}`\n"
                f"- **Structured JSON data**: `{json_filename}`\n"
                f"These reports have been fully saved and indexed into your RAG file base."
            )
        except Exception as e:
            logger.error(f"[Research Agent] Failed to generate/save report files: {e}", exc_info=True)

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "research_agent": {
                "response": response,
                "sources": search_results,
            },
        },
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }


async def _web_search(query: str) -> list[dict]:
    """Perform web search using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })

        logger.info(f"Web search returned {len(results)} results for: {query[:50]}")
        return results

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


async def _synthesize_research(query: str, results: list[dict]) -> str:
    """Synthesize search results into a coherent structured response."""
    llm = get_llm(temperature=0.3)

    sources_text = "\n\n".join(
        f"**{r['title']}** ({r['url']})\n{r['snippet']}"
        for r in results
    ) if results else "No web search results available."

    messages = [
        SystemMessage(content=RESEARCH_PROMPT),
        HumanMessage(content=f"""Research Topic/Query: {query}

Search Results Content:
{sources_text}

Analyze the query and search results to generate a comprehensive structured research dossier. Provide fact verification and source comparison details as requested."""),
    ]

    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Research synthesis failed: {e}")
        return f"I found some results but had trouble synthesizing them. Here are the raw sources:\n\n{sources_text}"


def create_pdf_report(topic: str, content: str, sources: list[dict], file_path: Path):
    """Generate a clean, professional PDF report from the markdown synthesis."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(str(file_path), pagesize=letter)
        story = []
        
        styles = getSampleStyleSheet()
        
        # Custom styles for research reports
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Heading3'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#718096"),
            spaceAfter=25
        )
        
        h2_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2C5282"),
            spaceBefore=15,
            spaceAfter=8
        )
        
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['BodyText'],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#2D3748"),
            spaceAfter=8
        )
        
        source_style = ParagraphStyle(
            'SourceStyle',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#4A5568")
        )

        story.append(Paragraph(f"Research Dossier: {topic[:100]}", title_style))
        story.append(Paragraph(f"Generated by Nidhi Operating System on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Process and append content lines
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue
                
            if line.startswith("# "):
                story.append(Paragraph(line[2:], title_style))
            elif line.startswith("## "):
                story.append(Paragraph(line[3:], h2_style))
            elif line.startswith("### ") or line.startswith("#### "):
                story.append(Paragraph(line[line.find(" ")+1:], h2_style))
            elif line.startswith("- ") or line.startswith("* "):
                cleaned = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line[2:])
                story.append(Paragraph(f"• {cleaned}", body_style))
            else:
                cleaned = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                story.append(Paragraph(cleaned, body_style))
                
        story.append(Spacer(1, 15))
        story.append(Paragraph("References & Sources", h2_style))
        story.append(Spacer(1, 8))
        
        # Append references
        for idx, src in enumerate(sources, start=1):
            source_text = f"<b>[{idx}] {src['title']}</b><br/>URL: <font color='blue'>{src['url']}</font><br/>{src['snippet']}"
            story.append(Paragraph(source_text, source_style))
            story.append(Spacer(1, 8))
            
        doc.build(story)
        logger.info(f"PDF research report created successfully at {file_path}")
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}", exc_info=True)


async def index_file_in_db_and_rag(user_id: str, file_path: Path, original_filename: str, file_type: str):
    """Index the generated report file into the PostgreSQL DB and ChromaDB vector store."""
    from app.database import async_session_factory
    from app.models.document import Document, DocumentChunk
    from app.rag.ingest import ingest_file
    from app.rag.chunker import chunk_document
    from app.rag.retriever import rag_retriever

    try:
        user_uuid = uuid.UUID(user_id)
        doc_id = uuid.uuid4()
        filename = file_path.name
        file_size = file_path.stat().st_size
        
        async with async_session_factory() as db:
            # Create Document record
            document = Document(
                id=doc_id,
                user_id=user_uuid,
                filename=filename,
                original_filename=original_filename,
                file_type=file_type,
                file_size=file_size,
                storage_path=str(file_path),
                status="processing",
            )
            db.add(document)
            await db.flush()
            
            # Ingest content
            file_type_ingested, pages = await ingest_file(file_path, original_filename)
            chunks = chunk_document(pages)
            
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
            
            # Index chunks in ChromaDB RAG Vector Store
            rag_retriever.store_chunks(
                chunks=chunk_dicts,
                document_id=str(doc_id),
                user_id=user_id,
            )
            
            document.chunk_count = len(chunks)
            document.status = "ready"
            await db.commit()
            
            logger.info(f"Indexed research file: {original_filename} ({len(chunks)} chunks)")
    except Exception as e:
        logger.error(f"Failed to index generated research file {original_filename} in DB/RAG: {e}", exc_info=True)
