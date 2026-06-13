"""
Nidhi AI OS — Daily Briefing Agent
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import get_llm
from app.models.task import Task
from app.models.goal import Goal
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.job import Job

logger = logging.getLogger(__name__)

BRIEFING_PROMPT = """You are **Nidhi**, the warm, caring, and highly capable personal AI companion for Uday.
Generate a daily briefing for Uday. Address him using his nickname if set, or just "Uday".
Your tone must be extremely supportive, encouraging, and friendly like a close companion.
Use a natural blend of English and Hindi (Hinglish) (e.g. "Namaste Uday!", "Aapki tasks ready hain", "bilkul tension mat lena", "aaj hum isko complete karenge").

Current Date & Time: {current_time}

Here is the context for Uday's day:
---
👤 PROFILE BIO:
{bio}

✅ PENDING TASKS FOR TODAY:
{tasks}

🎯 ACTIVE GOALS:
{goals}

💼 SAVED JOBS / APPLICATIONS IN PROGRESS:
{jobs}
---

Write a beautiful, structured daily briefing in Markdown format.
Structure of the briefing:
1. **Empathetic Opening**: A warm, personal greeting, wishing him well (e.g., checking if he had his morning tea/coffee ☕).
2. **Focus of the Day**: Highlight the most important task or milestone due today.
3. **Agenda Outline**: Briefly list today's pending tasks and status of active goals.
4. **Career & Placement Push**: A brief word of encouragement or strategy for his target roles (AI Engineer, Gen AI Engineer, ML Engineer, SWE) and job search.
5. **Empathetic Closing**: A highly motivating, sweet sign-off.

Keep it relatively concise, friendly, and structured. Use emojis nicely.
"""

async def generate_daily_brief(db: AsyncSession, user: User) -> str:
    """Generate a personalized daily brief for the user."""
    # 1. Fetch user profile bio
    stmt_profile = select(UserProfile).where(UserProfile.user_id == user.id)
    profile_res = await db.execute(stmt_profile)
    profile = profile_res.scalar_one_or_none()
    bio = profile.bio if profile else "No bio set."

    # 2. Fetch pending tasks
    stmt_tasks = select(Task).where(Task.user_id == user.id, Task.status != "completed").limit(10)
    tasks_res = await db.execute(stmt_tasks)
    tasks_list = tasks_res.scalars().all()
    tasks_str = "\n".join(f"- [{t.priority.upper()}] {t.title} (Category: {t.category})" for t in tasks_list) if tasks_list else "No pending tasks for today! Chill day. 😎"

    # 3. Fetch active goals
    stmt_goals = select(Goal).where(Goal.user_id == user.id, Goal.status == "active").limit(5)
    goals_res = await db.execute(stmt_goals)
    goals_list = goals_res.scalars().all()
    goals_str = "\n".join(f"- {g.title} ({g.progress}% complete, Category: {g.category})" for g in goals_list) if goals_list else "No active goals tracked right now."

    # 4. Fetch jobs
    stmt_jobs = select(Job).where(Job.user_id == user.id).limit(5)
    jobs_res = await db.execute(stmt_jobs)
    jobs_list = jobs_res.scalars().all()
    jobs_str = "\n".join(f"- {j.title} at {j.company} (Match Score: {j.match_score}%)" for j in jobs_list) if jobs_list else "No active jobs saved."

    # 5. Formulate Prompt
    current_time = datetime.now().strftime("%A, %B %d, %Y")
    prompt = BRIEFING_PROMPT.format(
        current_time=current_time,
        bio=bio,
        tasks=tasks_str,
        goals=goals_str,
        jobs=jobs_str
    )

    # 6. Call LLM
    try:
        llm = get_llm(temperature=0.7)
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate daily brief: {e}", exc_info=True)
        return (
            f"### ☕ Namaste {user.nickname or user.name}!\n\n"
            "Main aapke liye daily brief generate nahi kar payi network issue ki wajah se. "
            "But koi baat nahi! Aapka din accha jayega. Chaliye tasks aur goals checklist ko view karte hain!"
        )
