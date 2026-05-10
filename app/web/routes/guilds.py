from typing import Annotated

from core.config import Settings, get_settings
from core.sessions import DashboardSession
from fastapi import APIRouter, Depends

from app.web.dependencies import get_current_session, get_manageable_guilds_for_session

router = APIRouter(prefix="/guilds", tags=["guilds"])


@router.get("")
async def list_manageable_guilds(
    session: Annotated[DashboardSession, Depends(get_current_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[dict]:
    return await get_manageable_guilds_for_session(session, settings)
