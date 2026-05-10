from datetime import datetime
from uuid import uuid4

from core.db import Base
from core.sessions import utcnow
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class SocialTracker(Base):
    __tablename__ = "social_trackers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guild_id: Mapped[str] = mapped_column(String(32), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[str] = mapped_column(String(256))
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notification_channel_id: Mapped[str] = mapped_column(String(32))
    custom_message: Mapped[str] = mapped_column(
        Text,
        default="New {provider} post from {source}: {url}",
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_seen_external_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_seen_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class GameSuggestionSettings(Base):
    __tablename__ = "game_suggestion_settings"

    guild_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    announcement_channel_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reward_role_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mention_everyone: Mapped[bool] = mapped_column(Boolean, default=True)
    announcement_weekday: Mapped[int] = mapped_column(Integer, default=0)
    announcement_hour_utc: Mapped[int] = mapped_column(Integer, default=18)
    custom_message: Mapped[str] = mapped_column(
        Text,
        default=(
            "This week's community game pick is **{game}** from {player}! "
            "{player_mention}, you were picked and received the reward."
        ),
    )
    last_announced_week: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class GameActivitySnapshot(Base):
    __tablename__ = "game_activity_snapshots"
    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", "game_name", name="uq_game_activity_seen"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guild_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    username: Mapped[str] = mapped_column(String(128))
    game_name: Mapped[str] = mapped_column(String(128), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GameSuggestionPick(Base):
    __tablename__ = "game_suggestion_picks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guild_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32))
    username: Mapped[str] = mapped_column(String(128))
    game_name: Mapped[str] = mapped_column(String(128))
    channel_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    announced_week: Mapped[str] = mapped_column(String(16), index=True)
    announced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
