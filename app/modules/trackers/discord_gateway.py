import discord
from discord.ext import commands


class DiscordTrackersGateway:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def send_tracker_message(self, *, channel_id: str, content: str) -> str | None:
        channel = await self._fetch_channel(channel_id)
        if not isinstance(
            channel,
            discord.TextChannel | discord.Thread | discord.VoiceChannel | discord.StageChannel,
        ):
            raise TypeError("Tracker notification destination must be a messageable channel")
        message = await channel.send(
            content,
            allowed_mentions=discord.AllowedMentions(
                everyone=True,
                users=True,
                roles=True,
            ),
        )
        return str(message.id)

    async def send_game_pick(
        self,
        *,
        guild_id: str,
        channel_id: str,
        user_id: str,
        reward_role_id: str | None,
        content: str,
        mention_everyone: bool,
    ) -> str | None:
        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            guild = await self.bot.fetch_guild(int(guild_id))
        if reward_role_id:
            await self._assign_reward_role(guild, user_id=user_id, role_id=reward_role_id)

        channel = await self._fetch_channel(channel_id)
        if not isinstance(
            channel,
            discord.TextChannel | discord.Thread | discord.VoiceChannel | discord.StageChannel,
        ):
            raise TypeError("Game suggestion destination must be a messageable channel")
        message = await channel.send(
            content,
            allowed_mentions=discord.AllowedMentions(
                everyone=mention_everyone,
                users=True,
                roles=True,
            ),
        )
        return str(message.id)

    async def _assign_reward_role(
        self,
        guild: discord.Guild,
        *,
        user_id: str,
        role_id: str,
    ) -> None:
        member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        role = guild.get_role(int(role_id))
        if role is None:
            raise LookupError("Reward role not found")
        await member.add_roles(role, reason="Weekly game suggestion pick")

    async def _fetch_channel(self, channel_id: str) -> discord.abc.Messageable:
        channel = self.bot.get_channel(int(channel_id))
        if channel is not None:
            return channel
        return await self.bot.fetch_channel(int(channel_id))
