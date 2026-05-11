from datetime import UTC, datetime

import discord
import structlog
from core.db import get_session_factory
from discord import app_commands
from discord.ext import commands, tasks

from app.modules.trackers.discord_gateway import DiscordTrackersGateway
from app.modules.trackers.models import SocialTracker
from app.modules.trackers.providers import fetch_latest_tracker_item
from app.modules.trackers.service import (
    GameCandidate,
    TrackersService,
    format_tracker_message,
)

log = structlog.get_logger(__name__)


class TrackersCog(commands.Cog):
    trackers = app_commands.Group(name="trackers", description="Manage notification trackers.")

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.session_factory = get_session_factory()

    async def cog_load(self) -> None:
        self.poll_social_trackers.start()
        self.collect_game_activity.start()
        self.publish_weekly_game_picks.start()

    async def cog_unload(self) -> None:
        self.poll_social_trackers.cancel()
        self.collect_game_activity.cancel()
        self.publish_weekly_game_picks.cancel()

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        if after.bot or after.guild is None:
            return
        candidates = game_candidates_from_members([after])
        if not candidates:
            return
        async with self.session_factory() as db:
            await TrackersService(db).observe_game_activity(
                guild_id=str(after.guild.id),
                candidates=candidates,
            )

    @tasks.loop(minutes=5)
    async def poll_social_trackers(self) -> None:
        await self.bot.wait_until_ready()
        async with self.session_factory() as db:
            service = TrackersService(db)
            trackers = await service.list_enabled_social_trackers()
            gateway = DiscordTrackersGateway(self.bot)
            for tracker in trackers:
                await self._poll_tracker(service, gateway, tracker)

    @tasks.loop(minutes=10)
    async def collect_game_activity(self) -> None:
        await self.bot.wait_until_ready()
        async with self.session_factory() as db:
            service = TrackersService(db)
            for guild in self.bot.guilds:
                candidates = game_candidates_from_members(guild.members)
                if candidates:
                    await service.observe_game_activity(
                        guild_id=str(guild.id),
                        candidates=candidates,
                    )

    @tasks.loop(minutes=15)
    async def publish_weekly_game_picks(self) -> None:
        await self.bot.wait_until_ready()
        now = datetime.now(UTC)
        gateway = DiscordTrackersGateway(self.bot)
        async with self.session_factory() as db:
            service = TrackersService(db)
            for guild in self.bot.guilds:
                candidates = game_candidates_from_members(guild.members)
                try:
                    await service.create_weekly_game_pick(
                        guild_id=str(guild.id),
                        now=now,
                        gateway=gateway,
                        candidates=candidates,
                    )
                except Exception as exc:
                    log.warning("weekly_game_pick_failed", guild_id=guild.id, error=str(exc))

    @trackers.command(
        name="run_game_pick",
        description="Run the weekly game suggestion pick now for testing.",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def run_game_pick(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None or interaction.guild is None:
            await interaction.response.send_message("Run this in a server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        candidates = game_candidates_from_members(interaction.guild.members)
        async with self.session_factory() as db:
            try:
                pick = await TrackersService(db).create_weekly_game_pick(
                    guild_id=str(interaction.guild_id),
                    now=datetime.now(UTC),
                    gateway=DiscordTrackersGateway(self.bot),
                    candidates=candidates,
                    force=True,
                )
            except Exception as exc:
                log.warning(
                    "manual_game_pick_failed",
                    guild_id=interaction.guild_id,
                    error=str(exc),
                )
                await interaction.followup.send(
                    "I could not run the game pick. Check the announcement channel and my "
                    "permissions there.",
                    ephemeral=True,
                )
                return

        if pick is None:
            await interaction.followup.send(
                "No pick was posted. Make sure the game suggestion settings have an announcement "
                "channel, at least one member has shared a Playing status, and this week has not "
                "already been picked.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            f"Posted this week's game pick: **{pick.game_name}** from {pick.username}.",
            ephemeral=True,
        )

    async def _poll_tracker(
        self,
        service: TrackersService,
        gateway: DiscordTrackersGateway,
        tracker: SocialTracker,
    ) -> None:
        try:
            latest = await fetch_latest_tracker_item(tracker)
        except Exception as exc:
            log.warning("social_tracker_poll_failed", tracker_id=tracker.id, error=str(exc))
            return
        if latest is None:
            await service.mark_tracker_checked(tracker, latest=None)
            return
        should_notify = (
            tracker.last_seen_external_id is not None
            and tracker.last_seen_external_id != latest.external_id
        )
        if should_notify:
            await gateway.send_tracker_message(
                channel_id=tracker.notification_channel_id,
                content=format_tracker_message(tracker, latest),
            )
        await service.mark_tracker_checked(tracker, latest=latest)


def game_candidates_from_members(members: list[discord.Member]) -> list[GameCandidate]:
    candidates: list[GameCandidate] = []
    seen: set[tuple[str, str]] = set()
    for member in members:
        if member.bot:
            continue
        for activity in member.activities:
            if activity.type != discord.ActivityType.playing or not activity.name:
                continue
            key = (str(member.id), activity.name)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                GameCandidate(
                    user_id=str(member.id),
                    username=member.display_name,
                    game_name=activity.name,
                )
            )
    return candidates


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TrackersCog(bot))
