from typing import Annotated

from core.config import Settings, get_settings
from core.discord_permissions import filter_manageable_guilds
from core.oauth import DiscordOAuthClient
from core.sessions import DashboardSession
from fastapi import APIRouter, Depends

from app.web.dependencies import get_current_session, is_local_admin_session

router = APIRouter(prefix="/guilds", tags=["guilds"])


@router.get("")
async def list_manageable_guilds(
    session: Annotated[DashboardSession, Depends(get_current_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[dict]:
    if is_local_admin_session(session, settings):
        return settings.local_admin_guild_list
    if session.token is None:
        return []
    guilds = await DiscordOAuthClient(settings).fetch_user_guilds(session.token.access_token)
    return filter_manageable_guilds(guilds)
