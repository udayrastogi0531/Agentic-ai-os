"""
Nidhi AI OS — Career Coach API Routes
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.agents.career_agent import generate_career_roadmap
from app.llm.provider import get_llm

router = APIRouter(prefix="/career", tags=["career"])


class CareerChatRequest(BaseModel):
    message: str


@router.get("/roadmap")
async def get_roadmap(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate profile-based career roadmaps."""
    roadmap = await generate_career_roadmap(db, current_user)
    return {"roadmap": roadmap}


@router.post("/chat")
async def career_chat(
    data: CareerChatRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Chat with Nidhi specifically on career topics."""
    prompt = f"""You are **Nidhi**, Uday's warm, supportive, and strategic career coach.
He wants to ask you something about his career path:

User Query: "{data.message}"

Please respond in a highly encouraging, helpful, Hinglish tone.
Reference his target roles (AI Engineer, Gen AI Engineer, ML Engineer, SWE, Full Stack) and locations (India + Remote) if relevant.
"""
    try:
        llm = get_llm(temperature=0.7)
        response = await llm.ainvoke(prompt)
        return {"response": response.content}
    except Exception as e:
        return {"response": f"Oh, sorry! Main response generate nahi kar payi. (Error: {str(e)})"}
