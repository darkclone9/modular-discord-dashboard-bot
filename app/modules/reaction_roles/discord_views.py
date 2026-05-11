from collections.abc import Sequence

import discord
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.reaction_roles.discord_gateway import DiscordReactionRolesGateway
from app.modules.reaction_roles.models import ReactionRoleMenu
from app.modules.reaction_roles.service import ReactionRolesService, ReactionRoleValidationError


class ReactionRoleButtonView(discord.ui.View):
    def __init__(
        self,
        menu: ReactionRoleMenu,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(timeout=None)
        self.menu_id = menu.id
        self.session_factory = session_factory
        for option in menu.options[:25]:
            button = discord.ui.Button(
                label=option.label,
                emoji=option.emoji,
                style=discord.ButtonStyle.secondary,
                custom_id=f"reaction_roles:button:{menu.id}:{option.id}",
            )
            button.callback = self._button_callback(option.id)
            self.add_item(button)

    def _button_callback(self, option_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            await handle_component_selection(
                interaction,
                menu_id=self.menu_id,
                option_ids=[option_id],
                session_factory=self.session_factory,
            )

        return callback


class ReactionRoleSelectView(discord.ui.View):
    def __init__(
        self,
        menu: ReactionRoleMenu,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(timeout=None)
        self.add_item(ReactionRoleSelect(menu, session_factory))


class ReactionRoleSelect(discord.ui.Select):
    def __init__(
        self,
        menu: ReactionRoleMenu,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.menu_id = menu.id
        self.session_factory = session_factory
        options = [
            discord.SelectOption(
                label=option.label,
                value=option.id,
                description=option.description or None,
                emoji=option.emoji,
            )
            for option in menu.options[:25]
        ]
        max_values = 1 if menu.behavior == "single" else max(1, len(options))
        super().__init__(
            custom_id=f"reaction_roles:select:{menu.id}",
            placeholder="Choose your role",
            min_values=1,
            max_values=max_values,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await handle_component_selection(
            interaction,
            menu_id=self.menu_id,
            option_ids=self.values,
            session_factory=self.session_factory,
        )


async def handle_component_selection(
    interaction: discord.Interaction,
    *,
    menu_id: str,
    option_ids: Sequence[str],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if interaction.guild_id is None:
        await interaction.response.send_message(
            "Reaction roles only work in servers.",
            ephemeral=True,
        )
        return
    await interaction.response.defer(ephemeral=True)
    async with session_factory() as db:
        service = ReactionRolesService(db)
        try:
            await service.handle_component_selection(
                guild_id=str(interaction.guild_id),
                menu_id=menu_id,
                user_id=str(interaction.user.id),
                option_ids=option_ids,
                gateway=DiscordReactionRolesGateway(interaction.client, session_factory),
            )
        except ReactionRoleValidationError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
            return
        except PermissionError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
            return
    await interaction.followup.send("Your role selection has been updated.", ephemeral=True)


def view_for_menu(
    menu: ReactionRoleMenu,
    session_factory: async_sessionmaker[AsyncSession],
) -> discord.ui.View | None:
    if menu.picker_style == "buttons":
        return ReactionRoleButtonView(menu, session_factory)
    if menu.picker_style == "select":
        return ReactionRoleSelectView(menu, session_factory)
    return None


def describe_options(menu: ReactionRoleMenu) -> str:
    lines: list[str] = []
    for option in menu.options:
        emoji = f"{option.emoji} " if option.emoji else ""
        lines.append(f"{emoji}{option.label} - <@&{option.role_id}>")
    return "\n".join(lines)
