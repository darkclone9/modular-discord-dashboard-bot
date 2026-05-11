from datetime import datetime
from uuid import uuid4

from core.db import Base
from core.sessions import utcnow
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ReactionRoleMenu(Base):
    __tablename__ = "reaction_role_menus"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guild_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(100))
    channel_id: Mapped[str] = mapped_column(String(32))
    message_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    message_mode: Mapped[str] = mapped_column(String(32), default="bot_post")
    picker_style: Mapped[str] = mapped_column(String(32), default="reactions")
    behavior: Mapped[str] = mapped_column(String(32), default="toggle")
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    options: Mapped[list["ReactionRoleOption"]] = relationship(
        back_populates="menu",
        cascade="all, delete-orphan",
        order_by="ReactionRoleOption.position",
        lazy="selectin",
    )


class ReactionRoleOption(Base):
    __tablename__ = "reaction_role_options"
    __table_args__ = (
        UniqueConstraint("menu_id", "position", name="uq_reaction_role_options_menu_position"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    menu_id: Mapped[str] = mapped_column(
        ForeignKey("reaction_role_menus.id", ondelete="CASCADE"),
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(100))
    role_id: Mapped[str] = mapped_column(String(32))
    emoji: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(String(100), default="")

    menu: Mapped[ReactionRoleMenu] = relationship(back_populates="options")
