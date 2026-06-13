"""
Nidhi AI OS — Daily Briefing API Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.api.deps import get_current_user, get_optional_user
from app.models.user import User
from app.agents.briefing_agent import generate_daily_brief

router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("")
async def get_briefing(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate and return today's daily briefing."""
    brief = await generate_daily_brief(db, current_user)
    return {
        "brief": brief,
        "timestamp": datetime.now().isoformat()
    }

# Make sure datetime is imported
from datetime import datetime
