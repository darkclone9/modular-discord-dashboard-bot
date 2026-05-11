from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MessageMode = Literal["bot_post", "existing_message"]
PickerStyle = Literal["reactions", "buttons", "select"]
MenuBehavior = Literal["toggle", "add_only", "single"]


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ReactionRoleOptionCreate(APIModel):
    label: str = Field(min_length=1, max_length=100)
    role_id: str = Field(min_length=1, max_length=32)
    emoji: str | None = Field(default=None, max_length=128)
    description: str = Field(default="", max_length=100)


class ReactionRoleOptionRead(ReactionRoleOptionCreate):
    id: str
    position: int


class ReactionRoleMenuCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    channel_id: str = Field(min_length=1, max_length=32)
    message_id: str | None = Field(default=None, max_length=32)
    message_mode: MessageMode = "bot_post"
    picker_style: PickerStyle = "reactions"
    behavior: MenuBehavior = "toggle"
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)
    is_enabled: bool = True
    options: list[ReactionRoleOptionCreate] = Field(min_length=1, max_length=25)


class ReactionRoleMenuUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    channel_id: str | None = Field(default=None, min_length=1, max_length=32)
    message_id: str | None = Field(default=None, max_length=32)
    message_mode: MessageMode | None = None
    picker_style: PickerStyle | None = None
    behavior: MenuBehavior | None = None
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    is_enabled: bool | None = None
    options: list[ReactionRoleOptionCreate] | None = Field(
        default=None,
        min_length=1,
        max_length=25,
    )


class ReactionRoleMenuRead(APIModel):
    id: str
    guild_id: str
    name: str
    channel_id: str
    message_id: str | None
    message_mode: MessageMode
    picker_style: PickerStyle
    behavior: MenuBehavior
    title: str
    description: str
    is_enabled: bool
    options: list[ReactionRoleOptionRead]
    created_at: datetime
    updated_at: datetime
