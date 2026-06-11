"""
Uday AI — Unified LLM Provider

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

LLMProviderType = Literal["ollama", "openai", "gemini"]


def get_llm(
    provider: LLMProviderType | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    streaming: bool = False,
) -> BaseChatModel:
    """
    Create an LLM instance from the specified provider.

    Args:
        provider: LLM provider (ollama, openai, gemini). Defaults to config.
        model: Model name override. Defaults to provider's default.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.
        streaming: Enable streaming output.

    Returns:
        A LangChain ChatModel instance.
    """
    provider = provider or settings.default_llm_provider

    if provider == "ollama":
        return _create_ollama(model, temperature, max_tokens, streaming)
    elif provider == "openai":
        return _create_openai(model, temperature, max_tokens, streaming)
    elif provider == "gemini":
        return _create_gemini(model, temperature, max_tokens, streaming)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _create_ollama(
    model: str | None,
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> BaseChatModel:
    """Create an Ollama LLM instance."""
    from langchain_ollama import ChatOllama

    model_name = model or settings.ollama_default_model
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


def get_available_providers() -> list[dict]:
    """Return a list of available (configured) LLM providers."""
    providers = []

    # Ollama is always "available" if the URL is set
    providers.append({
        "id": "ollama",
        "name": "Ollama (Local)",
        "models": [settings.ollama_default_model],
        "is_default": settings.default_llm_provider == "ollama",
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

    if settings.google_api_key:
        providers.append({
            "id": "gemini",
            "name": "Google Gemini",
            "models": [settings.gemini_model, "gemini-2.0-flash", "gemini-1.5-pro"],
            "is_default": settings.default_llm_provider == "gemini",
            "status": "available",
        })

    return providers
