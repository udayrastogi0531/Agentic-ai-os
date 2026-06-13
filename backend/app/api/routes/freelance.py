"""
Nidhi AI OS — Freelancing Assistant API Routes
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user
from app.models.user import User
from app.agents.freelance_agent import search_freelance_gigs, generate_freelance_proposal

router = APIRouter(prefix="/freelance", tags=["freelance"])


# ── Schemas ─────────────────────────────────────────────────────────────

class FreelanceProposalRequest(BaseModel):
    title: str
    platform: str
    description: str
    budget: str


# ── Routes ──────────────────────────────────────────────────────────────

@router.get("/search")
async def get_gigs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Search freelance matched opportunities."""
    gigs = await search_freelance_gigs(db, current_user)
    return {"gigs": gigs}


@router.post("/proposal")
async def make_proposal(
    data: FreelanceProposalRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate high-converting custom proposals."""
    proposal = await generate_freelance_proposal(
        data.title,
        data.platform,
        data.description,
        data.budget,
        db,
        current_user
    )
    return {"proposal": proposal}
