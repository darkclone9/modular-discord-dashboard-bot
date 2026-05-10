from datetime import UTC, datetime, timedelta
from typing import Annotated

from core.config import Settings, get_settings
from core.oauth import DiscordOAuthClient, token_expires_at
from core.security import random_token, sign_state, verify_state
from core.sessions import DashboardSession, DiscordOAuthToken
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.web.dependencies import get_current_session, get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, settings: Settings, session: DashboardSession) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        session.id,
        max_age=settings.session_ttl_seconds,
        domain=settings.normalized_cookie_domain,
        secure=settings.secure_cookies,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        session.csrf_token,
        max_age=settings.session_ttl_seconds,
        domain=settings.normalized_cookie_domain,
        secure=settings.secure_cookies,
        httponly=False,
        samesite="lax",
    )


@router.get("/discord/login")
async def discord_login(settings: Annotated[Settings, Depends(get_settings)]) -> RedirectResponse:
    state = sign_state(settings, {"nonce": random_token()})
    return RedirectResponse(DiscordOAuthClient(settings).authorization_url(state))


@router.get("/discord/callback")
async def discord_callback(
    code: str,
    state: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedirectResponse:
    try:
        verify_state(settings, state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    oauth = DiscordOAuthClient(settings)
    token_payload = await oauth.exchange_code(code)
    user = await oauth.fetch_current_user(token_payload["access_token"])

    dashboard_session = DashboardSession(
        discord_user_id=str(user["id"]),
        username=user.get("global_name") or user.get("username") or str(user["id"]),
        avatar=user.get("avatar"),
        csrf_token=random_token(),
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.session_ttl_seconds),
    )
    dashboard_session.token = DiscordOAuthToken(
        access_token=token_payload["access_token"],
        refresh_token=token_payload.get("refresh_token"),
        token_type=token_payload.get("token_type", "Bearer"),
        scope=token_payload.get("scope", ""),
        expires_at=token_expires_at(token_payload),
    )
    db.add(dashboard_session)
    await db.commit()

    response = RedirectResponse(settings.web_domain)
    _set_auth_cookies(response, settings, dashboard_session)
    return response


@router.get("/me")
async def me(session: Annotated[DashboardSession, Depends(get_current_session)]) -> dict:
    return {
        "id": session.discord_user_id,
        "username": session.username,
        "avatar": session.avatar,
        "csrfToken": session.csrf_token,
    }


@router.post("/logout")
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    session: Annotated[DashboardSession, Depends(get_current_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    await db.delete(session)
    await db.commit()
    response.delete_cookie(settings.session_cookie_name, domain=settings.normalized_cookie_domain)
    response.delete_cookie(settings.csrf_cookie_name, domain=settings.normalized_cookie_domain)
    return {"status": "ok"}
