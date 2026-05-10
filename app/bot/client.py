import discord
import structlog
from discord.ext import commands

from app.bot.discovery import discover_cog_extensions

log = structlog.get_logger(__name__)


class ModularBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for extension in discover_cog_extensions():
            await self.load_extension(extension)
            log.info("loaded_cog_extension", extension=extension)

    async def on_ready(self) -> None:
        log.info("bot_ready", user=str(self.user), guilds=len(self.guilds))
