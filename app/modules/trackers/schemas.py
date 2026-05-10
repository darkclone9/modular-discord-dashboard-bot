from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TrackerProvider = Literal["youtube", "tiktok", "instagram", "facebook"]


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SocialTrackerCreate(APIModel):
    provider: TrackerProvider
    label: str = Field(min_length=1, max_length=100)
    source_id: str = Field(min_length=1, max_length=256)
    source_url: str | None = Field(default=None, max_length=512)
    notification_channel_id: str = Field(min_length=1, max_length=32)
    custom_message: str = Field(
        default="New {provider} post from {source}: {url}",
        max_length=2000,
    )
    is_enabled: bool = True

    @field_validator("custom_message")
    @classmethod
    def custom_message_must_include_url(cls, value: str) -> str:
        if "{url}" not in value:
            raise ValueError("Custom message must include {url}")
        return value


class SocialTrackerUpdate(APIModel):
    provider: TrackerProvider | None = None
    label: str | None = Field(default=None, min_length=1, max_length=100)
    source_id: str | None = Field(default=None, min_length=1, max_length=256)
    source_url: str | None = Field(default=None, max_length=512)
    notification_channel_id: str | None = Field(default=None, min_length=1, max_length=32)
    custom_message: str | None = Field(default=None, max_length=2000)
    is_enabled: bool | None = None

    @field_validator("custom_message")
    @classmethod
    def custom_message_must_include_url(cls, value: str | None) -> str | None:
        if value is not None and "{url}" not in value:
            raise ValueError("Custom message must include {url}")
        return value


class SocialTrackerRead(SocialTrackerCreate):
    id: str
    guild_id: str
    last_seen_external_id: str | None
    last_seen_url: str | None
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class GameSuggestionSettingsRead(APIModel):
    guild_id: str
    enabled: bool
    announcement_channel_id: str | None
    reward_role_id: str | None
    mention_everyone: bool
    announcement_weekday: int
    announcement_hour_utc: int
    custom_message: str
    last_announced_week: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GameSuggestionSettingsUpdate(APIModel):
    enabled: bool = False
    announcement_channel_id: str | None = None
    reward_role_id: str | None = None
    mention_everyone: bool = True
    announcement_weekday: int = Field(default=0, ge=0, le=6)
    announcement_hour_utc: int = Field(default=18, ge=0, le=23)
    custom_message: str = Field(
        default=(
            "This week's community game pick is **{game}** from {player}! "
            "{player_mention}, you were picked and received the reward."
        ),
        max_length=2000,
    )

    @field_validator("custom_message")
    @classmethod
    def custom_message_must_include_game(cls, value: str) -> str:
        if "{game}" not in value:
            raise ValueError("Custom message must include {game}")
        return value


class GameSuggestionPickRead(APIModel):
    id: str
    guild_id: str
    user_id: str
    username: str
    game_name: str
    channel_id: str | None
    message_id: str | None
    announced_week: str
    announced_at: datetime
