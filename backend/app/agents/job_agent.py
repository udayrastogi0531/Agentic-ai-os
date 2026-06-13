"""
Nidhi AI OS — Job Agent

Searches for jobs, analyzes job descriptions, matches resume to JD,
generates cover letters, and tracks applications.

Uses: Brave Search API + Gemini/Groq for analysis.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.llm.provider import get_llm
from app.models.job import Job, JobApplication

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Job Search ──────────────────────────────────────────────────────────

async def search_jobs(
    query: str,
    job_type: str = "all",
    location: str = "India",
    count: int = 10,
) -> list[dict]:
    """
    Search for jobs using Brave Search API.
    Returns structured job listings.
    """
    search_query = f"{query} {job_type} jobs {location} site:linkedin.com OR site:naukri.com OR site:internshala.com OR site:indeed.com"
    if job_type == "internship":
        search_query = f"{query} internship 2024 2025 {location}"
    elif job_type == "remote":
        search_query = f"{query} remote job work from home"
    elif job_type == "freelance":
        search_query = f"{query} freelance project contract"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={
                    "q": search_query,
                    "count": min(count, 20),
                    "search_lang": "en",
                    "country": "IN",
                },
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": settings.brave_api_key or "",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("web", {}).get("results", [])
        jobs = []
        for r in results:
            title = r.get("title", "Unknown Role")
            url = r.get("url", "")
            description = r.get("description", "")
            company = _extract_company_from_url(url) or "Unknown Company"

            jobs.append({
                "title": title,
                "company": company,
                "url": url,
                "description": description,
                "location": location,
                "job_type": job_type,
                "source": "brave_search",
                "tags": _extract_tags_from_description(description),
            })

        return jobs

    except Exception as e:
        logger.error(f"Job search failed: {e}")
        # Return mock data as fallback
        return _get_mock_jobs(query, job_type)


def _extract_company_from_url(url: str) -> str | None:
    """Try to extract company name from job URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").replace(".com", "").replace(".in", "")
        if "linkedin" in domain:
            return None  # LinkedIn jobs have company in title
        return domain.title()
    except Exception:
        return None


def _extract_tags_from_description(description: str) -> list[str]:
    """Quick keyword extraction for job tags."""
    tech_keywords = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI",
        "Django", "Machine Learning", "AI", "LLM", "LangChain", "LangGraph",
        "TensorFlow", "PyTorch", "SQL", "PostgreSQL", "MongoDB", "Redis",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Git", "REST API",
        "GraphQL", "Next.js", "Vue.js", "Flutter", "Golang", "Rust", "Java",
        "Generative AI", "GPT", "NLP", "Computer Vision", "Data Science",
    ]
    found = []
    desc_lower = description.lower()
    for kw in tech_keywords:
        if kw.lower() in desc_lower:
            found.append(kw)
    return found[:8]


def _get_mock_jobs(query: str, job_type: str) -> list[dict]:
    """Fallback mock jobs when API unavailable."""
    return [
        {
            "title": f"{query} Engineer",
            "company": "OpenAI",
            "location": "Remote",
            "job_type": job_type,
            "description": f"Looking for a talented {query} engineer to join our team.",
            "url": "https://openai.com/careers",
            "source": "mock",
            "tags": ["Python", "Machine Learning", "LLMs"],
        },
        {
            "title": f"Junior {query} Developer",
            "company": "Google DeepMind",
            "location": "India",
            "job_type": job_type,
            "description": f"Entry level {query} position at Google DeepMind India.",
            "url": "https://careers.google.com",
            "source": "mock",
            "tags": ["Python", "TensorFlow", "AI"],
        },
        {
            "title": f"{query} Intern",
            "company": "Microsoft",
            "location": "Hyderabad",
            "job_type": "internship",
            "description": f"6-month internship in {query} at Microsoft India.",
            "url": "https://careers.microsoft.com",
            "source": "mock",
            "tags": ["Python", "Azure", "Machine Learning"],
        },
    ]


# ── Job Description Analysis ────────────────────────────────────────────

async def analyze_jd(job_description: str) -> dict:
    """
    Analyze a job description using LLM.
    Returns structured requirements, skills, culture fit indicators.
    """
    llm = get_llm("fast")
    prompt = f"""Analyze this job description and extract structured information.

JOB DESCRIPTION:
{job_description[:3000]}

Return ONLY valid JSON with this exact structure:
{{
  "role": "extracted role title",
  "company": "company name if mentioned",
  "required_skills": ["skill1", "skill2"],
  "nice_to_have": ["skill1", "skill2"],
  "experience_required": "0-2 years / 2-5 years / 5+ years",
  "responsibilities": ["responsibility 1", "responsibility 2"],
  "perks": ["perk 1", "perk 2"],
  "culture_signals": ["fast-paced", "collaborative", "startup"],
  "ats_keywords": ["keyword1", "keyword2"],
  "summary": "2 sentence summary of the role"
}}"""

    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        # Strip markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        logger.error(f"JD analysis failed: {e}")
        return {
            "role": "Unknown",
            "required_skills": [],
            "summary": job_description[:200],
            "ats_keywords": [],
        }


