"""
Nidhi AI OS — Resume Agent

Analyzes resumes, generates ATS scores, improves content,
creates cover letters, LinkedIn summaries, and portfolio descriptions.
"""

from __future__ import annotations

import json
import logging

from app.llm.provider import get_llm

logger = logging.getLogger(__name__)


# ── Resume Analysis ─────────────────────────────────────────────────────

async def analyze_resume(
    resume_text: str,
    target_role: str | None = None,
) -> dict:
    """
    Comprehensive resume analysis with ATS scoring.
    Returns strengths, weaknesses, and improvement recommendations.
    """
    llm = get_llm("reasoning")

    role_context = f"Target role: {target_role}" if target_role else "General tech/software roles"

    prompt = f"""You are an expert resume coach and ATS optimization specialist.

Analyze this resume comprehensively.

{role_context}

RESUME:
{resume_text[:4000]}

Return ONLY valid JSON:
{{
  "ats_score": 72,
  "overall_score": 68,
  "verdict": "Good - needs improvements",
  "strengths": [
    "Strong technical skills section",
    "Well-quantified project achievements"
  ],
  "weaknesses": [
    "Missing summary/objective section",
    "Action verbs underused"
  ],
  "missing_sections": ["Professional Summary", "Certifications"],
  "formatting_issues": ["Inconsistent date formats", "Too long"],
  "keyword_density": {{
    "technical": ["Python", "Machine Learning"],
    "missing_high_value": ["LLM", "Generative AI", "Cloud"]
  }},
  "improvements": [
    {{
      "priority": "high",
      "section": "Summary",
      "issue": "No professional summary",
      "fix": "Add a 3-sentence summary highlighting your AI/ML expertise"
    }},
    {{
      "priority": "medium",
      "section": "Projects",
      "issue": "Projects lack impact metrics",
      "fix": "Add numbers: 'Reduced latency by 40%' instead of 'Improved performance'"
    }}
  ],
  "estimated_shortlist_probability": "35%",
  "summary": "Your resume shows solid technical foundations but needs stronger positioning for AI roles."
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
        logger.error(f"Resume analysis failed: {e}")
        return {
            "ats_score": 0,
            "overall_score": 0,
            "verdict": "Analysis failed",
            "strengths": [],
            "weaknesses": ["Could not analyze resume"],
            "improvements": [],
            "summary": f"Error: {str(e)}",
        }


# ── Resume Improvement ──────────────────────────────────────────────────

async def improve_resume(
    resume_text: str,
    target_role: str = "AI/ML Engineer",
    job_description: str | None = None,
) -> str:
    """
    Generate an improved version of the resume.
    """
    llm = get_llm("reasoning")

    jd_context = f"\nTarget JOB DESCRIPTION:\n{job_description[:1500]}" if job_description else ""

    prompt = f"""You are an expert resume writer specializing in tech and AI/ML roles.

Improve this resume for the target role: {target_role}
{jd_context}

ORIGINAL RESUME:
{resume_text[:3000]}

Instructions:
1. Keep all true information — never fabricate
2. Use strong action verbs (Built, Engineered, Developed, Led, Optimized)
3. Add quantifiable impact where logical ("Improved X by Y%")
4. Add ATS keywords for {target_role} roles
5. Fix formatting issues
6. Add/improve professional summary (3 sentences)
7. Rewrite project descriptions to highlight impact

Output the complete improved resume in clean, ATS-friendly plain text format.
Use this structure:
[NAME]
[CONTACT INFO]

PROFESSIONAL SUMMARY
[3 sentences]

SKILLS
[Categorized skills]

EXPERIENCE
[If any]

PROJECTS
[Enhanced descriptions]

EDUCATION
[Details]"""

    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        logger.error(f"Resume improvement failed: {e}")
        return f"[Resume improvement failed: {e}]\n\nOriginal:\n{resume_text}"


# ── ATS Resume Generator (from Profile) ────────────────────────────────

async def generate_ats_resume(user_profile: dict) -> str:
    """
    Generate a complete ATS-optimized resume from the user profile.
    """
    llm = get_llm("reasoning")

    name = user_profile.get("name", "Uday Rastogi")
    email = user_profile.get("email", "")
    github = user_profile.get("github_url", "")
    linkedin = user_profile.get("linkedin_url", "")
    portfolio = user_profile.get("portfolio_url", "")
    university = user_profile.get("university", "")
    graduation_year = user_profile.get("graduation_year", "")
    skills = user_profile.get("skills", [])
    projects = user_profile.get("current_projects", [])
    target_roles = user_profile.get("target_roles", ["AI Engineer"])
    goals = user_profile.get("career_goals", [])

    skills_str = ", ".join(skills) if skills else "Python, Machine Learning, FastAPI"
    target = ", ".join(target_roles) if target_roles else "AI/ML Engineer"

    projects_str = "\n".join([
        f"- {p.get('name', 'Project')}: {p.get('description', '')}"
        for p in (projects or [])[:5]
    ]) or "- Nidhi AI OS: Personal AI Operating System using FastAPI + LangGraph + Next.js"

    prompt = f"""Generate a professional, ATS-optimized resume for this person.

