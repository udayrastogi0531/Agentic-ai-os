"""
Uday AI — Smart Model Router

Classifies user queries based on complexity, checks model health,
and routes to the optimal LLM provider (Ollama, OpenAI, Gemini, Groq)
with automatic fallback and cost/latency optimizations.
"""

from __future__ import annotations

import logging
import httpx
from typing import Literal
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

LLMRouteCategory = Literal["simple", "coding", "research", "reasoning", "long_context", "privacy"]
LLMProviderType = Literal["ollama", "openai", "gemini", "groq"]

# Global cache for health status to prevent blocking calls
_OLLAMA_HEALTHY = True
_GEMINI_HEALTHY = True
_GROQ_HEALTHY = True
_LAST_CHECK = 0.0


async def check_all_providers_health_async() -> dict[str, bool]:
    """Asynchronously check health of all LLM providers and update global caches."""
    global _OLLAMA_HEALTHY, _GEMINI_HEALTHY, _GROQ_HEALTHY, _LAST_CHECK
    import time
    import asyncio

    async def check_ollama():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{settings.ollama_base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def check_groq():
        if not settings.groq_api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"}
                )
                return res.status_code == 200
        except Exception:
            return False

    async def check_gemini():
        if not settings.google_api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={settings.google_api_key}"
                )
                return res.status_code == 200
        except Exception:
            return False

    ollama_ok, groq_ok, gemini_ok = await asyncio.gather(
        check_ollama(),
        check_groq(),
        check_gemini(),
        return_exceptions=True
    )

    global _OLLAMA_HEALTHY, _GROQ_HEALTHY, _GEMINI_HEALTHY
    _OLLAMA_HEALTHY = ollama_ok if isinstance(ollama_ok, bool) else False
    _GROQ_HEALTHY = groq_ok if isinstance(groq_ok, bool) else False
    _GEMINI_HEALTHY = gemini_ok if isinstance(gemini_ok, bool) else False
    _LAST_CHECK = time.time()

    return {
        "ollama": _OLLAMA_HEALTHY,
        "groq": _GROQ_HEALTHY,
        "gemini": _GEMINI_HEALTHY
    }


async def check_ollama_health_async() -> bool:
    """Asynchronously check if local Ollama server is responding."""
    res = await check_all_providers_health_async()
    return res.get("ollama", False)


