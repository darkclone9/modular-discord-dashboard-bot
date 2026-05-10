import discord
import structlog
from core.config import get_settings
from discord.ext import commands

from app.bot.discovery import discover_cog_extensions

log = structlog.get_logger(__name__)


class ModularBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = get_settings()
        self._synced_guild_ids: set[int] = set()

    async def setup_hook(self) -> None:
        for extension in discover_cog_extensions():
            await self.load_extension(extension)
            log.info("loaded_cog_extension", extension=extension)

    async def on_ready(self) -> None:
        log.info("bot_ready", user=str(self.user), guilds=len(self.guilds))
        if self.settings.sync_application_commands:
            for guild in self.guilds:
                await self._sync_commands_for_guild(guild)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        if self.settings.sync_application_commands:
            await self._sync_commands_for_guild(guild)

    async def _sync_commands_for_guild(self, guild: discord.Guild) -> None:
        if guild.id in self._synced_guild_ids:
            return
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        self._synced_guild_ids.add(guild.id)
        log.info("synced_application_commands", guild_id=guild.id, count=len(synced))
