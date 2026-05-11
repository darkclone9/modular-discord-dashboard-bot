import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.reaction_roles.models import ReactionRoleMenu


class DiscordReactionRolesGateway:
    def __init__(
        self,
        bot: commands.Bot,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.bot = bot
        self.session_factory = session_factory

    async def publish_menu(self, menu: ReactionRoleMenu) -> str:
        channel = await self._fetch_channel(menu.channel_id)
        if not isinstance(channel, discord.TextChannel | discord.Thread):
            raise TypeError("Reaction role menus must be published to a text channel or thread")

        embed = to_menu_embed(menu)
        view = build_view(menu, self.session_factory)
        if menu.message_mode == "existing_message":
            if not menu.message_id:
                raise ValueError("Existing-message menus require a message ID")
            message = await channel.fetch_message(int(menu.message_id))
        elif menu.message_id:
            message = await channel.fetch_message(int(menu.message_id))
            await message.edit(embed=embed, view=view)
        else:
            message = await channel.send(
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )

        if menu.picker_style == "reactions":
            for option in menu.options:
                if option.emoji:
                    await message.add_reaction(option.emoji)
        return str(message.id)

    async def assign_role(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
        reason: str,
    ) -> None:
        guild = await self._fetch_guild(guild_id)
        member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        role = guild.get_role(int(role_id))
        if role is None:
            raise LookupError("Role not found")
        ensure_can_manage_role(guild, role)
        await member.add_roles(role, reason=reason)

    async def remove_role(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
        reason: str,
    ) -> None:
        guild = await self._fetch_guild(guild_id)
        member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        role = guild.get_role(int(role_id))
        if role is None:
            return
        ensure_can_manage_role(guild, role)
        await member.remove_roles(role, reason=reason)

    async def _fetch_channel(self, channel_id: str) -> discord.abc.GuildChannel | discord.Thread:
        channel = self.bot.get_channel(int(channel_id))
        if channel is not None:
            return channel
        return await self.bot.fetch_channel(int(channel_id))

    async def _fetch_guild(self, guild_id: str) -> discord.Guild:
        guild = self.bot.get_guild(int(guild_id))
        if guild is not None:
            return guild
        return await self.bot.fetch_guild(int(guild_id))


def build_view(
    menu: ReactionRoleMenu,
    session_factory: async_sessionmaker[AsyncSession],
) -> discord.ui.View | None:
    from app.modules.reaction_roles.discord_views import view_for_menu

    return view_for_menu(menu, session_factory)


def to_menu_embed(menu: ReactionRoleMenu) -> discord.Embed:
    from app.modules.reaction_roles.discord_views import describe_options

    embed = discord.Embed(
        title=menu.title,
        description=menu.description or "Choose a role below.",
        color=discord.Color.blurple(),
    )
    if menu.picker_style == "reactions":
        embed.add_field(
            name="Roles",
            value=describe_options(menu) or "No roles configured.",
            inline=False,
        )
    embed.set_footer(text="Use the menu below to manage your roles.")
    return embed


def ensure_can_manage_role(guild: discord.Guild, role: discord.Role) -> None:
    me = guild.me
    if me is None:
        raise PermissionError("I could not read my server member permissions.")
    if not me.guild_permissions.manage_roles:
        raise PermissionError("I need Manage Roles to update reaction roles.")
    if me.top_role <= role:
        raise PermissionError(f"Move my bot role above {role.name} in the role list.")
