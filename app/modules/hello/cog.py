import discord
from discord.ext import commands


class HelloCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="hello", description="Check that the bot is alive.")
    async def hello(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="Hello",
            description="The modular bot scaffold is running.",
            color=discord.Color.blurple(),
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelloCog(bot))
