# 🧠 Uday AI — Personal AI Operating System

<div align="center">

**An enterprise-grade AI Assistant combining ChatGPT, Jarvis, Perplexity, and a Personal Secretary into one platform.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C?logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://docker.com/)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **Conversational AI** | Natural chat with Hinglish support, Nidhi voice profile |
| 🧠 **Long-Term Memory** | Remembers preferences, goals, facts across sessions |
| 📄 **RAG System** | Upload PDF/DOCX/TXT/Images, ask questions with citations |
| 🔍 **Research Agent** | Web search, multi-source synthesis, report generation |
| 📁 **File Agent** | Search, create, organize files on your system |
| 📅 **Calendar Agent** | Google Calendar integration (events, reminders) |
| 📧 **Gmail Agent** | Read, summarize, draft, send emails |
| 📝 **Notes Agent** | Smart note-taking with semantic search |
| 💻 **Computer Agent** | Automate opening apps (VS Code, Chrome), files, directories, and WhatsApp messages |
| ✅ **Task Agent** | To-do management with daily/weekly planning |
| 💻 **Coding Agent** | Generate, explain, debug code |
| 🌐 **Browser Agent** | Web browsing and information extraction |
| 🎤 **Voice Assistant** | Speech-to-text, text-to-speech, "Hey Nidhi" wake word |
| 🤖 **Multi-Agent System** | 11 specialized agents orchestrated by LangGraph |
| 🔌 **MCP Integration** | Model Context Protocol for extensibility |

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│     Frontend (Next.js 15)       │
│  Dashboard • Chat • Voice • Admin│
├─────────────────────────────────┤
│     API Gateway (FastAPI)        │
│   REST API • WebSocket • Auth    │
├─────────────────────────────────┤
│   Agent Orchestration (LangGraph)│
│  Planner → [11 Specialist Agents]│
├─────────────────────────────────┤
│   Data Layer                     │
│  PostgreSQL • ChromaDB • Redis   │
├─────────────────────────────────┤
│   AI Layer                       │
│  Ollama • OpenAI • Gemini        │
└─────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **PostgreSQL 16+**
- **Docker & Docker Compose** (recommended)
- **Ollama** (for local LLMs)

### Option 1: Docker (Recommended)

```bash
# Clone the repo
cd "Personal AI Assistent(Uday AI)"

# Set up environment
cp docker/.env.example docker/.env
# Edit docker/.env with your API keys

# Start all services
docker compose -f docker/docker-compose.dev.yml up -d

# Pull a local LLM model
docker exec -it udayai-ollama ollama pull llama3.1:8b

# Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Option 2: Manual Setup

```bash
# 1. Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env with your config

# Start backend
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev

# 3. Database
# Make sure PostgreSQL is running
# Create database: udayai_db

# 4. Ollama
ollama serve
ollama pull llama3.1:8b
```

---

## 📁 Project Structure

```
├── frontend/          # Next.js 15 App (TypeScript, Tailwind)
│   ├── src/app/       # App Router pages
│   ├── src/components/# React components
│   ├── src/lib/       # Utilities, API client
│   └── src/hooks/     # Custom React hooks
│
├── backend/           # FastAPI Backend (Python)
│   ├── app/
│   │   ├── agents/    # LangGraph agents (11 agents)
│   │   ├── api/       # REST routes + WebSocket
│   │   ├── llm/       # LLM provider factory
│   │   ├── memory/    # Long-term memory system
│   │   ├── mcp/       # MCP client manager
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── rag/       # RAG pipeline
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── voice/     # Voice pipeline
│   └── alembic/       # Database migrations
│
├── docker/            # Docker Compose configs
└── docs/              # Documentation
```

---

## 🔧 Configuration

All configuration is via environment variables. See `.env.example` for the full list.

### LLM Providers

| Provider | Setup | Model |
|----------|-------|-------|
| **Ollama** (default) | Install Ollama, pull model | llama3.1:8b |
| **OpenAI** | Set `OPENAI_API_KEY` | gpt-4o-mini |
| **Gemini** | Set `GOOGLE_API_KEY` | gemini-2.0-flash |

### Integrations

| Integration | Requires |
|-------------|----------|
| Google Calendar | Google OAuth credentials |
| Gmail | Google OAuth credentials |
| GitHub MCP | Personal access token |
| Web Search | Tavily API key (optional — DuckDuckGo is free) |

---

## 🧪 API Documentation

When running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
POST /api/v1/auth/register  — Register
POST /api/v1/auth/login     — Login
POST /api/v1/chat/send      — Send message
WS   /ws/chat               — Streaming chat
POST /api/v1/files/upload   — Upload document
POST /api/v1/memories/search — Search memories
GET  /api/v1/tasks           — List tasks
GET  /api/v1/admin/analytics — Dashboard stats
```

---

## 🛣️ Development Roadmap

- [x] Phase 1: Foundation (Backend, DB, Auth)
- [x] Phase 2: LLM Layer + Memory + Chat
- [x] Phase 3: Multi-Agent System (LangGraph)
- [x] Phase 4: RAG + MCP
- [x] Phase 5: Frontend Dashboard
- [x] Phase 6: Docker + Deployment
- [x] Phase 7: Voice Pipeline (Whisper + Piper)
- [ ] Phase 8: Real Google Calendar/Gmail Integration (MCP Ready)
- [x] Phase 9: Advanced Autonomous Workflows (Jarvis loops + Safety Gates)
- [ ] Phase 10: Mobile App (React Native)

---

## 📜 License

MIT License — Built with ❤️ by Uday

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Ollama](https://ollama.ai/)
- [ChromaDB](https://www.trychroma.com/)
- [Shadcn UI](https://ui.shadcn.com/)
