"""
Nidhi — Unified LLM Provider

Factory pattern to create LLM instances from different providers.
Supports Ollama (local), OpenAI, and Google Gemini.
"""

from __future__ import annotations

import logging
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

LLMProviderType = Literal["ollama", "openai", "gemini", "groq"]


def get_llm(
    provider: LLMProviderType | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    streaming: bool = False,
    query: str | None = None,
) -> BaseChatModel:
    """
    Create an LLM instance from the specified provider, with support for
    dynamic model routing and automatic fallbacks.
    """
    # If no specific model/provider requested, use Smart Model Router
    if provider is None and model is None:
        from app.llm.router import SmartModelRouter
        provider, model = SmartModelRouter.route(query)
        logger.info(f"[Model Router] Dynamically routed to: {provider} ({model})")
    else:
        provider = provider or settings.default_llm_provider

    try:
        if provider == "ollama":
            return _create_ollama(model, temperature, max_tokens, streaming)
        elif provider == "openai":
            return _create_openai(model, temperature, max_tokens, streaming)
        elif provider == "gemini":
            return _create_gemini(model, temperature, max_tokens, streaming)
        elif provider == "groq":
            return _create_groq(model, temperature, max_tokens, streaming)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    except Exception as e:
        logger.warning(
            f"[Model Router] Provider '{provider}' creation failed: {e}. "
            "Executing fallback routing..."
        )
        # Fallback sequence: gemini -> groq -> ollama
        if provider == "gemini":
            if settings.groq_api_key:
                logger.info("[Model Router Fallback] Gemini failed, falling back to Groq")
                return _create_groq(None, temperature, max_tokens, streaming)
            else:
                logger.info("[Model Router Fallback] Gemini failed, falling back to Ollama")
                return _create_ollama(None, temperature, max_tokens, streaming)
        elif provider == "groq":
            logger.info("[Model Router Fallback] Groq failed, falling back to Ollama")
            return _create_ollama(None, temperature, max_tokens, streaming)
        elif provider == "openai":
            if settings.groq_api_key:
                logger.info("[Model Router Fallback] OpenAI failed, falling back to Groq")
                return _create_groq(None, temperature, max_tokens, streaming)
            else:
                logger.info("[Model Router Fallback] OpenAI failed, falling back to Ollama")
                return _create_ollama(None, temperature, max_tokens, streaming)
        else:
            # Re-raise original exception if absolute fallback fails
            raise e


def _create_ollama(
    model: str | None,
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> BaseChatModel:
    """Create an Ollama LLM instance."""
    from langchain_ollama import ChatOllama

    model_name = model or settings.ollama_chat_model
    logger.info(f"Creating Ollama LLM: {model_name}")

    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=model_name,
        temperature=temperature,
        num_predict=max_tokens,
        streaming=streaming,
    )


def _create_openai(
    model: str | None,
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> BaseChatModel:
    """Create an OpenAI LLM instance."""
    from langchain_openai import ChatOpenAI

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    model_name = model or settings.openai_model
    logger.info(f"Creating OpenAI LLM: {model_name}")

    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
    )


def _create_gemini(
    model: str | None,
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> BaseChatModel:
    """Create a Google Gemini LLM instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is not set.")

    model_name = model or settings.gemini_model
    logger.info(f"Creating Gemini LLM: {model_name}")

    return ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        model=model_name,
        temperature=temperature,
        max_output_tokens=max_tokens,
        streaming=streaming,
    )


def _create_groq(
    model: str | None,
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> BaseChatModel:
    """Create a Groq LLM instance using ChatOpenAI wrapper."""
    from langchain_openai import ChatOpenAI

    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set.")

    model_name = model or settings.groq_default_model
    logger.info(f"Creating Groq LLM: {model_name}")

    return ChatOpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
    )


def get_available_providers() -> list[dict]:
    """Return a list of available (configured) LLM providers."""
    providers = []

    # Ollama is always "available" if the URL is set
    providers.append({
        "id": "ollama",
        "name": "Ollama (Local)",
        "models": [settings.ollama_chat_model],
        "is_default": settings.default_llm_provider == "ollama",
        "status": "available",
    })

    if settings.groq_api_key:
        providers.append({
            "id": "groq",
            "name": "Groq",
            "models": [settings.groq_default_model, settings.groq_coding_model],
            "is_default": settings.default_llm_provider == "groq",
            "status": "available",
        })

    if settings.google_api_key:
        providers.append({
            "id": "gemini",
            "name": "Google Gemini",
            "models": [settings.gemini_model, "gemini-2.0-flash", "gemini-1.5-pro"],
            "is_default": settings.default_llm_provider == "gemini",
            "status": "available",
        })

    if settings.openai_api_key:
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "models": [settings.openai_model, "gpt-4o", "gpt-4o-mini"],
            "is_default": settings.default_llm_provider == "openai",
            "status": "available",
        })

    return providers
