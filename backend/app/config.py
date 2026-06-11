"""
Uday AI — Application Configuration

Centralized settings management using Pydantic Settings.
All values are loaded from environment variables with sensible defaults.
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Project root ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────
    app_name: str = "Uday AI"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # ── Database (PostgreSQL) ─────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://udayai:udayai_password@localhost:5432/udayai_db"
    )

    # ── Redis ─────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── ChromaDB ──────────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_dir: str = str(BASE_DIR / "data" / "chromadb")

    # ── JWT Auth ──────────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # ── LLM Providers ────────────────────────────────────────────────
    default_llm_provider: Literal["ollama", "openai", "gemini"] = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.1:8b"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Google Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ── Embeddings ────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Voice ─────────────────────────────────────────────────────────
    whisper_model: str = "base"
    piper_model_path: str = str(BASE_DIR / "models" / "piper" / "en_US-lessac-medium.onnx")
    wake_word_model: str = "hey_uday"

    # ── Web Search ────────────────────────────────────────────────────
    tavily_api_key: str = ""
    serpapi_api_key: str = ""

    # ── Google APIs ───────────────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── GitHub ────────────────────────────────────────────────────────
    github_token: str = ""

    # ── MCP Servers ───────────────────────────────────────────────────
    mcp_filesystem_enabled: bool = True
    mcp_filesystem_root: str = str(BASE_DIR / "workspace")
    mcp_browser_enabled: bool = True
    mcp_gmail_enabled: bool = False
    mcp_calendar_enabled: bool = False
    mcp_github_enabled: bool = False

    # ── File Upload ───────────────────────────────────────────────────
    max_upload_size_mb: int = 50
    upload_dir: str = str(BASE_DIR / "data" / "uploads")

    # ── Logging ───────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = str(BASE_DIR / "logs" / "udayai.log")

    # ── Computed properties ───────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.is_production:
            return [self.frontend_url]
        return ["*"]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        path = Path(self.log_file).parent
        path.mkdir(parents=True, exist_ok=True)
        return Path(self.log_file)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