# ── Resume Match Scoring ────────────────────────────────────────────────

async def match_resume(
    job_description: str,
    resume_text: str,
    user_skills: list[str] | None = None,
) -> dict:
    """
    Match a resume against a job description.
    Returns score (0-100) and detailed gap analysis.
    """
    llm = get_llm("reasoning")
    skills_context = f"User's known skills: {', '.join(user_skills)}" if user_skills else ""

    prompt = f"""You are an expert ATS (Applicant Tracking System) and career coach.

Match this resume against the job description and provide detailed analysis.

JOB DESCRIPTION:
{job_description[:2000]}

RESUME:
{resume_text[:2000]}

{skills_context}

Return ONLY valid JSON:
{{
  "match_score": 75,
  "verdict": "Strong Match / Good Match / Partial Match / Weak Match",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "gaps": ["missing skill 1", "missing skill 2"],
  "recommendations": ["Add X to resume", "Highlight Y experience"],
  "ats_score": 68,
  "keywords_present": ["keyword1", "keyword2"],
  "keywords_missing": ["keyword3", "keyword4"],
  "summary": "One paragraph assessment"
}}"""

    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        logger.error(f"Resume match failed: {e}")
        return {
            "match_score": 0,
            "verdict": "Could not analyze",
            "strengths": [],
            "gaps": ["Could not analyze — please try again"],
            "summary": str(e),
        }


# ── Cover Letter Generator ──────────────────────────────────────────────

async def generate_cover_letter(
    job_description: str,
    user_profile: dict,
    tone: str = "professional-warm",
) -> str:
    """
    Generate a personalized cover letter for a job application.
    """
    llm = get_llm("reasoning")

    name = user_profile.get("name", "Uday")
    skills = ", ".join(user_profile.get("skills", [])[:10])
    goals = user_profile.get("career_goals", "become an AI engineer")
    projects = user_profile.get("current_projects", [])
    project_str = "; ".join([p.get("name", "") for p in projects[:3]]) if projects else "various AI projects"
    university = user_profile.get("university", "")
    github = user_profile.get("github_url", "")

    prompt = f"""Write a compelling, personalized cover letter for this job application.

APPLICANT: {name}
SKILLS: {skills}
UNIVERSITY: {university}
KEY PROJECTS: {project_str}
CAREER GOALS: {goals}
GITHUB: {github}

JOB DESCRIPTION:
{job_description[:2000]}

Instructions:
- Tone: {tone} (professional but warm, not robotic)
- Length: 250-350 words
- Mention 2-3 specific skills/projects that match the JD
- Show genuine enthusiasm for the company/role
- End with a confident call to action
- Do NOT use clichés like "I am writing to express my interest"
- Sound like a real, passionate person

Write only the cover letter, no subject line or metadata."""

    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        return f"Dear Hiring Manager,\n\nI am excited to apply for this position...\n\n[Generation failed: {e}]"


# ── Database Operations ─────────────────────────────────────────────────

async def save_job_to_db(
    db: AsyncSession,
    user_id: uuid.UUID,
    job_data: dict,
) -> Job:
    """Save a job listing to the database."""
    job = Job(
        id=uuid.uuid4(),
        user_id=user_id,
        title=job_data.get("title", "Unknown"),
        company=job_data.get("company", "Unknown"),
        location=job_data.get("location"),
        job_type=job_data.get("job_type", "full-time"),
        description=job_data.get("description"),
        url=job_data.get("url"),
        salary_range=job_data.get("salary_range"),
        match_score=job_data.get("match_score"),
        match_analysis=job_data.get("match_analysis"),
        source=job_data.get("source", "manual"),
        tags=job_data.get("tags", []),
        requirements=job_data.get("requirements", []),
    )
    db.add(job)
    await db.flush()
    return job


async def get_user_jobs(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Job]:
    """Get all saved jobs for a user."""
    stmt = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_application_status(
    db: AsyncSession,
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    status: str,
    cover_letter: str | None = None,
    notes: str | None = None,
) -> JobApplication:
    """Create or update a job application."""
    stmt = select(JobApplication).where(
        JobApplication.job_id == job_id,
        JobApplication.user_id == user_id,
    )
    result = await db.execute(stmt)
    application = result.scalar_one_or_none()

    if not application:
        application = JobApplication(
            id=uuid.uuid4(),
            job_id=job_id,
            user_id=user_id,
        )
        db.add(application)

    application.status = status
    if cover_letter:
        application.cover_letter = cover_letter
    if notes:
        application.notes = notes
    if status == "applied" and not application.applied_at:
        application.applied_at = datetime.now(timezone.utc)

    await db.flush()
    return application
