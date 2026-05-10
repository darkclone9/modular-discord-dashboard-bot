from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from core.config import Settings
from core.retries import retry_external_call

DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordOAuthClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.settings.discord_client_id,
            "redirect_uri": self.settings.discord_redirect_uri,
            "response_type": "code",
            "scope": "identify guilds",
            "state": state,
        }
        return f"{DISCORD_API_BASE}/oauth2/authorize?{urlencode(params)}"

    @retry_external_call
    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{DISCORD_API_BASE}/oauth2/token",
                data={
                    "client_id": self.settings.discord_client_id,
                    "client_secret": self.settings.discord_client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.settings.discord_redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    @retry_external_call
    async def fetch_current_user(self, access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{DISCORD_API_BASE}/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    @retry_external_call
    async def fetch_user_guilds(self, access_token: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{DISCORD_API_BASE}/users/@me/guilds",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()


def token_expires_at(token_payload: dict) -> datetime | None:
    expires_in = token_payload.get("expires_in")
    if expires_in is None:
        return None
    return datetime.now(UTC) + timedelta(seconds=int(expires_in))
