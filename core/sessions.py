from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class DashboardSession(Base):
    __tablename__ = "dashboard_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid4().hex)
    discord_user_id: Mapped[str] = mapped_column(String(32), index=True)
    username: Mapped[str] = mapped_column(String(128))
    avatar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    csrf_token: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    token: Mapped["DiscordOAuthToken"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )


class DiscordOAuthToken(Base):
    __tablename__ = "discord_oauth_tokens"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("dashboard_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str] = mapped_column(String(32), default="Bearer")
    scope: Mapped[str] = mapped_column(String(256), default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    session: Mapped[DashboardSession] = relationship(back_populates="token")
