"""
Uday AI — Auth Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ───────────────────────────────────────────────────

class UserRegister(BaseModel):
    """Registration request."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    nickname: str | None = Field(None, max_length=100)


class UserLogin(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Profile update request."""
    name: str | None = Field(None, min_length=2, max_length=255)
    nickname: str | None = Field(None, max_length=100)
    avatar_url: str | None = None
    preferences: dict | None = None


# ── Response Schemas ──────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public user data."""
    id: uuid.UUID
    email: str
    name: str
    nickname: str | None = None
    avatar_url: str | None = None
    preferences: dict | None = None
    is_admin: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthStatus(BaseModel):
    """Auth status check."""
    authenticated: bool
    user: UserResponse | None = None
