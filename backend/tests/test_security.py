import pytest
from unittest.mock import patch, MagicMock
from app.agents.computer_agent import run_computer_agent
from app.security.rate_limiter import RateLimiter
from fastapi import Request

@pytest.mark.asyncio
async def test_computer_agent_shell_injection_filter():
    state = {
        "messages": [MagicMock(content="open vscode & echo injection")],
        "approved": True
    }
    res = await run_computer_agent(state)
    assert "Command Execution Blocked" in res["final_response"]

@pytest.mark.asyncio
async def test_computer_agent_path_traversal_filter():
    state = {
        "messages": [MagicMock(content="open folder C:\\Windows\\System32")],
        "approved": True
    }
    res = await run_computer_agent(state)
    assert "Failed to Open Folder" in res["final_response"]

@pytest.mark.asyncio
@patch("app.security.rate_limiter.redis_client.pipeline")
async def test_rate_limiter_redis_error_fail_open(mock_pipeline):
    import redis
    mock_pipeline.side_effect = redis.exceptions.ConnectionError("Redis offline")
    
    limiter = RateLimiter(requests=5, window_seconds=60, name="test_limit")
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "127.0.0.1"
    mock_request.state = MagicMock()
    mock_request.state.user = None
    mock_request.headers = {}
    
    # RateLimiter should complete cleanly without raising HTTPException (fail-open)
    await limiter(mock_request)
