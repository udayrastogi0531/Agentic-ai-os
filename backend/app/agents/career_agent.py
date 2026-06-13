"""
Nidhi AI OS — Career Coaching Agent
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.provider import get_llm
from app.models.user_profile import UserProfile
from app.models.user import User

logger = logging.getLogger(__name__)

CAREER_COACH_PROMPT = """You are **Nidhi**, Uday's dedicated, warm, and highly strategic Career Coach.
Analyze Uday's profile details below and generate a structured career roadmap to help him land his target roles in India & Remote.

Target Roles: AI Engineer, Gen AI Engineer, ML Engineer, Software Engineer, Full Stack Developer
Preferred Locations: India + Remote

UserProfile Context:
---
Bio: {bio}
Current Role: {current_role}
Skills: {skills}
Dream Companies: {dream_companies}
Target Roles: {target_roles}
Experience: {experience_years} years
Projects: {projects}
Learning Goals: {learning_goals}
---

Generate an structured Career Roadmap in JSON format.
Your output MUST be a valid JSON object matching the schema below (do not output any markdown wrapper or other text outside the JSON, just the JSON):
{{
  "summary": "Overall Hinglish warm summary of his readiness and target career steps.",
  "target_roles_readiness": [
    {{
      "role": "AI Engineer",
      "readiness_percentage": 75,
      "gap_skills": ["LangGraph", "ChromaDB", "Vector Search"]
    }}
  ],
  "roadmap_phases": [
    {{
      "phase_number": 1,
      "title": "Phase 1: Core Foundation",
      "timeline": "1-2 Months",
      "skills_to_learn": ["FastAPI", "Asyncio in Python"],
      "recommended_action_items": [
        "Build a simple RAG app using LangChain",
        "Practice coding problems on arrays/graphs"
      ]
    }}
  ],
  "suggested_certifications": ["Google Cloud Professional ML Engineer", "DeepLearning.AI LangChain certification"]
}}
"""

async def generate_career_roadmap(db: AsyncSession, user: User) -> dict:
    """Analyze profile data and generate a career roadmap."""
    stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()

    if not profile:
        return {
            "summary": "Uday, pehle aap apna profile fill kijiye so I can design a custom roadmap for you!",
            "target_roles_readiness": [],
            "roadmap_phases": [],
            "suggested_certifications": []
        }

    prompt = CAREER_COACH_PROMPT.format(
        bio=profile.bio or "No bio",
        current_role=profile.current_role or "No current role",
        skills=", ".join(profile.skills) if profile.skills else "None",
        dream_companies=", ".join(profile.dream_companies) if profile.dream_companies else "None",
        target_roles=", ".join(profile.target_roles) if profile.target_roles else "None",
        experience_years=profile.experience_years or 0,
        projects=str(profile.current_projects or []),
        learning_goals=str(profile.learning_goals or [])
    )

    try:
        llm = get_llm(temperature=0.2)
        # Use JSON parsing fallback
        import json
        response = await llm.ainvoke(prompt)
        text = response.content.strip()
        # Clean potential markdown wraps
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Failed to generate career roadmap: {e}", exc_info=True)
        return {
            "summary": "Sorry Uday, main aapke liye career roadmap design nahi kar payi abhi. Please checklist check karo.",
            "target_roles_readiness": [],
            "roadmap_phases": [
                {
                    "phase_number": 1,
                    "title": "Phase 1: GenAI & LLM agent development foundations",
                    "timeline": "Immediate",
                    "skills_to_learn": ["LangGraph", "LangChain", "FastAPI"],
                    "recommended_action_items": ["Build your agent portfolio", "Configure Ollama model locally"]
                }
            ],
            "suggested_certifications": []
        }
