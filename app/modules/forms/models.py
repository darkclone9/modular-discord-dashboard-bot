from datetime import datetime
from uuid import uuid4

from core.db import Base
from core.sessions import utcnow
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def short_id() -> str:
    return uuid4().hex[:12]


class Form(Base):
    __tablename__ = "forms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guild_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    post_channel_id: Mapped[str] = mapped_column(String(32))
    review_channel_id: Mapped[str] = mapped_column(String(32))
    reviewer_role_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    viewer_role_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    auto_role_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    approval_message: Mapped[str] = mapped_column(
        Text, default="Your application has been approved."
    )
    denial_message: Mapped[str] = mapped_column(Text, default="Your application was denied.")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    published_message_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    fields: Mapped[list["FormField"]] = relationship(
        back_populates="form",
        cascade="all, delete-orphan",
        order_by="FormField.position",
        lazy="selectin",
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="form", cascade="all, delete-orphan"
    )

    @property
    def thread_access_role_ids(self) -> list[str]:
        return list(dict.fromkeys([*self.reviewer_role_ids, *self.viewer_role_ids]))


class FormField(Base):
    __tablename__ = "form_fields"
    __table_args__ = (UniqueConstraint("form_id", "position", name="uq_form_fields_form_position"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(300))
    field_type: Mapped[str] = mapped_column(String(32))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    options: Mapped[list[str]] = mapped_column(JSON, default=list)

    form: Mapped[Form] = relationship(back_populates="fields")


class Submission(Base):
    __tablename__ = "form_submissions"
    __table_args__ = (
        Index("ix_form_submissions_form_user_status", "form_id", "user_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=short_id)
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"), index=True)
    guild_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    username: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    answers: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    thread_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    form: Mapped[Form] = relationship(back_populates="submissions", lazy="selectin")
    actions: Mapped[list["SubmissionAction"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SubmissionAction.created_at",
        lazy="selectin",
    )


class SubmissionAction(Base):
    __tablename__ = "form_submission_actions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    submission_id: Mapped[str] = mapped_column(
        ForeignKey("form_submissions.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    submission: Mapped[Submission] = relationship(back_populates="actions")
