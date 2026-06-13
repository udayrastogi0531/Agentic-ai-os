"""
Uday AI — Auth Routes

Endpoints: register, login, me, update profile.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.security.rate_limiter import RateLimiter
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
    update_user_profile,
)
from app.services.oauth_service import (
    get_google_login_url,
    exchange_code_for_tokens,
    revoke_google_token,
)
from app.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ──────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    dependencies=[Depends(RateLimiter(requests=5, window_seconds=60, name="register"))],
)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Create a new user account and return a JWT token."""
    try:
        return await register_user(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


# ── Login ─────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    dependencies=[Depends(RateLimiter(requests=5, window_seconds=60, name="login"))],
)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate and return a JWT token."""
    try:
        return await authenticate_user(db, data.email, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ── Current User ──────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(user)


# ── Update Profile ────────────────────────────────────────────────────

@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update user profile",
)
async def update_profile(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Update the current user's profile."""
    updated = await update_user_profile(
        db,
        user,
        name=data.name,
        nickname=data.nickname,
        avatar_url=data.avatar_url,
        preferences=data.preferences,
    )
    return UserResponse.model_validate(updated)


# ── Google OAuth ──────────────────────────────────────────────────────

@router.get(
    "/google/login",
    summary="Get Google OAuth authorization URL",
)
async def google_login(
    user: User = Depends(get_current_user),
) -> dict:
    """Generate the Google OAuth URL for the user to authorize."""
    login_url = get_google_login_url(state=str(user.id))
    return {"url": login_url}


@router.get(
    "/google/callback",
    summary="Google OAuth callback endpoint",
)
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Callback from Google authentication flow."""
    from fastapi.responses import RedirectResponse
    import uuid
    try:
        user_uuid = uuid.UUID(state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    try:
        await exchange_code_for_tokens(db, user_uuid, code)
    except Exception as e:
        logger.error(f"Failed to exchange Google OAuth code: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/settings?google_connected=false&error=exchange_failed"
        )

    return RedirectResponse(
        url=f"{settings.frontend_url}/settings?google_connected=true"
    )


@router.post(
    "/google/revoke",
    summary="Revoke Google OAuth tokens",
)
async def google_revoke(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Revoke Google OAuth access/refresh tokens and remove from DB."""
    success = await revoke_google_token(db, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google token found for user",
        )
    return {"status": "success", "message": "Google tokens revoked successfully"}
