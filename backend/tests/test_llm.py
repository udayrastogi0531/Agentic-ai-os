import pytest
from unittest.mock import patch, MagicMock

from app.config import get_settings
from app.llm.provider import get_llm, get_available_providers, settings as provider_settings
from app.llm.router import SmartModelRouter, check_all_providers_health_async, settings as router_settings

settings = get_settings()

@pytest.fixture(autouse=True)
def setup_teardown_settings():
    # Save original settings
    orig_google = settings.google_api_key
    orig_groq = settings.groq_api_key
    orig_ollama = settings.ollama_base_url
    orig_default = settings.default_llm_provider

    yield settings

    # Restore settings
    settings.google_api_key = orig_google
    settings.groq_api_key = orig_groq
    settings.ollama_base_url = orig_ollama
    settings.default_llm_provider = orig_default

    provider_settings.google_api_key = orig_google
    provider_settings.groq_api_key = orig_groq
    provider_settings.ollama_base_url = orig_ollama
    provider_settings.default_llm_provider = orig_default

    router_settings.google_api_key = orig_google
    router_settings.groq_api_key = orig_groq
    router_settings.ollama_base_url = orig_ollama
    router_settings.default_llm_provider = orig_default


def test_classify_query():
    # Simple queries
    assert SmartModelRouter.classify_query("Hello there") == "simple"
    assert SmartModelRouter.classify_query("") == "simple"

    # Privacy queries
    assert SmartModelRouter.classify_query("This is my private data") == "privacy"
    assert SmartModelRouter.classify_query("offline local assistant") == "privacy"

    # Coding queries
    assert SmartModelRouter.classify_query("write a python script to parse json") == "coding"
    assert SmartModelRouter.classify_query("debug javascript reference error") == "coding"

    # Research queries
    assert SmartModelRouter.classify_query("who is the president of France?") == "research"
    assert SmartModelRouter.classify_query("summarize this article about quantum physics") == "research"

    # Reasoning queries
    assert SmartModelRouter.classify_query("why does water boil at 100 degrees?") == "reasoning"
    assert SmartModelRouter.classify_query("solve the mathematical equation x + 5 = 10") == "reasoning"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_health_checks(mock_get):
    # Mock health responses: Ollama up, Groq up, Gemini down
    def side_effect(url, headers=None):
        mock_res = MagicMock()
        if "api/tags" in url:
            mock_res.status_code = 200
        elif "groq.com" in url:
            mock_res.status_code = 200
        elif "generativelanguage.googleapis.com" in url:
            mock_res.status_code = 500
        return mock_res

    mock_get.side_effect = side_effect

    # Mutate settings for test
    router_settings.google_api_key = "test_gemini_key"
    router_settings.groq_api_key = "test_groq_key"
    router_settings.ollama_base_url = "http://localhost:11434"

    health = await check_all_providers_health_async()
    assert health["ollama"] is True
    assert health["groq"] is True
    assert health["gemini"] is False


def test_router_routing_matrix():
    # Force mock health settings
    with patch.object(SmartModelRouter, "is_groq_healthy", return_value=True), \
         patch.object(SmartModelRouter, "is_gemini_healthy", return_value=True), \
         patch.object(SmartModelRouter, "is_ollama_healthy", return_value=True):

        router_settings.google_api_key = "test_gemini_key"
        router_settings.groq_api_key = "test_groq_key"
        router_settings.ollama_base_url = "http://localhost:11434"

        # Simple query -> groq
        provider, model = SmartModelRouter.route("Hello there")
        assert provider == "groq"
        assert model == "llama-3.3-70b-specdec"

        # Coding query -> groq (deepseek)
        provider, model = SmartModelRouter.route("write a python script")
        assert provider == "groq"
        assert model == "deepseek-r1-distill-llama-70b"

        # Reasoning/Research/Long context query -> gemini
        provider, model = SmartModelRouter.route("why does gravity exist?")
        assert provider == "gemini"
        assert model == "gemini-2.0-flash"

        # Privacy -> ollama
        provider, model = SmartModelRouter.route("keep this private please")
        assert provider == "ollama"
        assert model == "qwen2.5:3b"


def test_router_fallback_matrix():
    # Groq down, Gemini up, Ollama up
    with patch.object(SmartModelRouter, "is_groq_healthy", return_value=False), \
         patch.object(SmartModelRouter, "is_gemini_healthy", return_value=True), \
         patch.object(SmartModelRouter, "is_ollama_healthy", return_value=True):

        router_settings.google_api_key = "test_gemini_key"
        router_settings.groq_api_key = "test_groq_key"
        router_settings.ollama_base_url = "http://localhost:11434"

        # Coding query would normally go to Groq (DeepSeek), but Groq is down.
        # Fallback 1 is Gemini
        provider, model = SmartModelRouter.route("write a python script")
        assert provider == "gemini"
        assert model == "gemini-2.0-flash"

    # Groq down, Gemini down, Ollama up
    with patch.object(SmartModelRouter, "is_groq_healthy", return_value=False), \
         patch.object(SmartModelRouter, "is_gemini_healthy", return_value=False), \
         patch.object(SmartModelRouter, "is_ollama_healthy", return_value=True):

        router_settings.google_api_key = "test_gemini_key"
        router_settings.groq_api_key = "test_groq_key"
        router_settings.ollama_base_url = "http://localhost:11434"

        # Simple query would normally go to Groq, but Groq and Gemini are down.
        # Fallback to Ollama
        provider, model = SmartModelRouter.route("Hello there")
        assert provider == "ollama"
        assert model == "qwen2.5:3b"


def test_get_available_providers():
    provider_settings.google_api_key = "test_gemini_key"
    provider_settings.groq_api_key = "test_groq_key"
    
    providers = get_available_providers()
    provider_ids = [p["id"] for p in providers]
    assert "groq" in provider_ids
    assert "gemini" in provider_ids
    assert "ollama" in provider_ids


@patch("app.llm.provider._create_gemini")
@patch("app.llm.provider._create_groq")
@patch("app.llm.provider._create_ollama")
def test_get_llm_factory_and_fallbacks(mock_ollama, mock_groq, mock_gemini):
    mock_gemini.return_value = MagicMock()
    mock_groq.return_value = MagicMock()
    mock_ollama.return_value = MagicMock()

    # Direct provider calls
    get_llm(provider="gemini")
    mock_gemini.assert_called_once()

    get_llm(provider="groq")
    mock_groq.assert_called_once()

    # Test get_llm fallback: Gemini fails, falls back to Groq
    mock_gemini.side_effect = Exception("Gemini API Error")
    provider_settings.google_api_key = "test_gemini_key"
    provider_settings.groq_api_key = "test_groq_key"

    get_llm(provider="gemini")
    # should have attempted Gemini creation, then fallen back to Groq
    assert mock_gemini.call_count == 2
    mock_groq.assert_called()
