from typing import Annotated

from core.config import Settings, get_settings
from core.discord_permissions import filter_manageable_guilds
from core.oauth import DiscordOAuthClient
from core.sessions import DashboardSession
from fastapi import APIRouter, Depends

from app.web.dependencies import get_current_session

router = APIRouter(prefix="/guilds", tags=["guilds"])


@router.get("")
async def list_manageable_guilds(
    session: Annotated[DashboardSession, Depends(get_current_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[dict]:
    guilds = await DiscordOAuthClient(settings).fetch_user_guilds(session.token.access_token)
    return filter_manageable_guilds(guilds)
