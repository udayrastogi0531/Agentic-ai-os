"""
Nidhi AI OS — Profile API Routes

Manages the extended user profile including personal info,
career goals, skills, social links, and resume.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])


# ── Schemas ─────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    # Personal
    age: int | None = None
    bio: str | None = None
    education: str | None = None
    university: str | None = None
    graduation_year: int | None = None
    location: str | None = None
    # Career
    current_role: str | None = None
    skills: list[str] | None = None
    career_goals: list[dict] | None = None
    dream_companies: list[str] | None = None
    target_roles: list[str] | None = None
    experience_years: float | None = None
    # Social
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    twitter_url: str | None = None
    # Resume
    resume_text: str | None = None
    resume_url: str | None = None
    # Projects
    current_projects: list[dict] | None = None
    # Context
    important_dates: list[dict] | None = None
    friends: list[dict] | None = None
    family: list[dict] | None = None
    # Preferences
    favorite_tech: list[str] | None = None
    favorite_music: str | None = None
    favorite_topics: list[str] | None = None
    learning_goals: list[dict] | None = None
    # Job Hunt
    job_hunt_active: bool | None = None
    preferred_work_type: str | None = None
    expected_salary: str | None = None
    notice_period: str | None = None


class ResumeUpload(BaseModel):
    resume_text: str
    resume_url: str | None = None


# ── Helpers ─────────────────────────────────────────────────────────────

async def get_or_create_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> UserProfile:
    """Get existing profile or create empty one."""
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(
            id=uuid.uuid4(),
            user_id=user_id,
        )
        db.add(profile)
        await db.flush()

    return profile


def profile_to_dict(profile: UserProfile, user: User) -> dict:
    """Serialize profile + user base info to dict."""
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        # From User model
        "name": user.name,
        "nickname": user.nickname,
        "email": user.email,
        "avatar_url": user.avatar_url,
        # Personal
        "age": profile.age,
        "bio": profile.bio,
        "education": profile.education,
        "university": profile.university,
        "graduation_year": profile.graduation_year,
        "location": profile.location,
        # Career
        "current_role": profile.current_role,
        "skills": profile.skills or [],
        "career_goals": profile.career_goals or [],
        "dream_companies": profile.dream_companies or [],
        "target_roles": profile.target_roles or [],
        "experience_years": profile.experience_years,
        # Social
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "portfolio_url": profile.portfolio_url,
        "twitter_url": profile.twitter_url,
        # Resume
        "resume_text": profile.resume_text,
        "resume_url": profile.resume_url,
        "resume_ats_score": profile.resume_ats_score,
        "resume_last_analyzed": (
            profile.resume_last_analyzed.isoformat()
            if profile.resume_last_analyzed
            else None
        ),
        # Projects & Context
        "current_projects": profile.current_projects or [],
        "important_dates": profile.important_dates or [],
        "friends": profile.friends or [],
        "family": profile.family or [],
        # Preferences
        "favorite_tech": profile.favorite_tech or [],
        "favorite_music": profile.favorite_music,
        "favorite_topics": profile.favorite_topics or [],
        "learning_goals": profile.learning_goals or [],
        # Job Hunt
        "job_hunt_active": profile.job_hunt_active,
        "preferred_work_type": profile.preferred_work_type,
        "expected_salary": profile.expected_salary,
        "notice_period": profile.notice_period,
        # Timestamps
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


# ── Routes ───────────────────────────────────────────────────────────────

@router.get("")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's full profile."""
    profile = await get_or_create_profile(db, current_user.id)
    await db.commit()
    return profile_to_dict(profile, current_user)


@router.put("")
async def update_profile(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update profile fields. Only provided fields are updated."""
    profile = await get_or_create_profile(db, current_user.id)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    logger.info(f"Profile updated for user {current_user.id}: {list(update_data.keys())}")
    return profile_to_dict(profile, current_user)


@router.post("/resume")
async def upload_resume(
    data: ResumeUpload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store resume text (and optional URL for PDF stored externally)."""
    profile = await get_or_create_profile(db, current_user.id)

    profile.resume_text = data.resume_text
    if data.resume_url:
        profile.resume_url = data.resume_url

    await db.commit()

    return {
        "message": "Resume stored successfully",
        "character_count": len(data.resume_text),
        "has_url": bool(data.resume_url),
    }


@router.delete("/resume")
async def clear_resume(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear stored resume."""
    profile = await get_or_create_profile(db, current_user.id)
    profile.resume_text = None
    profile.resume_url = None
    profile.resume_ats_score = None
    await db.commit()
    return {"message": "Resume cleared"}
