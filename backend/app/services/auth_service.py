"""
Nidhi — Authentication Service

Handles password hashing, JWT token creation/validation,
and user registration/login logic.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.schemas.auth import UserRegister, TokenResponse, UserResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Password Hashing ─────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    email: str,
    is_admin: bool = False,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "is_admin": is_admin,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None


# ── User Operations ──────────────────────────────────────────────────

async def register_user(
    db: AsyncSession,
    data: UserRegister,
) -> TokenResponse:
    """Register a new user and return a JWT token."""
    # Check if email already exists
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise ValueError("A user with this email already exists.")

    # Create user
    user = User(
        id=uuid.uuid4(),
        email=data.email,
        name=data.name,
        nickname=data.nickname,
        hashed_password=hash_password(data.password),
        preferences={
            "language": "en",
            "theme": "dark",
            "llm_provider": "ollama",
            "personality": "friendly",
        },
    )
    db.add(user)
    await db.flush()

    # Generate token
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        is_admin=user.is_admin,
    )

    logger.info(f"User registered: {user.email}")

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> TokenResponse:
    """Authenticate a user and return a JWT token."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password.")

    if not user.is_active:
        raise ValueError("Account is deactivated.")

    # Generate token
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        is_admin=user.is_admin,
    )

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    """Get a user by ID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_user_profile(
    db: AsyncSession,
    user: User,
    name: str | None = None,
    nickname: str | None = None,
    avatar_url: str | None = None,
    preferences: dict | None = None,
) -> User:
    """Update user profile fields."""
    if name is not None:
        user.name = name
    if nickname is not None:
        user.nickname = nickname
    if avatar_url is not None:
        user.avatar_url = avatar_url
    if preferences is not None:
        user.preferences = {**(user.preferences or {}), **preferences}
    await db.flush()
    return user
