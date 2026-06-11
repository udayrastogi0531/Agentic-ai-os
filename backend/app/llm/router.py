"""
Uday AI — Smart Model Router

Classifies user queries based on complexity, checks model health,
and routes to the optimal LLM provider (Ollama, OpenAI, Gemini)
with automatic fallback and cost/latency optimizations.
"""

from __future__ import annotations

import logging
import httpx
from typing import Literal
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

LLMRouteCategory = Literal["simple", "coding", "research", "reasoning", "long_context"]
LLMProviderType = Literal["ollama", "openai", "gemini"]


class SmartModelRouter:
    """Routes queries to the optimal LLM dynamically with health checks and fallbacks."""

    stats = {
        "categories": {
            "simple": 0,
            "coding": 0,
            "research": 0,
            "reasoning": 0,
            "long_context": 0
        },
        "providers": {
            "ollama": 0,
            "openai": 0,
            "gemini": 0
        },
        "total_requests": 0,
        "fallbacks_triggered": 0
    }

    @staticmethod
    def classify_query(query: str) -> LLMRouteCategory:
        """Classify the user query type based on keywords and length."""
        if not query:
            return "simple"

        query_lower = query.lower()

        # 1. Check for long context
        if len(query.split()) > 1000:
            return "long_context"

        # 2. Coding queries
        coding_keywords = [
            "code", "program", "function", "debug", "compile", "script",
            "python", "javascript", "typescript", "c++", "rust", "java",
            "html", "css", "sql", "syntax", "refactor", "bug", "exception"
        ]
        if any(kw in query_lower for kw in coding_keywords):
            return "coding"

        # 3. Research queries
        research_keywords = [
            "search", "research", "find out", "web search", "latest",
            "news", "sources", "explain", "who is", "what is", "where is",
            "history", "summary", "summarize", "article", "paper"
        ]
        if any(kw in query_lower for kw in research_keywords):
            return "research"

        # 4. Reasoning/Logic queries
        reasoning_keywords = [
            "why", "how", "solve", "math", "logic", "calculate", "prove",
            "reason", "strategy", "plan", "complex", "comparison", "compare"
        ]
        if any(kw in query_lower for kw in reasoning_keywords):
            return "reasoning"

        return "simple"

    @staticmethod
    def is_ollama_healthy() -> bool:
        """Check if local Ollama server is responding (synchronous)."""
        try:
            with httpx.Client(timeout=0.5) as client:
                res = client.get(f"{settings.ollama_base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    @classmethod
    def route(
        cls,
        query: str | None = None
    ) -> tuple[LLMProviderType, str]:
        """
        Select the optimal LLM provider and model name based on query complexity
        and service availability.

        Routing Matrix:
        - Simple Questions -> Local Ollama (Qwen)
        - Coding -> Local/Remote (DeepSeek / Coder)
        - Research / Reasoning / Long Context -> Google Gemini / OpenAI
        - Fallback -> Llama/Ollama Default
        """
        category = cls.classify_query(query or "")
        cls.stats["total_requests"] += 1
        cls.stats["categories"][category] += 1
        logger.info(f"[Model Router] Query categorized as: '{category}'")

        # Check provider configurations
        has_openai = bool(settings.openai_api_key)
        has_gemini = bool(settings.google_api_key)
        ollama_healthy = cls.is_ollama_healthy()

        provider = None
        model = None

        # 1. Long context & reasoning -> Gemini (large context windows / cheap reasoning)
        if category in ("long_context", "reasoning", "research"):
            if has_gemini:
                provider, model = "gemini", settings.gemini_model
            elif has_openai:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "openai", settings.openai_model

        # 2. Coding queries -> DeepSeek / Coder
        elif category == "coding":
            if ollama_healthy:
                provider, model = "ollama", "deepseek-coder:6.7b"
            elif has_openai:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "openai", "gpt-4o-mini"
            elif has_gemini:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "gemini", settings.gemini_model

        # 3. Simple questions or fallback
        elif category == "simple" and ollama_healthy:
            provider, model = "ollama", settings.ollama_default_model

        # Fallbacks if target could not be resolved
        if not provider:
            cls.stats["fallbacks_triggered"] += 1
            if has_gemini:
                provider, model = "gemini", settings.gemini_model
            elif has_openai:
                provider, model = "openai", settings.openai_model
            elif ollama_healthy:
                provider, model = "ollama", settings.ollama_default_model
            else:
                provider, model = "ollama", "llama3.1:8b"

        cls.stats["providers"][provider] += 1
        logger.info(f"[Model Router] Selected provider: '{provider}' model: '{model}'")
        return provider, model
