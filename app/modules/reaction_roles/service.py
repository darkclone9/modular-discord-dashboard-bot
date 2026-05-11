from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.reaction_roles.models import ReactionRoleMenu, ReactionRoleOption
from app.modules.reaction_roles.schemas import (
    ReactionRoleMenuCreate,
    ReactionRoleMenuRead,
    ReactionRoleMenuUpdate,
    ReactionRoleOptionCreate,
)


class NotFoundError(LookupError):
    pass


class ReactionRoleValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class ReactionRolesGateway(Protocol):
    async def publish_menu(self, menu: ReactionRoleMenu) -> str: ...

    async def assign_role(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
        reason: str,
    ) -> None: ...

    async def remove_role(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
        reason: str,
    ) -> None: ...


class ReactionRolesService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_menus(self, guild_id: str) -> list[ReactionRoleMenu]:
        result = await self.db.execute(
            select(ReactionRoleMenu)
            .options(selectinload(ReactionRoleMenu.options))
            .where(ReactionRoleMenu.guild_id == guild_id)
            .order_by(ReactionRoleMenu.created_at.desc())
        )
        return list(result.scalars().unique())

    async def list_enabled_component_menus(self) -> list[ReactionRoleMenu]:
        result = await self.db.execute(
            select(ReactionRoleMenu)
            .options(selectinload(ReactionRoleMenu.options))
            .where(
                ReactionRoleMenu.is_enabled.is_(True),
                ReactionRoleMenu.message_id.is_not(None),
                ReactionRoleMenu.picker_style.in_(["buttons", "select"]),
            )
        )
        return list(result.scalars().unique())

    async def create_menu(self, guild_id: str, payload: ReactionRoleMenuCreate) -> ReactionRoleMenu:
        validate_menu_payload(payload)
        menu = ReactionRoleMenu(
            guild_id=guild_id,
            name=payload.name,
            channel_id=payload.channel_id,
            message_id=payload.message_id,
            message_mode=payload.message_mode,
            picker_style=payload.picker_style,
            behavior=payload.behavior,
            title=payload.title,
            description=payload.description,
            is_enabled=payload.is_enabled,
        )
        menu.options = build_options(payload.options)
        self.db.add(menu)
        await self.db.commit()
        await self.db.refresh(menu, ["options"])
        return menu

    async def get_menu(self, guild_id: str, menu_id: str) -> ReactionRoleMenu:
        result = await self.db.execute(
            select(ReactionRoleMenu)
            .options(selectinload(ReactionRoleMenu.options))
            .where(ReactionRoleMenu.guild_id == guild_id, ReactionRoleMenu.id == menu_id)
        )
        menu = result.scalar_one_or_none()
        if menu is None:
            raise NotFoundError("Reaction role menu not found")
        return menu

    async def update_menu(
        self,
        guild_id: str,
        menu_id: str,
        payload: ReactionRoleMenuUpdate,
    ) -> ReactionRoleMenu:
        menu = await self.get_menu(guild_id, menu_id)
        if payload.name is not None:
            menu.name = payload.name
        if payload.channel_id is not None:
            menu.channel_id = payload.channel_id
        if payload.message_id is not None:
            menu.message_id = payload.message_id or None
        if payload.message_mode is not None:
            menu.message_mode = payload.message_mode
        if payload.picker_style is not None:
            menu.picker_style = payload.picker_style
        if payload.behavior is not None:
            menu.behavior = payload.behavior
        if payload.title is not None:
            menu.title = payload.title
        if payload.description is not None:
            menu.description = payload.description
        if payload.is_enabled is not None:
            menu.is_enabled = payload.is_enabled
        if payload.options is not None:
            validate_options(payload.options, picker_style=menu.picker_style)
            await self.db.execute(
                delete(ReactionRoleOption).where(ReactionRoleOption.menu_id == menu.id)
            )
            menu.options = build_options(payload.options)

        validate_menu(menu)
        await self.db.commit()
        await self.db.refresh(menu, ["options"])
        return menu

    async def delete_menu(self, guild_id: str, menu_id: str) -> None:
        menu = await self.get_menu(guild_id, menu_id)
        await self.db.delete(menu)
        await self.db.commit()

    async def disable_menu(self, guild_id: str, menu_id: str) -> ReactionRoleMenu:
        menu = await self.get_menu(guild_id, menu_id)
        menu.is_enabled = False
        await self.db.commit()
        await self.db.refresh(menu, ["options"])
        return menu

    async def enable_menu(self, guild_id: str, menu_id: str) -> ReactionRoleMenu:
        menu = await self.get_menu(guild_id, menu_id)
        validate_menu(menu)
        menu.is_enabled = True
        await self.db.commit()
        await self.db.refresh(menu, ["options"])
        return menu

    async def publish_menu(
        self,
        guild_id: str,
        menu_id: str,
        gateway: ReactionRolesGateway,
    ) -> ReactionRoleMenu:
        menu = await self.get_menu(guild_id, menu_id)
        validate_menu(menu)
        message_id = await gateway.publish_menu(menu)
        menu.message_id = message_id
        menu.is_enabled = True
        await self.db.commit()
        await self.db.refresh(menu, ["options"])
        return menu

    async def handle_reaction_add(
        self,
        *,
        guild_id: str,
        message_id: str,
        user_id: str,
        emoji: str,
        gateway: ReactionRolesGateway,
    ) -> ReactionRoleMenu | None:
        menu, option = await self._find_reaction_option(guild_id, message_id, emoji)
        if menu is None or option is None:
            return None
        await self._apply_option(menu, option, user_id=user_id, gateway=gateway)
        return menu

    async def handle_reaction_remove(
        self,
        *,
        guild_id: str,
        message_id: str,
        user_id: str,
        emoji: str,
        gateway: ReactionRolesGateway,
    ) -> ReactionRoleMenu | None:
        menu, option = await self._find_reaction_option(guild_id, message_id, emoji)
        if menu is None or option is None:
            return None
        if menu.behavior == "toggle":
            await gateway.remove_role(
                guild_id=menu.guild_id,
                user_id=user_id,
                role_id=option.role_id,
                reason=f"Reaction role removed from {menu.name}",
            )
        return menu

    async def handle_component_selection(
        self,
        *,
        guild_id: str,
        menu_id: str,
        user_id: str,
        option_ids: Sequence[str],
        gateway: ReactionRolesGateway,
    ) -> ReactionRoleMenu:
        menu = await self.get_menu(guild_id, menu_id)
        if not menu.is_enabled:
            raise ReactionRoleValidationError(["This reaction role menu is disabled"])
        selected = [option for option in menu.options if option.id in set(option_ids)]
        if not selected:
            raise ReactionRoleValidationError(["No matching role option was selected"])
        for option in selected:
            await self._apply_option(menu, option, user_id=user_id, gateway=gateway)
        return menu

    async def _find_reaction_option(
        self,
        guild_id: str,
        message_id: str,
        emoji: str,
    ) -> tuple[ReactionRoleMenu | None, ReactionRoleOption | None]:
        result = await self.db.execute(
            select(ReactionRoleMenu)
            .options(selectinload(ReactionRoleMenu.options))
            .where(
                ReactionRoleMenu.guild_id == guild_id,
                ReactionRoleMenu.message_id == message_id,
                ReactionRoleMenu.is_enabled.is_(True),
                ReactionRoleMenu.picker_style == "reactions",
            )
        )
        for menu in result.scalars().unique():
            for option in menu.options:
                if option.emoji == emoji:
                    return menu, option
        return None, None

    async def _apply_option(
        self,
        menu: ReactionRoleMenu,
        option: ReactionRoleOption,
        *,
        user_id: str,
        gateway: ReactionRolesGateway,
    ) -> None:
        if menu.behavior == "single":
            for other in menu.options:
                if other.role_id != option.role_id:
                    await gateway.remove_role(
                        guild_id=menu.guild_id,
                        user_id=user_id,
                        role_id=other.role_id,
                        reason=f"Reaction role single-choice cleanup from {menu.name}",
                    )
        await gateway.assign_role(
            guild_id=menu.guild_id,
            user_id=user_id,
            role_id=option.role_id,
            reason=f"Reaction role selected from {menu.name}",
        )


