"""
Nidhi AI OS — Resume API Routes

Resume analysis, improvement, ATS scoring, cover letter,
LinkedIn summary, and portfolio content generation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.user_profile import UserProfile
from app.agents import resume_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["resume"])


# ── Schemas ──────────────────────────────────────────────────────────────

class ResumeAnalyzeRequest(BaseModel):
    resume_text: str | None = None   # If None, uses stored profile resume
    target_role: str | None = None


class ResumeImproveRequest(BaseModel):
    resume_text: str | None = None
    target_role: str = "AI/ML Engineer"
    job_description: str | None = None


class CoverLetterRequest(BaseModel):
    job_description: str
    company_name: str = ""
    resume_text: str | None = None


class LinkedInRequest(BaseModel):
    additional_context: str | None = None


class PortfolioRequest(BaseModel):
    projects: list[dict] | None = None  # If None, uses profile projects


# ── Helpers ──────────────────────────────────────────────────────────────

async def get_profile_and_resume(
    db: AsyncSession,
    user: User,
    provided_resume: str | None = None,
) -> tuple[UserProfile | None, str | None]:
    """Get profile and resolve resume text."""
    stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    resume_text = provided_resume
    if not resume_text and profile:
        resume_text = profile.resume_text

    return profile, resume_text


def profile_to_agent_dict(profile: UserProfile | None, user: User) -> dict:
    """Convert profile to dict for agents."""
    base = {
        "name": user.name,
        "email": user.email,
        "skills": [],
        "career_goals": [],
        "current_projects": [],
        "target_roles": [],
        "github_url": None,
        "linkedin_url": None,
        "university": None,
    }
    if profile:
        base.update({
            "skills": profile.skills or [],
            "career_goals": profile.career_goals or [],
            "current_projects": profile.current_projects or [],
            "target_roles": profile.target_roles or [],
            "github_url": profile.github_url,
            "linkedin_url": profile.linkedin_url,
            "university": profile.university,
            "graduation_year": profile.graduation_year,
        })
    return base


# ── Routes ───────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_resume(
    request: ResumeAnalyzeRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze resume and return ATS score, strengths, weaknesses, and improvements.
    If no resume_text provided, uses the stored profile resume.
    """
    profile, resume_text = await get_profile_and_resume(
        db, current_user, request.resume_text
    )

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No resume found. Please upload your resume in Profile or provide resume_text.",
        )

    analysis = await resume_agent.analyze_resume(
        resume_text=resume_text,
        target_role=request.target_role,
    )

    # Update ATS score in profile if using stored resume
    if not request.resume_text and profile:
        profile.resume_ats_score = analysis.get("ats_score")
        profile.resume_last_analyzed = datetime.now(timezone.utc)
        await db.commit()

    return analysis


@router.post("/improve")
async def improve_resume(
    request: ResumeImproveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an improved version of the resume.
    """
    profile, resume_text = await get_profile_and_resume(
        db, current_user, request.resume_text
    )

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No resume found. Please upload your resume first.",
        )

    improved = await resume_agent.improve_resume(
        resume_text=resume_text,
        target_role=request.target_role,
        job_description=request.job_description,
    )

    return {
        "improved_resume": improved,
        "target_role": request.target_role,
        "original_length": len(resume_text),
        "improved_length": len(improved),
    }


@router.post("/generate")
async def generate_ats_resume(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a complete ATS-optimized resume from the user's stored profile.
    """
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    profile_dict = profile_to_agent_dict(profile, current_user)
    profile_dict["email"] = current_user.email

    generated = await resume_agent.generate_ats_resume(profile_dict)

    return {
        "generated_resume": generated,
        "note": "Review and personalize before submitting. Never submit AI content without review.",
    }


@router.post("/cover-letter")
async def generate_cover_letter(
    request: CoverLetterRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a personalized cover letter for a job."""
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    profile_dict = profile_to_agent_dict(profile, current_user)

    cover_letter = await resume_agent.generate_cover_letter(
        user_profile=profile_dict,
        job_description=request.job_description,
        company_name=request.company_name,
    )

    return {
        "cover_letter": cover_letter,
        "company": request.company_name,
        "word_count": len(cover_letter.split()),
    }


@router.post("/linkedin")
async def generate_linkedin_summary(
    request: LinkedInRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a LinkedIn About section."""
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    profile_dict = profile_to_agent_dict(profile, current_user)
    if request.additional_context:
        profile_dict["additional_context"] = request.additional_context

    summary = await resume_agent.generate_linkedin_summary(profile_dict)

    return {"linkedin_summary": summary, "word_count": len(summary.split())}


@router.post("/portfolio")
async def generate_portfolio_content(
    request: PortfolioRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate polished portfolio content for projects."""
    projects = request.projects

    if not projects:
        stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile:
            projects = profile.current_projects or []

    if not projects:
        raise HTTPException(
            status_code=400,
            detail="No projects found. Add projects to your profile or provide them in request.",
        )

    content = await resume_agent.generate_portfolio_content(projects)
    return {"portfolio": content, "project_count": len(content)}


@router.get("/ats-score")
async def get_ats_score(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get the last computed ATS score for the stored resume."""
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile or not profile.resume_ats_score:
        return {
            "ats_score": None,
            "message": "No ATS score yet. Analyze your resume first at POST /resume/analyze",
        }

    return {
        "ats_score": profile.resume_ats_score,
        "last_analyzed": (
            profile.resume_last_analyzed.isoformat()
            if profile.resume_last_analyzed
            else None
        ),
        "has_resume": bool(profile.resume_text),
    }
