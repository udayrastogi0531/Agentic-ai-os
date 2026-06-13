"""
Nidhi AI OS — Jobs API Routes

Job search, saving, matching, application tracking.
Powered by Job Agent + Brave Search.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.job import Job, JobApplication
from app.models.user_profile import UserProfile
from app.agents import job_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


# ── Schemas ──────────────────────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    query: str
    job_type: str = "all"   # all, internship, full-time, remote, freelance
    location: str = "India"
    count: int = 10


class JobSaveRequest(BaseModel):
    title: str
    company: str
    location: str | None = None
    job_type: str = "full-time"
    description: str | None = None
    url: str | None = None
    salary_range: str | None = None
    source: str = "manual"
    tags: list[str] = []


class JDAnalyzeRequest(BaseModel):
    job_description: str


class ResumeMatchRequest(BaseModel):
    job_description: str
    resume_text: str | None = None   # If None, uses stored profile resume


class CoverLetterRequest(BaseModel):
    job_id: str | None = None
    job_description: str | None = None
    company_name: str = ""


class ApplicationStatusUpdate(BaseModel):
    status: str  # saved, applied, screening, interview, offer, rejected, accepted
    notes: str | None = None
    cover_letter: str | None = None
    interview_date: str | None = None


# ── Serializers ──────────────────────────────────────────────────────────

def job_to_dict(job: Job) -> dict:
    return {
        "id": str(job.id),
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "job_type": job.job_type,
        "description": job.description,
        "url": job.url,
        "salary_range": job.salary_range,
        "match_score": job.match_score,
        "match_analysis": job.match_analysis or {},
        "source": job.source,
        "tags": job.tags or [],
        "requirements": job.requirements or [],
        "is_saved": job.is_saved,
        "is_recommended": job.is_recommended,
        "created_at": job.created_at.isoformat(),
        "application": (
            {
                "id": str(job.application.id),
                "status": job.application.status,
                "applied_at": (
                    job.application.applied_at.isoformat()
                    if job.application.applied_at
                    else None
                ),
                "follow_up_date": (
                    job.application.follow_up_date.isoformat()
                    if job.application.follow_up_date
                    else None
                ),
                "interview_date": (
                    job.application.interview_date.isoformat()
                    if job.application.interview_date
                    else None
                ),
                "notes": job.application.notes,
            }
            if job.application
            else None
        ),
    }


async def get_user_profile_dict(db: AsyncSession, user_id: uuid.UUID, user: User) -> dict:
    """Get user profile data for agents."""
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    base = {
        "name": user.name,
        "email": user.email,
        "skills": [],
        "career_goals": [],
        "current_projects": [],
        "github_url": None,
        "linkedin_url": None,
        "portfolio_url": None,
        "university": None,
        "target_roles": [],
        "resume_text": None,
    }

    if profile:
        base.update({
            "skills": profile.skills or [],
            "career_goals": profile.career_goals or [],
            "current_projects": profile.current_projects or [],
            "github_url": profile.github_url,
            "linkedin_url": profile.linkedin_url,
            "portfolio_url": profile.portfolio_url,
            "university": profile.university,
            "target_roles": profile.target_roles or [],
            "resume_text": profile.resume_text,
        })

    return base


# ── Routes ───────────────────────────────────────────────────────────────

@router.get("")
async def list_jobs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List all saved jobs for current user."""
    jobs = await job_agent.get_user_jobs(db, current_user.id)
    return {
        "jobs": [job_to_dict(j) for j in jobs],
        "total": len(jobs),
        "pipeline": {
            "saved": sum(1 for j in jobs if not j.application or j.application.status == "saved"),
            "applied": sum(1 for j in jobs if j.application and j.application.status == "applied"),
            "screening": sum(1 for j in jobs if j.application and j.application.status == "screening"),
            "interview": sum(1 for j in jobs if j.application and j.application.status == "interview"),
            "offer": sum(1 for j in jobs if j.application and j.application.status == "offer"),
        },
    }


@router.post("/search")
async def search_jobs(
    request: JobSearchRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Search for jobs using Brave Search."""
    results = await job_agent.search_jobs(
        query=request.query,
        job_type=request.job_type,
        location=request.location,
        count=request.count,
    )

    # Try to get resume for match scoring
    profile = await get_user_profile_dict(db, current_user.id, current_user)
    resume_text = profile.get("resume_text")
    user_skills = profile.get("skills", [])

    # Score each job against resume if available
    if resume_text and results:
        for job in results[:5]:  # Score top 5 to avoid too many LLM calls
            try:
                match = await job_agent.match_resume(
                    job.get("description", job.get("title", "")),
                    resume_text,
                    user_skills,
                )
                job["match_score"] = match.get("match_score", 0)
                job["match_analysis"] = match
            except Exception:
                job["match_score"] = None

    return {"results": results, "count": len(results), "query": request.query}


@router.post("/analyze")
async def analyze_job_description(
    request: JDAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze a job description to extract requirements and structure."""
    analysis = await job_agent.analyze_jd(request.job_description)
    return analysis


@router.post("/match")
async def match_resume_to_job(
    request: ResumeMatchRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Match user's resume against a job description."""
    profile = await get_user_profile_dict(db, current_user.id, current_user)
    resume_text = request.resume_text or profile.get("resume_text")

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No resume found. Please upload your resume in Profile first.",
        )

    result = await job_agent.match_resume(
        job_description=request.job_description,
        resume_text=resume_text,
        user_skills=profile.get("skills", []),
    )
    return result


@router.post("/save")
async def save_job(
    request: JobSaveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Save a job listing."""
    job = await job_agent.save_job_to_db(db, current_user.id, request.model_dump())
    await db.commit()
    await db.refresh(job)
    return job_to_dict(job)


@router.post("/{job_id}/cover-letter")
async def generate_cover_letter(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a cover letter for a saved job."""
    # Get job
    stmt = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = await get_user_profile_dict(db, current_user.id, current_user)

    cover_letter = await job_agent.generate_cover_letter(
        job_description=job.description or job.title,
        user_profile=profile,
        tone="professional-warm",
    )

    return {"cover_letter": cover_letter, "job_id": str(job_id)}


@router.put("/{job_id}/status")
async def update_application_status(
    job_id: uuid.UUID,
    data: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update job application status (pipeline stage)."""
    # Verify job ownership
    stmt = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    application = await job_agent.update_application_status(
        db=db,
        job_id=job_id,
        user_id=current_user.id,
        status=data.status,
        cover_letter=data.cover_letter,
        notes=data.notes,
    )

    if data.interview_date:
        application.interview_date = datetime.fromisoformat(data.interview_date)

    await db.commit()
    return {"message": "Application status updated", "status": data.status}


@router.delete("/{job_id}")
async def delete_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Remove a saved job."""
    stmt = select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete(job)
    await db.commit()
    return {"message": "Job removed"}
