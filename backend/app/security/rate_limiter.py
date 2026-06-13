"""
Nidhi — Redis-Backed Sliding Window Rate Limiter
"""

import time
import logging
from fastapi import Request, HTTPException, status
import redis
import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize async Redis client
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


class RateLimiter:
    """Sliding window rate limiter using Redis sorted sets (ZSET)."""

    def __init__(self, requests: int, window_seconds: int, name: str):
        self.requests = requests
        self.window_seconds = window_seconds
        self.name = name

    async def __call__(self, request: Request) -> None:
        # Get client IP
        ip = request.client.host if request.client else "unknown-ip"
        
        # Check if user is authenticated (FastAPI stores it in request.state or we can parse header)
        user_id = None
        user = getattr(request.state, "user", None)
        if user:
            user_id = str(user.id)
        else:
            # Fallback to checking Authorization header if auth dependency was not executed yet
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                from app.services.auth_service import decode_access_token
                payload = decode_access_token(token)
                if payload:
                    user_id = payload.get("sub")

        now = time.time()
        
        # Define keys
        ip_key = f"ratelimit:ip:{ip}:{self.name}"
        user_key = f"ratelimit:user:{user_id}:{self.name}" if user_id else None

        try:
            # 1. IP check
            await self._check_limit(ip_key, self.requests, self.window_seconds, now)
            
            # 2. User check
            if user_key:
                # User-specific limits can be slightly higher/lower, let's enforce same or custom limits
                await self._check_limit(user_key, self.requests, self.window_seconds, now)
                
        except redis.exceptions.RedisError as e:
            logger.warning(f"Redis rate limiter failed (fail-open): {e}")
            return  # Fail-open in case of Redis connection issues

    async def _check_limit(self, key: str, max_requests: int, window: int, now: float) -> None:
        """Enforce sliding window limit in Redis."""
        clear_before = now - window
        
        # Multi-command pipeline for atomic operations
        async with redis_client.pipeline(transaction=True) as pipe:
            # Add current request timestamp
            pipe.zadd(key, {str(now): now})
            # Remove expired requests
            pipe.zremrangebyscore(key, "-inf", clear_before)
            # Count remaining requests in window
            pipe.zcard(key)
            # Set key expiration to clean up unused sets
            pipe.expire(key, window)
            
            results = await pipe.execute()
            
        request_count = results[2]  # ZCARD result
        
        if request_count > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests to endpoint '{self.name}'. Limit is {max_requests} requests per {window}s.",
                    "retry_after": int(window - (now - float(clear_before)))
                }
            )
