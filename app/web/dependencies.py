from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from core.config import Settings, get_settings
from core.db import get_session_factory
from core.discord_permissions import filter_manageable_guilds
from core.oauth import DiscordOAuthClient
from core.sessions import DashboardSession
from fastapi import Depends, HTTPException, Path, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_db() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def get_current_session(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DashboardSession:
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    result = await db.execute(
        select(DashboardSession)
        .options(selectinload(DashboardSession.token))
        .where(
            DashboardSession.id == session_id,
            DashboardSession.expires_at > datetime.now(UTC),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return session


async def require_guild_manager(
    guild_id: Annotated[str, Path(...)],
    dashboard_session: Annotated[DashboardSession, Depends(get_current_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if dashboard_session.token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth token missing")
    oauth = DiscordOAuthClient(settings)
    guilds = await oauth.fetch_user_guilds(dashboard_session.token.access_token)
    manageable = filter_manageable_guilds(guilds)
    if not any(str(guild["id"]) == str(guild_id) for guild in manageable):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manage Server required")
    return guild_id
