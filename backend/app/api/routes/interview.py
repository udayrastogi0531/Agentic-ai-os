"""
Nidhi AI OS — Interview Coach API Routes
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.user import User
from app.agents.interview_agent import generate_interview_questions, evaluate_interview_answer

router = APIRouter(prefix="/interview", tags=["interview"])


# ── Schemas ─────────────────────────────────────────────────────────────

class InterviewQuestionsRequest(BaseModel):
    role: str = "AI Engineer"
    topic: str = "ML & GenAI Theory"
    difficulty: str = "Mid"


class InterviewEvaluationRequest(BaseModel):
    question: str
    answer: str


# ── Routes ──────────────────────────────────────────────────────────────

@router.post("/questions")
async def get_questions(
    data: InterviewQuestionsRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate interview questions matching custom criteria."""
    questions = await generate_interview_questions(data.role, data.topic, data.difficulty)
    return {"questions": questions}


@router.post("/evaluate")
async def evaluate_answer(
    data: InterviewEvaluationRequest,
    current_user: User = Depends(get_current_user),
):
    """Evaluate a candidate's answer text."""
    evaluation = await evaluate_interview_answer(data.question, data.answer)
    return {"evaluation": evaluation}
