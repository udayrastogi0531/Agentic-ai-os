"""
Uday AI — FastAPI Application Entry Point

Creates and configures the FastAPI application with:
- CORS middleware
- Request logging
- Lifespan management (DB init/teardown)
- All API route registration
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.database import init_db, close_db

settings = get_settings()


# ── Logging Setup ─────────────────────────────────────────────────────

def setup_logging() -> None:
    """Configure application logging."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
        ],
    )
    # Suppress noisy loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown logic."""
    logger.info("🚀 Starting Uday AI Backend...")
    logger.info(f"   Environment: {settings.app_env}")
    logger.info(f"   Debug: {settings.debug}")
    logger.info(f"   LLM Provider: {settings.default_llm_provider}")

    # Initialize database
    if not settings.is_production:
        await init_db()
        logger.info("✅ Database initialized (dev mode — tables auto-created)")
    else:
        logger.info("✅ Database connected (production — use Alembic migrations)")

    # Create upload directory
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    # Start background providers health check polling
    import asyncio
    from app.llm.router import check_all_providers_health_async

    async def poll_providers_health():
        while True:
            try:
                await check_all_providers_health_async()
            except Exception as e:
                logger.debug(f"Error polling providers health: {e}")
            await asyncio.sleep(10)

    health_task = asyncio.create_task(poll_providers_health())

    logger.info("✅ Uday AI Backend is ready!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Uday AI Backend...")
    health_task.cancel()
    try:
        await health_task
    except asyncio.CancelledError:
        pass
    await close_db()
    logger.info("👋 Goodbye!")


# ── Application Factory ──────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Startup validation for production secrets
    if settings.is_production:
        missing_secrets = []
        default_secrets = []

        if not settings.secret_key or settings.secret_key == "change-me-in-production":
            default_secrets.append("SECRET_KEY")
        if not settings.jwt_secret_key or settings.jwt_secret_key == "change-me-jwt-secret":
            default_secrets.append("JWT_SECRET_KEY")
        if not settings.google_client_id:
            missing_secrets.append("GOOGLE_CLIENT_ID")
        if not settings.google_client_secret:
            missing_secrets.append("GOOGLE_CLIENT_SECRET")

        if missing_secrets or default_secrets:
            error_msg = (
                "FATAL: Application failed to start due to insecure or missing production secrets.\n"
            )
            if missing_secrets:
                error_msg += f"Missing Secrets: {', '.join(missing_secrets)}\n"
            if default_secrets:
                error_msg += f"Default/Insecure Secrets: {', '.join(default_secrets)}\n"
            error_msg += "Please configure secure values in environment variables."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Uday AI — Personal AI Operating System. "
            "A production-grade AI assistant combining conversational AI, "
            "long-term memory, multi-agent orchestration, RAG, voice, "
            "and productivity integrations."
        ),
        version="1.0.0",
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ── CORS ──────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging Middleware ────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000

        if settings.debug:
            logger.debug(
                f"{request.method} {request.url.path} → "
                f"{response.status_code} ({elapsed:.1f}ms)"
            )

        response.headers["X-Process-Time"] = f"{elapsed:.1f}ms"
        return response

    # ── Register Routes ──────────────────────────────────────────
    _register_routes(app)

    # ── Health Check ─────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": "1.0.0",
            "environment": settings.app_env,
        }

    return app


def _register_routes(app: FastAPI) -> None:
    """Register all API route modules."""
    from app.api.routes import auth, chat, memory, files, tasks, notes, admin, voice
    from app.api.websocket import websocket_chat_handler

    api_prefix = "/api/v1"

    # REST routes
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(chat.router, prefix=api_prefix)
    app.include_router(memory.router, prefix=api_prefix)
    app.include_router(files.router, prefix=api_prefix)
    app.include_router(tasks.router, prefix=api_prefix)
    app.include_router(notes.router, prefix=api_prefix)
    app.include_router(admin.router, prefix=api_prefix)
    app.include_router(voice.router, prefix=api_prefix)

    # WebSocket routes
    @app.websocket("/ws/chat/{conversation_id}")
    async def ws_chat(websocket: WebSocket, conversation_id: str, token: str | None = None):
        from app.security.rate_limiter import RateLimiter
        from fastapi import HTTPException
        try:
            limiter = RateLimiter(requests=5, window_seconds=60, name="websocket")
            await limiter(websocket)
        except HTTPException:
            await websocket.close(code=1008)  # Policy Violation
            return
        await websocket_chat_handler(websocket, conversation_id, token)

    @app.websocket("/ws/chat")
    async def ws_chat_new(websocket: WebSocket, token: str | None = None):
        from app.security.rate_limiter import RateLimiter
        from fastapi import HTTPException
        try:
            limiter = RateLimiter(requests=5, window_seconds=60, name="websocket")
            await limiter(websocket)
        except HTTPException:
            await websocket.close(code=1008)  # Policy Violation
            return
        await websocket_chat_handler(websocket, None, token)

    logger.info(f"✅ All routes registered under {api_prefix}")


# ── App Instance ─────────────────────────────────────────────────────

app = create_app()
