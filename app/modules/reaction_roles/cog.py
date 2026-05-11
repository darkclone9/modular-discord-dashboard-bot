from typing import cast

import discord
import structlog
from core.db import get_session_factory
from discord import app_commands
from discord.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.reaction_roles.discord_gateway import DiscordReactionRolesGateway
from app.modules.reaction_roles.discord_views import view_for_menu
from app.modules.reaction_roles.models import ReactionRoleMenu
from app.modules.reaction_roles.schemas import (
    MenuBehavior,
    PickerStyle,
    ReactionRoleMenuCreate,
    ReactionRoleMenuUpdate,
    ReactionRoleOptionCreate,
)
from app.modules.reaction_roles.service import (
    NotFoundError,
    ReactionRolesService,
    ReactionRoleValidationError,
)

log = structlog.get_logger(__name__)


class ReactionRolesCog(commands.Cog):
    reactionroles = app_commands.Group(
        name="reactionroles",
        description="Create and manage reaction role menus.",
    )

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.session_factory = get_session_factory()

    async def cog_load(self) -> None:
        await self.register_persistent_views()
        self.publish_enabled_menus.start()

    async def cog_unload(self) -> None:
        self.publish_enabled_menus.cancel()

    async def register_persistent_views(self) -> None:
        async with self.session_factory() as db:
            result = await db.execute(
                select(ReactionRoleMenu)
                .options(selectinload(ReactionRoleMenu.options))
                .where(
                    ReactionRoleMenu.is_enabled.is_(True),
                    ReactionRoleMenu.message_id.is_not(None),
                    ReactionRoleMenu.picker_style.in_(["buttons", "select"]),
                )
            )
            for menu in result.scalars().unique():
                view = view_for_menu(menu, self.session_factory)
                if view is not None:
                    self.bot.add_view(view)

    @tasks.loop(seconds=45)
    async def publish_enabled_menus(self) -> None:
        await self.bot.wait_until_ready()
        async with self.session_factory() as db:
            result = await db.execute(
                select(ReactionRoleMenu)
                .options(selectinload(ReactionRoleMenu.options))
                .where(ReactionRoleMenu.is_enabled.is_(True))
            )
            service = ReactionRolesService(db)
            gateway = DiscordReactionRolesGateway(self.bot, self.session_factory)
            for menu in result.scalars().unique():
                try:
                    await service.publish_menu(menu.guild_id, menu.id, gateway)
                except Exception as exc:
                    log.warning("reaction_role_publish_failed", menu_id=menu.id, error=str(exc))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return
        if payload.member and payload.member.bot:
            return
        async with self.session_factory() as db:
            await ReactionRolesService(db).handle_reaction_add(
                guild_id=str(payload.guild_id),
                message_id=str(payload.message_id),
                user_id=str(payload.user_id),
                emoji=str(payload.emoji),
                gateway=DiscordReactionRolesGateway(self.bot, self.session_factory),
            )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return
        async with self.session_factory() as db:
            await ReactionRolesService(db).handle_reaction_remove(
                guild_id=str(payload.guild_id),
                message_id=str(payload.message_id),
                user_id=str(payload.user_id),
                emoji=str(payload.emoji),
                gateway=DiscordReactionRolesGateway(self.bot, self.session_factory),
            )

    @reactionroles.command(name="create", description="Create and publish a reaction role menu.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guild_only()
    @app_commands.describe(
        name="Internal menu name.",
        channel="Channel where the role menu should be posted.",
        role="First role to offer.",
        emoji="Emoji for the first role.",
        title="Public message title.",
        description="Public message description.",
        style="reactions, buttons, or select.",
        behavior="toggle, add_only, or single.",
    )
    async def create_menu(
        self,
        interaction: discord.Interaction,
        name: str,
        channel: discord.TextChannel,
        role: discord.Role,
        emoji: str,
        title: str = "Choose your roles",
        description: str = "",
        style: str = "reactions",
        behavior: str = "toggle",
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("Run this in a server.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        payload = ReactionRoleMenuCreate(
            name=name,
            channel_id=str(channel.id),
            picker_style=normalize_style(style),
            behavior=normalize_behavior(behavior),
            title=title,
            description=description,
            options=[
                ReactionRoleOptionCreate(
                    label=role.name,
                    role_id=str(role.id),
                    emoji=emoji,
                )
            ],
        )
        async with self.session_factory() as db:
            service = ReactionRolesService(db)
            try:
                menu = await service.create_menu(str(interaction.guild_id), payload)
                menu = await service.publish_menu(
                    str(interaction.guild_id),
                    menu.id,
                    DiscordReactionRolesGateway(self.bot, self.session_factory),
                )
            except (ReactionRoleValidationError, PermissionError, ValueError) as exc:
                await interaction.followup.send(str(exc), ephemeral=True)
                return
        await interaction.followup.send(
            f"Created **{menu.name}** in {channel.mention}. Menu ID: `{menu.id}`",
            ephemeral=True,
        )

    @reactionroles.command(name="add_option", description="Add a role option to a menu.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def add_option(
        self,
        interaction: discord.Interaction,
        menu_id: str,
        role: discord.Role,
        emoji: str,
        label: str | None = None,
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("Run this in a server.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        async with self.session_factory() as db:
            service = ReactionRolesService(db)
            try:
                menu = await service.get_menu(str(interaction.guild_id), menu_id)
                options = [
                    ReactionRoleOptionCreate(
                        label=option.label,
                        role_id=option.role_id,
                        emoji=option.emoji,
                        description=option.description,
                    )
                    for option in menu.options
                ]
                options.append(
                    ReactionRoleOptionCreate(
                        label=label or role.name,
                        role_id=str(role.id),
                        emoji=emoji,
                    )
                )
                await service.update_menu(
                    str(interaction.guild_id),
                    menu_id,
                    ReactionRoleMenuUpdate(options=options),
                )
                await service.publish_menu(
                    str(interaction.guild_id),
                    menu_id,
                    DiscordReactionRolesGateway(self.bot, self.session_factory),
                )
            except (NotFoundError, ReactionRoleValidationError, PermissionError) as exc:
                await interaction.followup.send(str(exc), ephemeral=True)
                return
        await interaction.followup.send("Role option added and menu refreshed.", ephemeral=True)

    @reactionroles.command(name="publish", description="Publish or refresh a reaction role menu.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def publish_menu(self, interaction: discord.Interaction, menu_id: str) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("Run this in a server.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        async with self.session_factory() as db:
            try:
                await ReactionRolesService(db).publish_menu(
                    str(interaction.guild_id),
                    menu_id,
                    DiscordReactionRolesGateway(self.bot, self.session_factory),
                )
            except (NotFoundError, ReactionRoleValidationError, PermissionError, ValueError) as exc:
                await interaction.followup.send(str(exc), ephemeral=True)
                return
        await interaction.followup.send("Reaction role menu published.", ephemeral=True)

    @reactionroles.command(name="disable", description="Disable a reaction role menu.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def disable_menu(self, interaction: discord.Interaction, menu_id: str) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("Run this in a server.", ephemeral=True)
            return
        async with self.session_factory() as db:
            try:
                await ReactionRolesService(db).disable_menu(str(interaction.guild_id), menu_id)
            except NotFoundError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
        await interaction.response.send_message("Reaction role menu disabled.", ephemeral=True)

    @reactionroles.command(name="delete", description="Delete a reaction role menu config.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def delete_menu(self, interaction: discord.Interaction, menu_id: str) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("Run this in a server.", ephemeral=True)
            return
        async with self.session_factory() as db:
            try:
                await ReactionRolesService(db).delete_menu(str(interaction.guild_id), menu_id)
            except NotFoundError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
        await interaction.response.send_message("Reaction role menu deleted.", ephemeral=True)


def normalize_style(value: str) -> PickerStyle:
    normalized = value.strip().lower()
    if normalized in {"reactions", "buttons", "select"}:
        return cast(PickerStyle, normalized)
    return "reactions"


def normalize_behavior(value: str) -> MenuBehavior:
    normalized = value.strip().lower()
    if normalized in {"toggle", "add_only", "single"}:
        return cast(MenuBehavior, normalized)
    return "toggle"


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRolesCog(bot))