def menu_to_read(menu: ReactionRoleMenu) -> ReactionRoleMenuRead:
    return ReactionRoleMenuRead.model_validate(menu)


def build_options(payload_options: Sequence[ReactionRoleOptionCreate]) -> list[ReactionRoleOption]:
    return [
        ReactionRoleOption(
            position=index,
            label=option.label,
            role_id=option.role_id,
            emoji=normalize_emoji(option.emoji),
            description=option.description,
        )
        for index, option in enumerate(payload_options)
    ]


def validate_menu_payload(payload: ReactionRoleMenuCreate) -> None:
    errors = validation_errors(
        message_mode=payload.message_mode,
        picker_style=payload.picker_style,
        message_id=payload.message_id,
        options=payload.options,
    )
    if errors:
        raise ReactionRoleValidationError(errors)


def validate_menu(menu: ReactionRoleMenu) -> None:
    option_payload = [
        ReactionRoleOptionCreate(
            label=option.label,
            role_id=option.role_id,
            emoji=option.emoji,
            description=option.description,
        )
        for option in menu.options
    ]
    errors = validation_errors(
        message_mode=menu.message_mode,
        picker_style=menu.picker_style,
        message_id=menu.message_id,
        options=option_payload,
    )
    if errors:
        raise ReactionRoleValidationError(errors)


def validate_options(options: Sequence[ReactionRoleOptionCreate], *, picker_style: str) -> None:
    errors = validation_errors(
        message_mode="bot_post",
        picker_style=picker_style,
        message_id=None,
        options=options,
    )
    if errors:
        raise ReactionRoleValidationError(errors)


def validation_errors(
    *,
    message_mode: str,
    picker_style: str,
    message_id: str | None,
    options: Sequence[ReactionRoleOptionCreate],
) -> list[str]:
    errors: list[str] = []
    if message_mode == "existing_message" and not message_id:
        errors.append("Existing-message menus require a message ID")
    if message_mode == "existing_message" and picker_style != "reactions":
        errors.append("Existing-message menus can only use classic reactions")
    if len(options) > 25:
        errors.append("Reaction role menus can have at most 25 options")

    role_ids = [option.role_id for option in options]
    duplicate_roles = sorted({role_id for role_id in role_ids if role_ids.count(role_id) > 1})
    if duplicate_roles:
        errors.append(f"Duplicate role mapping(s): {', '.join(duplicate_roles)}")

    emojis = [normalize_emoji(option.emoji) for option in options if normalize_emoji(option.emoji)]
    duplicate_emojis = sorted({emoji for emoji in emojis if emojis.count(emoji) > 1})
    if duplicate_emojis:
        errors.append(f"Duplicate emoji mapping(s): {', '.join(duplicate_emojis)}")
    if picker_style == "reactions":
        missing = [option.label for option in options if not normalize_emoji(option.emoji)]
        if missing:
            errors.append("Classic reaction options require an emoji")
    return errors


def normalize_emoji(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
