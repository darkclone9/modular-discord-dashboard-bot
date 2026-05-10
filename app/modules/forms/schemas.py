from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FieldType = Literal["short_text", "long_text", "select", "multi_select", "number", "boolean"]
SubmissionStatus = Literal["pending", "approved", "denied"]


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class FormFieldCreate(APIModel):
    label: str = Field(min_length=1, max_length=100)
    field_type: FieldType
    required: bool = True
    options: list[str] = Field(default_factory=list)


class FormFieldRead(FormFieldCreate):
    id: str
    position: int


class ReviewSettings(APIModel):
    reviewer_role_ids: list[str] = Field(default_factory=list)
    viewer_role_ids: list[str] = Field(default_factory=list)
    review_channel_id: str
    auto_role_id: str | None = None
    approval_message: str = "Your application has been approved."
    denial_message: str = "Your application was denied."


class FormCreate(APIModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = ""
    post_channel_id: str
    fields: list[FormFieldCreate] = Field(min_length=1)
    review_settings: ReviewSettings


class FormUpdate(APIModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    post_channel_id: str | None = None
    fields: list[FormFieldCreate] | None = None
    review_settings: ReviewSettings | None = None


class FormRead(APIModel):
    id: str
    guild_id: str
    title: str
    description: str
    post_channel_id: str
    fields: list[FormFieldRead]
    review_settings: ReviewSettings
    is_archived: bool
    is_published: bool
    published_message_id: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SubmissionCreate(APIModel):
    answers: dict[str, object]


class SubmissionActionRead(APIModel):
    actor_id: str
    action: str
    note: str | None
    created_at: datetime


class SubmissionRead(APIModel):
    id: str
    form_id: str
    guild_id: str
    user_id: str
    username: str
    status: SubmissionStatus
    answers: dict[str, object]
    thread_id: str | None
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None
    actions: list[SubmissionActionRead] = Field(default_factory=list)
