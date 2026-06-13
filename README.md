# 🧠 Nidhi — Personal AI Operating System

<div align="center">

**An enterprise-grade, launch-ready AI Assistant combining conversational agency, smart routing, long-term memory, RAG, and desktop automation into a unified workspace.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.2.9-000000?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.60-1C3C3C?style=for-the-badge&logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=for-the-badge&logo=kubernetes)](https://kubernetes.io/)

</div>

---

## 🚀 System Showcase

**Nidhi AI OS** is a production-grade personal operating system that orchestrates specialized AI agents to solve productivity, engineering, research, and scheduling tasks dynamically. It bridges cloud power (Google Gemini, Groq) with secure local execution (Ollama) through a unified smart model router.

```
                  ┌─────────────────────────────────────────┐
                  │          Next.js 16.2 Frontend          │
                  │   (Dashboard • Chat • Voice • Admin)    │
                  └────────────────────┬────────────────────┘
                                       │ WebSocket / REST
                  ┌────────────────────▼────────────────────┐
                  │            FastAPI Backend              │
                  │       (APIs • WS Handlers • Auth)       │
                  └────────────────────┬────────────────────┘
                                       │ State Orchestration
                  ┌────────────────────▼────────────────────┐
                  │       LangGraph Multi-Agent Engine      │
                  │    Planner ➔ [11 Specialized Nodes]    │
                  └────────────────────┬────────────────────┘
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│   Data Layer    │           │    AI Layer     │           │   MCP Servers   │
│   PostgreSQL    │           │   Ollama Local  │           │   Filesystem    │
│    ChromaDB     │           │   Google Gemini │           │  Web Browser    │
│   Redis Cache   │           │    Groq Cloud   │           │ Gmail/Calendar  │
└─────────────────┘           └─────────────────┘           └─────────────────┘
```

---

## ✨ System Features & Agent Capability

| Component | Functionality | Status |
| :--- | :--- | :--- |
| 💬 **Conversational AI** | Contextual chat with seamless Hinglish support and custom profile voices. | **Verified** |
| 🧠 **Memory Agent** | Syncs preference mapping, user graph relationships, and facts with decay math. | **Verified** |
| 📄 **RAG Agent (Files)** | Upload PDF/DOCX/TXT/Images, chunking with overlap, and source citation tracking. | **Verified** |
| 🔍 **Research Agent** | Multi-source web search synthesis, fact-checking, and report compiling to PDF. | **Verified** |
| 💻 **Coding Agent** | Dynamic code generation, semantic analysis, refactoring, and automated debugger. | **Verified** |
| 🌐 **Browser Agent** | Playwright headless navigation, elements scraping, and click actions. | **Verified** |
| 📧 **Gmail Agent** | Dynamic OAuth token-injected email checking, draft generation, and sending. | **Verified** |
| 📅 **Calendar Agent** | Schedule creation, agenda querying, and weekly calendar syncs. | **Verified** |
| 💻 **Computer Agent** | Open apps (VS Code, Chrome), local workspace folders, and WhatsApp messages. | **Verified** |
| ✅ **Task Agent** | Goal planning, priority checklists, and to-do timeline tracking. | **Verified** |
| 📝 **Notes Agent** | Smart memo creation with vector-supported semantic search. | **Verified** |
| 🤖 **Planner / Evaluator** | LangGraph cyclical execution graph routing with replanner error-handlers. | **Verified** |

---

## ⚙️ Model Routing & Fallbacks

The smart router classifies user requests based on intent and routes tasks to the best-suited model. It ignores casual conversational greetings (e.g. *"How are you doing today?"*) to prevent routing them to heavy reasoning engines.

```
                           [ User Message ]
                                  │
                                  ▼
                        [ Smart Model Router ]
                                  │
        ┌───────────────────┬─────┴─────────────┬───────────────────┐
        ▼                   ▼                   ▼                   ▼
  [ Fast Chat ]         [ Coding ]         [ Reasoning ]     [ Private Tasks ]
      Groq                 Groq               Gemini             Ollama
  llama-3.3-70b        DeepSeek-R1         gemini-2.0-flash     qwen2.5:3b
```

### Fallback Priority Chain
If a primary provider fails health checks, the system automatically falls back along this priority chain:
$$\text{Google Gemini} \longrightarrow \text{Groq} \longrightarrow \text{Local Ollama (qwen2.5:3b)}$$

---

## 📦 Docker & Kubernetes Deployments

### Option 1: Docker Compose (Development Environment)

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and set your API keys:
   ```bash
   cp docker/.env.example docker/.env
   # Edit docker/.env with Google, Groq, and GitHub keys
   ```

2. **Spin Up Containers**:
   Runs PostgreSQL, Redis, ChromaDB, Browserless, Ollama, backend, and frontend:
   ```bash
   docker compose -f docker/docker-compose.dev.yml up -d --build
   ```

3. **Fetch LLM Models**:
   Pull the chat and embedding models to seed your local Ollama instance:
   ```bash
   docker exec -it udayai-ollama ollama pull qwen2.5:3b
   docker exec -it udayai-ollama ollama pull nomic-embed-text
   ```

### Option 2: Kubernetes (Production Orchestration)

1. **Deploy Resources**:
   Deploy the database, vector store, agents, and Ingress routing in the `udayai` namespace:
   ```bash
   kubectl apply -f kubernetes.yaml
   ```

2. **Verify Pod Readiness**:
   ```bash
   kubectl get pods -n udayai
   ```

3. **Ingress Entrypoint**:
   Access the web client at the host `http://udayai.local`.

---

## 🧪 Verification & Development

### Backend Test Suite
We have achieved a **100% pass rate** across all security, routing, and reliability tests:
```bash
# Navigate to backend directory and run tests
cd backend
python -m pytest tests/
```

### Verification Logs Output
```
rootdir: D:\Personal AI Assistent(Nidhi)\backend
plugins: anyio-4.13.0, asyncio-0.25.0
asyncio: mode=Mode.STRICT
collected 19 items

tests\test_llm.py ......                                                 [ 31%]
tests\test_reliability.py ..........                                     [ 84%]
tests\test_security.py ...                                               [100%]

====================== 19 passed, 262 warnings in 54.31s ======================
```

### Frontend Compilation
Verify Next.js compilation, TypeScript types, and linter constraints:
```bash
# Navigate to frontend directory and compile production bundle
cd frontend
npm run build
```

---

## 🛡️ Security Mitigations Included

- **No Shell Injections**: Mitigated in `ComputerAgent` using `shlex.split` arrays instead of running raw user commands through shell string interpreters.
- **Path Traversal Shield**: The `FileAgent` uses `get_secure_path` to strictly contain files and operations inside the isolated user workspace directory.
- **Fail-Open Rate Limiter**: Fixed name scoping issues in Redis rate limiters, allowing transactions to safely bypass limit checks when the Redis cache is offline.
- **No Hardcoded Keys**: Excluded `.env` files from Git tracking. All checked-in manifests (e.g. `kubernetes.yaml`) use secure base64-encoded placeholders.

---

## 📜 License
MIT License — Built with ❤️ by Uday