NAME: {name}
EMAIL: {email}
GITHUB: {github}
LINKEDIN: {linkedin}
PORTFOLIO: {portfolio}
UNIVERSITY: {university}
GRADUATION: {graduation_year}
SKILLS: {skills_str}
TARGET ROLES: {target}

PROJECTS:
{projects_str}

Create a complete, professional resume with:
1. Contact section
2. Professional Summary (3 impactful sentences, tailored for {target})
3. Technical Skills (categorized)
4. Projects (with tech stack and impact bullets)
5. Education
6. Add relevant ATS keywords throughout

Format: Clean plain text, ATS-friendly. NO tables, NO special characters.
Make it impressive but truthful."""

    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        logger.error(f"ATS resume generation failed: {e}")
        return f"[Generation failed: {e}]"


# ── Cover Letter ────────────────────────────────────────────────────────

async def generate_cover_letter(
    user_profile: dict,
    job_description: str,
    company_name: str = "",
) -> str:
    """
    Generate a personalized cover letter from profile + JD.
    """
    llm = get_llm("reasoning")

    name = user_profile.get("name", "Uday")
    skills = ", ".join((user_profile.get("skills") or [])[:10])
    projects = user_profile.get("current_projects") or []
    project_names = ", ".join([p.get("name", "") for p in projects[:3]])

    prompt = f"""Write a compelling cover letter.

APPLICANT: {name}
SKILLS: {skills}
KEY PROJECTS: {project_names or "AI/ML projects"}
COMPANY: {company_name or "this company"}

JOB DESCRIPTION:
{job_description[:2000]}

Rules:
- 250-320 words
- Professional-warm tone (not robotic)
- Opening: creative hook, NOT "I am writing to..."
- Body: 2 paragraphs, each connecting 1-2 specific skills/projects to JD requirements
- Closing: confident, specific call to action
- Sound like a passionate, real person who genuinely wants this role
- Add relevant technical keywords from JD naturally

Write ONLY the cover letter body (no subject line)."""

    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        logger.error(f"Cover letter failed: {e}")
        return f"[Cover letter generation failed: {e}]"


# ── LinkedIn Summary ────────────────────────────────────────────────────

async def generate_linkedin_summary(user_profile: dict) -> str:
    """Generate an engaging LinkedIn About section."""
    llm = get_llm("fast")

    name = user_profile.get("name", "Uday")
    skills = ", ".join((user_profile.get("skills") or [])[:10])
    goals = user_profile.get("career_goals") or []
    goal_str = goals[0].get("goal", "AI Engineer") if goals else "AI Engineer"
    projects = user_profile.get("current_projects") or []
    project_names = ", ".join([p.get("name", "") for p in projects[:3]])

    prompt = f"""Write a compelling LinkedIn About/Summary section.

PERSON: {name}
SKILLS: {skills}
CAREER GOAL: {goal_str}
PROJECTS: {project_names}

Rules:
- 150-200 words
- First person, conversational yet professional
- Start with a strong hook (not "Hi, I'm...")
- Mention passion for AI/tech
- Include 2-3 specific technical highlights
- End with what you're looking for
- Add 3-5 relevant hashtags at the end

Write the LinkedIn summary now:"""

    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        logger.error(f"LinkedIn summary failed: {e}")
        return f"[Generation failed: {e}]"


# ── Portfolio Content ───────────────────────────────────────────────────

async def generate_portfolio_content(projects: list[dict]) -> list[dict]:
    """Generate polished project descriptions for portfolio."""
    llm = get_llm("fast")
    results = []

    for project in projects[:8]:
        name = project.get("name", "Project")
        description = project.get("description", "")
        tech = project.get("tech", [])
        url = project.get("url", "")

        prompt = f"""Write a compelling project description for a portfolio website.

PROJECT: {name}
BASIC DESCRIPTION: {description}
TECH STACK: {', '.join(tech)}
URL: {url}

Generate:
1. "tagline": One punchy sentence (max 15 words)
2. "description": 2-3 sentences explaining what it does and why it matters
3. "impact": 1 sentence about impact or what you learned
4. "highlights": 3 bullet points of key features/achievements

Return valid JSON only."""

        try:
            from langchain_core.messages import HumanMessage
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            parsed = json.loads(content)
            parsed["name"] = name
            parsed["tech"] = tech
            parsed["url"] = url
            results.append(parsed)
        except Exception as e:
            logger.error(f"Portfolio content for {name} failed: {e}")
            results.append({
                "name": name,
                "tagline": description[:80],
                "description": description,
                "tech": tech,
                "url": url,
                "highlights": [],
            })

    return results
