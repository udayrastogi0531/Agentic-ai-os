import pytest
import uuid
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.state import AgentState
from app.llm.router import SmartModelRouter
from app.knowledge.graph import add_node, add_edge, get_user_graph, query_graph_context
from app.memory.manager import MemoryManager
from app.rag.chunker import chunk_document
from app.rag.retriever import RAGRetriever
from app.voice.stt import transcribe_audio
from app.voice.tts import synthesize_speech
from app.agents.gmail_agent import run_gmail_agent
from app.agents.calendar_agent import run_calendar_agent
from app.agents.github_agent import run_github_agent
from app.agents.browser_agent import run_browser_agent
from app.agents.computer_agent import run_computer_agent


@pytest.fixture
def mock_db_session():
    db = MagicMock()
    # Mock execute as an AsyncMock to allow awaiting it
    async def mock_execute(*args, **kwargs):
        mock_res = MagicMock()
        return mock_res
    async def mock_flush(*args, **kwargs):
        pass
    db.execute = mock_execute
    db.flush = mock_flush
    db.commit = mock_flush
    return db


# ── 1. Chat Conversation Router Test ───────────────────────────────────
def test_chat_conversation_routing():
    with patch.object(SmartModelRouter, "is_groq_healthy", return_value=True), \
         patch.object(SmartModelRouter, "is_gemini_healthy", return_value=True), \
         patch.object(SmartModelRouter, "is_ollama_healthy", return_value=True):
        
        # Verify that the model router correctly routes chat categories
        assert SmartModelRouter.classify_query("Hello! How are you today?") == "simple"
        provider, model = SmartModelRouter.route("Hello! How are you today?")
        assert provider in ["ollama", "gemini", "groq"]


# ── 2. Memory System Test ──────────────────────────────────────────────
@pytest.mark.asyncio
@patch("app.memory.manager.memory_retriever")
async def test_memory_recall(mock_retriever, mock_db_session):
    user_id = uuid.uuid4()
    memory_text = "Uday likes black coffee"
    
    # Instantiate the MemoryManager
    manager = MemoryManager(mock_db_session)
    
    with patch("app.memory.manager.generate_embedding", return_value=[0.1]*384):
        try:
            await manager.create_memory(
                user_id=user_id,
                content=memory_text,
                category="preferences",
                importance=0.8
            )
            success = True
        except Exception as e:
            print(f"Memory create failed: {e}")
            success = False
        assert success is True


