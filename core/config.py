from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")

    discord_bot_token: str = Field(alias="DISCORD_BOT_TOKEN")
    discord_client_id: str = Field(alias="DISCORD_CLIENT_ID")
    discord_client_secret: str = Field(alias="DISCORD_CLIENT_SECRET")
    discord_redirect_uri: str = Field(alias="DISCORD_REDIRECT_URI")

    web_domain: str = Field(default="http://localhost:5173", alias="WEB_DOMAIN")
    api_domain: str = Field(default="http://localhost:8000", alias="API_DOMAIN")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    cors_extra_origins: str = Field(default="", alias="CORS_EXTRA_ORIGINS")

    session_secret: str = Field(alias="SESSION_SECRET")
    session_cookie_name: str = Field(default="dashboard_session", alias="SESSION_COOKIE_NAME")
    csrf_cookie_name: str = Field(default="csrf_token", alias="CSRF_COOKIE_NAME")
    session_ttl_seconds: int = Field(default=60 * 60 * 24 * 7, alias="SESSION_TTL_SECONDS")

    publish_poll_interval_seconds: int = Field(default=30, alias="PUBLISH_POLL_INTERVAL_SECONDS")

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