class SmartModelRouter:
    """Routes queries to the optimal LLM dynamically with health checks and fallbacks."""

    stats = {
        "categories": {
            "simple": 0,
            "coding": 0,
            "research": 0,
            "reasoning": 0,
            "long_context": 0,
            "privacy": 0
        },
        "providers": {
            "ollama": 0,
            "openai": 0,
            "gemini": 0,
            "groq": 0
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

        # 0. Check for privacy / local keywords
        privacy_keywords = [
            "private", "local", "privacy", "offline", "confidential", "secret",
            "sensitive", "locally", "my data", "no cloud", "no api"
        ]
        if any(kw in query_lower for kw in privacy_keywords):
            return "privacy"

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
            if "how" in query_lower:
                greeting_phrases = ["how are you", "how's it going", "how is it going", "how's everything", "how do you do", "how have you been", "how's life", "how you doing"]
                if any(gp in query_lower for gp in greeting_phrases) and not any(kw in query_lower for kw in reasoning_keywords if kw != "how"):
                    pass
                else:
                    return "reasoning"
            else:
                return "reasoning"

        return "simple"

    @staticmethod
    def is_ollama_healthy() -> bool:
        """Return the cached health status of local Ollama server (non-blocking)."""
        global _OLLAMA_HEALTHY
        return _OLLAMA_HEALTHY

    @staticmethod
    def is_gemini_healthy() -> bool:
        """Return the cached health status of Gemini server (non-blocking)."""
        global _GEMINI_HEALTHY
        return _GEMINI_HEALTHY

    @staticmethod
    def is_groq_healthy() -> bool:
        """Return the cached health status of Groq server (non-blocking)."""
        global _GROQ_HEALTHY
        return _GROQ_HEALTHY

    @classmethod
    def route(
        cls,
        query: str | None = None
    ) -> tuple[LLMProviderType, str]:
        """
        Select the optimal LLM provider and model name based on query complexity
        and service availability.

        Routing Matrix:
        - Simple / Fast Chat -> Groq (llama-3.3-70b-specdec)
        - Coding -> DeepSeek (deepseek-r1-distill-llama-70b via Groq)
        - Reasoning / Research / Long Context -> Google Gemini (gemini-2.0-flash)
        - Local Privacy Tasks -> Local Ollama (qwen2.5:3b)
        - Fallback Chain -> Gemini -> Groq -> Ollama
        """
        category = cls.classify_query(query or "")
        cls.stats["total_requests"] += 1
        if category not in cls.stats["categories"]:
            cls.stats["categories"][category] = 0
        cls.stats["categories"][category] += 1
        logger.info(f"[Model Router] Query categorized as: '{category}'")

        # Check provider configurations and live health checks
        has_gemini = bool(settings.google_api_key)
        has_groq = bool(settings.groq_api_key)
        has_ollama = bool(settings.ollama_base_url)

        gemini_healthy = has_gemini and cls.is_gemini_healthy()
        groq_healthy = has_groq and cls.is_groq_healthy()
        ollama_healthy = has_ollama and cls.is_ollama_healthy()

        provider = None
        model = None

        # 1. Routing Rules by Category
        if category == "privacy":
            if ollama_healthy:
                provider, model = "ollama", settings.ollama_chat_model
            else:
                cls.stats["fallbacks_triggered"] += 1
                if gemini_healthy:
                    provider, model = "gemini", settings.gemini_model
                elif groq_healthy:
                    provider, model = "groq", settings.groq_default_model
                else:
                    provider, model = "ollama", settings.ollama_chat_model

        elif category in ("reasoning", "research", "long_context"):
            if gemini_healthy:
                provider, model = "gemini", settings.gemini_model
            elif groq_healthy:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "groq", settings.groq_default_model
            elif ollama_healthy:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "ollama", settings.ollama_chat_model
            else:
                cls.stats["fallbacks_triggered"] += 1
                if has_gemini:
                    provider, model = "gemini", settings.gemini_model
                elif has_groq:
                    provider, model = "groq", settings.groq_default_model
                else:
                    provider, model = "ollama", settings.ollama_chat_model

        elif category == "coding":
            if groq_healthy:
                provider, model = "groq", settings.groq_coding_model
            elif gemini_healthy:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "gemini", settings.gemini_model
            elif ollama_healthy:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "ollama", settings.ollama_chat_model
            else:
                cls.stats["fallbacks_triggered"] += 1
                if has_groq:
                    provider, model = "groq", settings.groq_coding_model
                elif has_gemini:
                    provider, model = "gemini", settings.gemini_model
                else:
                    provider, model = "ollama", settings.ollama_chat_model

        else:  # simple / fast chat
            if groq_healthy:
                provider, model = "groq", settings.groq_default_model
            elif gemini_healthy:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "gemini", settings.gemini_model
            elif ollama_healthy:
                cls.stats["fallbacks_triggered"] += 1
                provider, model = "ollama", settings.ollama_chat_model
            else:
                cls.stats["fallbacks_triggered"] += 1
                if has_groq:
                    provider, model = "groq", settings.groq_default_model
                elif has_gemini:
                    provider, model = "gemini", settings.gemini_model
                else:
                    provider, model = "ollama", settings.ollama_chat_model

        # Ensure provider statistics are tracked safely
        if provider not in cls.stats["providers"]:
            cls.stats["providers"][provider] = 0
        cls.stats["providers"][provider] += 1

        logger.info(f"[Model Router] Selected provider: '{provider}' model: '{model}'")
        return provider, model
