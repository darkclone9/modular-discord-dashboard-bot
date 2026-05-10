from collections.abc import Sequence

import discord
import structlog
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.forms.models import Form, Submission
from app.modules.forms.service import ThreadPost

log = structlog.get_logger(__name__)


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
        await add_role_members_to_thread(thread, form.thread_access_role_ids)
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

    async def add_form_role_members_to_thread(self, *, thread_id: str, form: Form) -> None:
        channel = await self._fetch_channel(thread_id)
        if not isinstance(channel, discord.Thread):
            raise TypeError("Review destination must be a thread")
        await add_role_members_to_thread(channel, form.thread_access_role_ids)

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


async def add_role_members_to_thread(
    thread: discord.Thread,
    role_ids: Sequence[str],
) -> None:
    normalized_role_ids = normalize_role_ids(role_ids)
    if not normalized_role_ids:
        return

    members = cached_members_with_roles(thread.guild, normalized_role_ids)
    fetched_member_count = 0
    try:
        async for member in thread.guild.fetch_members(limit=None):
            fetched_member_count += 1
            if member_matches_roles(member, normalized_role_ids):
                members[member.id] = member
    except (discord.ClientException, discord.Forbidden, discord.HTTPException) as exc:
        log.warning(
            "forms_thread_role_member_fetch_failed",
            guild_id=thread.guild.id,
            thread_id=thread.id,
            role_ids=sorted(normalized_role_ids),
            error=str(exc),
        )

    added = 0
    for member in members.values():
        if member.bot:
            continue
        try:
            await thread.add_user(member)
        except discord.HTTPException as exc:
            log.warning(
                "forms_thread_member_add_failed",
                guild_id=thread.guild.id,
                thread_id=thread.id,
                member_id=member.id,
                error=str(exc),
            )
            continue
        added += 1

    log.info(
        "forms_thread_role_members_added",
        guild_id=thread.guild.id,
        thread_id=thread.id,
        role_ids=sorted(normalized_role_ids),
        cached_matches=len(members),
        fetched_members=fetched_member_count,
        added=added,
    )


def cached_members_with_roles(
    guild: discord.Guild,
    role_ids: set[int],
) -> dict[int, discord.Member]:
    members: dict[int, discord.Member] = {}
    for role_id in role_ids:
        try:
            role = guild.get_role(role_id)
        except TypeError:
            continue
        if role is None:
            continue
        for member in role.members:
            if member_matches_roles(member, role_ids):
                members[member.id] = member
    return members


def member_matches_roles(member: discord.Member, role_ids: set[int]) -> bool:
    return not member.bot and any(role.id in role_ids for role in member.roles)


def normalize_role_ids(role_ids: Sequence[str]) -> set[int]:
    normalized: set[int] = set()
    for role_id in role_ids:
        try:
            normalized.add(int(role_id))
        except ValueError:
            continue
    return normalized
