"""
Nidhi AI OS — Freelancing Assistant Agent
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.provider import get_llm
from app.models.user_profile import UserProfile
from app.models.user import User

logger = logging.getLogger(__name__)

FREELANCE_SEARCH_PROMPT = """You are **Nidhi**, Uday's smart freelance gig hunter.
Based on Uday's profile skills, generate a list of 3 mock/recent high-value freelance projects from platforms like Upwork, Wellfound, and Internshala that he is highly suited for.

UserProfile Skills: {skills}

Generate the matched gig list in JSON format, matching this schema:
[
  {{
    "id": 1,
    "title": "Build a Custom LangGraph chatbot agent",
    "platform": "Upwork",
    "budget": "$1,500 - $2,500",
    "description": "Client wants an AI workflow that uses LangGraph to coordinate between a coding agent and a researcher.",
    "match_score": 95,
    "required_skills": ["LangGraph", "Python", "FastAPI"]
  }}
]
Output ONLY valid JSON, nothing else.
"""

FREELANCE_PROPOSAL_PROMPT = """You are **Nidhi**, Uday's freelance proposal strategist.
Write a high-converting, professional, yet warm project bid proposal for Uday based on his profile and the target project details below:

Project: {title} ({platform})
Description: {description}
Budget: {budget}

UserProfile Skills: {skills}

Write the proposal in clear markdown format.
Make sure to:
1. Address the client's problem directly and explain how Uday can solve it.
2. Outline specific technologies (e.g. LangChain, React, FastAPI) he will use.
3. Suggest a delivery timeline (e.g. 2-3 weeks) and hourly rate / project milestones.
4. Keep the tone professional, persuasive, and confident.
"""

async def search_freelance_gigs(db: AsyncSession, user: User) -> list[dict]:
    """Retrieve custom freelance project recommendations."""
    stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    skills = ", ".join(profile.skills) if profile and profile.skills else "Python, React, FastAPI, Machine Learning"

    prompt = FREELANCE_SEARCH_PROMPT.format(skills=skills)
    try:
        llm = get_llm(temperature=0.7)
        response = await llm.ainvoke(prompt)
        import json
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Failed to search freelance gigs: {e}", exc_info=True)
        return [
            {
                "id": 1,
                "title": "GenAI Agent Developer for Automating Workflows",
                "platform": "Upwork",
                "budget": "$45 - $60 / hr",
                "description": "Looking for a Python dev who can configure LangGraph, Tavily API, and LlamaIndex agents.",
                "match_score": 90,
                "required_skills": ["Python", "LangGraph", "LlamaIndex"]
            },
            {
                "id": 2,
                "title": "Fullstack React + FastAPI AI App Integration",
                "platform": "Wellfound",
                "budget": "$3,000",
                "description": "Need a developer to construct a beautiful client dashboard integrating real-time Websocket events.",
                "match_score": 88,
                "required_skills": ["React", "FastAPI", "Websockets"]
            }
        ]


async def generate_freelance_proposal(project_title: str, platform: str, description: str, budget: str, db: AsyncSession, user: User) -> str:
    """Generate custom bid proposal cover letter."""
    stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    skills = ", ".join(profile.skills) if profile and profile.skills else "Python, React, FastAPI"

    prompt = FREELANCE_PROPOSAL_PROMPT.format(
        title=project_title,
        platform=platform,
        description=description,
        budget=budget,
        skills=skills
    )
    try:
        llm = get_llm(temperature=0.5)
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception as e:
        return f"Error crafting proposal template: {str(e)}"
