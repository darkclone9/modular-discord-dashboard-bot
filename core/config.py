from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.discord_permissions import MANAGE_GUILD


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")

    discord_bot_token: str = Field(alias="DISCORD_BOT_TOKEN")
    discord_client_id: str = Field(alias="DISCORD_CLIENT_ID")
    discord_client_secret: str = Field(alias="DISCORD_CLIENT_SECRET")
    discord_redirect_uri: str = Field(alias="DISCORD_REDIRECT_URI")

    local_admin_username: str | None = Field(default=None, alias="LOCAL_ADMIN_USERNAME")
    local_admin_password: str | None = Field(default=None, alias="LOCAL_ADMIN_PASSWORD")
    local_admin_guilds: str = Field(default="", alias="LOCAL_ADMIN_GUILDS")

    web_domain: str = Field(default="http://localhost:5173", alias="WEB_DOMAIN")
    api_domain: str = Field(default="http://localhost:8000", alias="API_DOMAIN")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    cors_extra_origins: str = Field(default="", alias="CORS_EXTRA_ORIGINS")

    session_secret: str = Field(alias="SESSION_SECRET")
    session_cookie_name: str = Field(default="dashboard_session", alias="SESSION_COOKIE_NAME")
    csrf_cookie_name: str = Field(default="csrf_token", alias="CSRF_COOKIE_NAME")
    session_ttl_seconds: int = Field(default=60 * 60 * 24 * 7, alias="SESSION_TTL_SECONDS")

    publish_poll_interval_seconds: int = Field(default=30, alias="PUBLISH_POLL_INTERVAL_SECONDS")
    sync_application_commands: bool = Field(default=True, alias="SYNC_APPLICATION_COMMANDS")

    @field_validator("cookie_domain", mode="before")
    @classmethod
    def empty_cookie_domain_to_none(cls, value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def secure_cookies(self) -> bool:
        return self.is_production or self.api_domain.startswith("https://")

    @property
    def normalized_cookie_domain(self) -> str | None:
        if self.cookie_domain in {None, "localhost"}:
            return None
        return self.cookie_domain

    @property
    def local_admin_enabled(self) -> bool:
        return bool(self.local_admin_username and self.local_admin_password)

    @property
    def local_admin_session_user_id(self) -> str:
        return "local-admin"

    @property
    def local_admin_guild_list(self) -> list[dict[str, object]]:
        guilds: list[dict[str, object]] = []
        for item in self.local_admin_guilds.split(","):
            if not item.strip():
                continue
            guild_id, _, name = item.partition(":")
            guild_id = guild_id.strip()
            name = name.strip() or f"Server {guild_id}"
            if guild_id:
                guilds.append(
                    {
                        "id": guild_id,
                        "name": name,
                        "icon": None,
                        "owner": True,
                        "permissions": str(MANAGE_GUILD),
                    }
                )
        return guilds

    def local_admin_can_manage_guild(self, guild_id: str) -> bool:
        return any(str(guild["id"]) == str(guild_id) for guild in self.local_admin_guild_list)

    @property
    def allowed_cors_origins(self) -> list[str]:
        origins = [self.web_domain.rstrip("/")]
        if not self.is_production:
            origins.append("http://localhost:5173")
        if self.cors_extra_origins.strip():
            origins.extend(
                origin.strip().rstrip("/")
                for origin in self.cors_extra_origins.split(",")
                if origin.strip()
            )
        return list(dict.fromkeys(origins))


@lru_cache
def get_settings() -> Settings:
    return Settings()
