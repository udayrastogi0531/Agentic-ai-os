"""
Uday AI — Google OAuth Service
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user_token import UserToken
from app.security.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)
settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]


def get_google_login_url(state: str | None = None) -> str:
    """Generate the Google OAuth authorization URL."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",  # Force to always get refresh token
    }
    if state:
        params["state"] = state
    query = "&".join(f"{k}={httpx.percent_encode(v)}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_code_for_tokens(
    db: AsyncSession,
    user_id: uuid.UUID,
    code: str,
) -> dict:
    """Exchange authorization code for access and refresh tokens, and store them."""
    payload = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)
        if response.status_code != 200:
            logger.error(f"Failed to exchange Google OAuth code: {response.text}")
            raise ValueError(f"Google OAuth token exchange failed: {response.text}")
        
        token_data = response.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    scopes = token_data.get("scope", "").split(" ")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Store or update the token in the database
    stmt = select(UserToken).where(
        UserToken.user_id == user_id,
        UserToken.service == "google",
    )
    result = await db.execute(stmt)
    user_token = result.scalar_one_or_none()

    if not user_token:
        user_token = UserToken(
            user_id=user_id,
            service="google",
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=encrypt_token(refresh_token) if refresh_token else None,
            expires_at=expires_at,
            scopes=scopes,
        )
        db.add(user_token)
    else:
        user_token.encrypted_access_token = encrypt_token(access_token)
        if refresh_token:
            user_token.encrypted_refresh_token = encrypt_token(refresh_token)
        user_token.expires_at = expires_at
        user_token.scopes = scopes
        user_token.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return token_data


async def get_valid_google_token(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> str | None:
    """Retrieve a valid Google access token, automatically refreshing it if expired."""
    stmt = select(UserToken).where(
        UserToken.user_id == user_id,
        UserToken.service == "google",
    )
    result = await db.execute(stmt)
    user_token = result.scalar_one_or_none()

    if not user_token:
        return None

    # Check if access token is expired or close to expiring (within 1 minute)
    now = datetime.now(timezone.utc)
    if user_token.expires_at and user_token.expires_at <= now + timedelta(minutes=1):
        # We need to refresh
        refresh_token = decrypt_token(user_token.encrypted_refresh_token)
        if not refresh_token:
            logger.warning(f"Google refresh token missing for user {user_id}")
            return None

        # Call Google to refresh
        payload = {
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
            if response.status_code != 200:
                logger.error(f"Failed to refresh Google OAuth token for user {user_id}: {response.text}")
                return None
            
            token_data = response.json()

        new_access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        user_token.encrypted_access_token = encrypt_token(new_access_token)
        if new_refresh_token:
            user_token.encrypted_refresh_token = encrypt_token(new_refresh_token)
        user_token.expires_at = expires_at
        user_token.updated_at = datetime.now(timezone.utc)
        await db.flush()

        return new_access_token

    return decrypt_token(user_token.encrypted_access_token)


async def revoke_google_token(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> bool:
    """Revoke the stored Google tokens and delete the record from database."""
    stmt = select(UserToken).where(
        UserToken.user_id == user_id,
        UserToken.service == "google",
    )
    result = await db.execute(stmt)
    user_token = result.scalar_one_or_none()

    if not user_token:
        return False

    access_token = decrypt_token(user_token.encrypted_access_token)
    refresh_token = decrypt_token(user_token.encrypted_refresh_token)

    # We try revoking refresh token first, then access token
    token_to_revoke = refresh_token or access_token
    if token_to_revoke:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_REVOKE_URL,
                params={"token": token_to_revoke},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code != 200:
                logger.warning(f"Failed to revoke Google token at API endpoint: {response.text}")

    await db.delete(user_token)
    await db.flush()
    return True
