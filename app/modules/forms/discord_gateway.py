from collections.abc import Sequence

import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.forms.models import Form, Submission
from app.modules.forms.service import ThreadPost


class DiscordFormsGateway:
    def __init__(
        self,
        bot: commands.Bot,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.bot = bot
        self.session_factory = session_factory

    async def create_review_thread(
        self,
        *,
        form: Form,
        submission: Submission,
        thread_name: str,
        submitter_id: str,
    ) -> str:
        channel = await self._fetch_channel(form.review_channel_id)
        if not isinstance(channel, discord.TextChannel):
            raise TypeError("Review channel must be a text channel")

        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            invitable=False,
            reason=f"Application submission {submission.id}",
        )
        try:
            member = channel.guild.get_member(
                int(submitter_id)
            ) or await channel.guild.fetch_member(int(submitter_id))
            await thread.add_user(member)
        except discord.HTTPException:
            pass
        return str(thread.id)

    async def post_submission_review(
        self,
        *,
        thread_id: str,
        submission_id: str,
        content: str,
        embed: dict[str, object],
    ) -> ThreadPost:
        from app.modules.forms.discord_views import ReviewActionsView

        thread = await self._fetch_channel(thread_id)
        if not isinstance(thread, discord.Thread):
            raise TypeError("Review destination must be a thread")

        message = await thread.send(
            content=content,
            embed=to_discord_embed(embed),
            view=ReviewActionsView(submission_id, self.session_factory),
            allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
        )
        return ThreadPost(message_id=str(message.id))

    async def dm_user(self, *, user_id: str, content: str) -> None:
        user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
        await user.send(content)

    async def assign_role(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
        reason: str,
    ) -> None:
        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            guild = await self.bot.fetch_guild(int(guild_id))
        member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        role = guild.get_role(int(role_id))
        if role is None:
            role = guild.get_role(int(role_id))
        if role is None:
            raise LookupError("Auto-role not found")
        await member.add_roles(role, reason=reason)

    async def lock_thread(self, *, thread_id: str) -> None:
        channel = await self._fetch_channel(thread_id)
        if isinstance(channel, discord.Thread):
            await channel.edit(locked=True, archived=True, reason="Application review complete")

    async def delete_thread(self, *, thread_id: str, reason: str) -> None:
        channel = await self._fetch_channel(thread_id)
        if isinstance(channel, discord.Thread):
            await channel.delete(reason=reason)

    async def post_thread_message(self, *, thread_id: str, content: str) -> None:
        channel = await self._fetch_channel(thread_id)
        if not isinstance(channel, discord.Thread):
            raise TypeError("Review destination must be a thread")
        await channel.send(
            content,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )

    async def _fetch_channel(self, channel_id: str) -> discord.abc.GuildChannel | discord.Thread:
        channel = self.bot.get_channel(int(channel_id))
        if channel is not None:
            return channel
        return await self.bot.fetch_channel(int(channel_id))


def to_discord_embed(payload: dict[str, object]) -> discord.Embed:
    embed = discord.Embed(
        title=str(payload.get("title") or "Application"),
        description=str(payload.get("description") or ""),
        color=discord.Color.blurple(),
    )
    for field in payload.get("fields", []):
        if not isinstance(field, dict):
            continue
        embed.add_field(
            name=str(field.get("name") or "Field"),
            value=str(field.get("value") or "(empty)")[:1024],
            inline=bool(field.get("inline", False)),
        )
    footer = payload.get("footer")
    if isinstance(footer, dict) and footer.get("text"):
        embed.set_footer(text=str(footer["text"]))
    return embed


def role_ids_from_member(member: discord.Member | discord.User) -> set[str]:
    roles: Sequence[discord.Role] = getattr(member, "roles", [])
    return {str(role.id) for role in roles}