# ── 3. PDF Upload & RAG Ingestion Test ────────────────────────────────
def test_pdf_chunking():
    test_text = "This is page 1.\n" * 100
    chunks = chunk_document(pages=[test_text], chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 0
    assert all(len(c.content) <= 250 for c in chunks)


# ── 4. Gmail Agent Execution Test ─────────────────────────────────────
@pytest.mark.asyncio
async def test_gmail_agent_execution():
    state: AgentState = {
        "messages": [HumanMessage(content="Send email to John about the project details")],
        "user_id": str(uuid.uuid4()),
        "agent_results": {}
    }
    
    # Mocking MCP token fetch & execution
    with patch("app.database.async_session_factory"), \
         patch("app.services.oauth_service.get_valid_google_token", return_value="mock_token"), \
         patch("app.mcp.client.MCPClientManager.call_tool", return_value="Email sent successfully!"):
        
        result = await run_gmail_agent(state)
        assert "final_response" in result
        assert " John" in result["final_response"] or "email" in result["final_response"].lower()


# ── 5. Calendar Agent Execution Test ──────────────────────────────────
@pytest.mark.asyncio
async def test_calendar_agent_execution():
    state: AgentState = {
        "messages": [HumanMessage(content="Create meeting tomorrow at 3pm")],
        "user_id": str(uuid.uuid4()),
        "agent_results": {}
    }
    
    with patch("app.database.async_session_factory"), \
         patch("app.services.oauth_service.get_valid_google_token", return_value="mock_token"), \
         patch("app.mcp.client.MCPClientManager.call_tool", return_value="Event created successfully!"):
        
        result = await run_calendar_agent(state)
        assert "final_response" in result


# ── 6. GitHub Agent Execution Test ────────────────────────────────────
@pytest.mark.asyncio
async def test_github_agent_execution():
    state: AgentState = {
        "messages": [HumanMessage(content="Create issue 'bug: button alignment' in udayai repo")],
        "user_id": str(uuid.uuid4()),
        "agent_results": {}
    }
    
    with patch("app.mcp.client.MCPClientManager.call_tool", return_value="GitHub Issue created successfully!"):
        result = await run_github_agent(state)
        assert "final_response" in result


# ── 7. Browser Agent Execution Test ───────────────────────────────────
@pytest.mark.asyncio
async def test_browser_search():
    # Inject mock playwright package into sys.modules to prevent ModuleNotFoundError on the host
    mock_p_module = MagicMock()
    sys.modules["playwright"] = mock_p_module
    sys.modules["playwright.async_api"] = mock_p_module

    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    mock_page.content.return_value = "<html><body>Search Results</body></html>"
    mock_page.title.return_value = "Mock Search"
    mock_context.new_page.return_value = mock_page
    mock_browser.contexts = [mock_context]
    mock_p.chromium.connect_over_cdp.return_value = mock_browser
    
    mock_p_module.async_playwright.return_value.__aenter__.return_value = mock_p
    
    state: AgentState = {
        "messages": [HumanMessage(content="search for OpenAI internship positions")],
        "user_id": str(uuid.uuid4()),
        "agent_results": {}
    }
    
    # Running agent
    result = await run_browser_agent(state)
    assert "final_response" in result


# ── 8. WhatsApp Message Execution Test ────────────────────────────────
@pytest.mark.asyncio
async def test_whatsapp_agent_interception():
    state: AgentState = {
        "messages": [HumanMessage(content="whatsapp message to Shubham hi")],
        "user_id": str(uuid.uuid4()),
        "approved": False,
        "agent_results": {}
    }
    
    # Should trigger safety approval gateway interception
    result = await run_computer_agent(state)
    assert result.get("approval_required") is True
    assert "WhatsApp" in result.get("final_response")


# ── 9. Voice Assistant STT / TTS Test ─────────────────────────────────
@pytest.mark.asyncio
@patch("app.voice.stt._get_whisper_model")
async def test_voice_stt_tts_fallback(mock_get_whisper):
    # Mock whisper model returning segments to prevent HuggingFace request connection timeout
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "Hello Uday"
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    mock_get_whisper.return_value = mock_model

    transcription = await transcribe_audio(b"fake_audio_bytes")
    assert "Hello Uday" in transcription
    
    # 1. Test Edge TTS Success Path
    async def mock_stream():
        yield {"type": "audio", "data": b"mock_edge_tts_audio"}

    mock_communicate = MagicMock()
    mock_communicate.stream = mock_stream

    with patch("edge_tts.Communicate", return_value=mock_communicate):
        audio = await synthesize_speech("Hello Uday!")
        assert audio == b"mock_edge_tts_audio"

    # 2. Test Fallback Path (Edge TTS fails -> Piper is missing -> returns None)
    with patch("edge_tts.Communicate", side_effect=Exception("Edge TTS failed")):
        audio_fallback = await synthesize_speech("Hello Uday!")
        assert audio_fallback is None


# ── 10. Knowledge Graph Retrieval Test ────────────────────────────────
@pytest.mark.asyncio
async def test_knowledge_graph_retrieval(mock_db_session):
    user_id = uuid.uuid4()
    
    # Mock database retrieval query returning nodes and edges
    mock_node = MagicMock()
    mock_node.id = uuid.uuid4()
    mock_node.label = "Alice"
    mock_node.type = "person"
    mock_node.properties = {"age": "25"}

    mock_node_bob = MagicMock()
    mock_node_bob.id = uuid.uuid4()
    mock_node_bob.label = "Bob"
    mock_node_bob.type = "person"
    mock_node_bob.properties = {}
    
    mock_edge = MagicMock()
    mock_edge.id = uuid.uuid4()
    mock_edge.source_id = mock_node.id
    mock_edge.target_id = mock_node_bob.id
    mock_edge.relationship_type = "friend"
    mock_edge.weight = 1.0
    
    # Define an async execute function to return the correct mock result objects when awaited
    async def mock_execute_graph(*args, **kwargs):
        # Determine whether nodes or edges query is executed by string inspection
        query_str = str(args[0]) if args else ""
        mock_res = MagicMock()
        if "node" in query_str.lower():
            mock_res.scalars.return_value.all.return_value = [mock_node, mock_node_bob]
        else:
            mock_res.scalars.return_value.all.return_value = [mock_edge]
        return mock_res
        
    mock_db_session.execute = mock_execute_graph
    
    graph_context = await query_graph_context(mock_db_session, user_id, "Alice")
    assert "Alice" in graph_context
    assert "friend" in graph_context
