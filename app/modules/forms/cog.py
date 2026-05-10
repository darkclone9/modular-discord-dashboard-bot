from datetime import UTC, datetime

import discord
import structlog
from core.config import get_settings
from core.db import get_session_factory
from discord.ext import commands, tasks
from sqlalchemy import select

from app.modules.forms.discord_views import ApplyView, ReviewActionsView
from app.modules.forms.models import Form, Submission

log = structlog.get_logger(__name__)


class FormsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.session_factory = get_session_factory()
        self.publish_pending_forms.change_interval(
            seconds=self.settings.publish_poll_interval_seconds
        )

    async def cog_load(self) -> None:
        await self.register_persistent_views()
        self.publish_pending_forms.start()

    async def cog_unload(self) -> None:
        self.publish_pending_forms.cancel()

    async def register_persistent_views(self) -> None:
        async with self.session_factory() as db:
            forms_result = await db.execute(
                select(Form).where(Form.is_published.is_(True), Form.is_archived.is_(False))
            )
            for form in forms_result.scalars():
                self.bot.add_view(ApplyView(form.id, self.session_factory))

            submissions_result = await db.execute(
                select(Submission).where(
                    Submission.status == "pending",
                    Submission.thread_id.is_not(None),
                )
            )
            for submission in submissions_result.scalars():
                self.bot.add_view(ReviewActionsView(submission.id, self.session_factory))

    @tasks.loop(seconds=30)
    async def publish_pending_forms(self) -> None:
        await self.bot.wait_until_ready()
        async with self.session_factory() as db:
            result = await db.execute(
                select(Form).where(
                    Form.is_published.is_(True),
                    Form.is_archived.is_(False),
                    Form.published_message_id.is_(None),
                )
            )
            forms = list(result.scalars())
            for form in forms:
                try:
                    message = await self._post_apply_message(form)
                except Exception as exc:
                    log.warning("form_publish_failed", form_id=form.id, error=str(exc))
                    continue
                form.published_message_id = str(message.id)
                form.published_at = datetime.now(UTC)
                self.bot.add_view(ApplyView(form.id, self.session_factory))
            await db.commit()

    async def _post_apply_message(self, form: Form) -> discord.Message:
        channel = self.bot.get_channel(int(form.post_channel_id))
        if channel is None:
            channel = await self.bot.fetch_channel(int(form.post_channel_id))
        if not isinstance(channel, discord.TextChannel):
            raise TypeError("Configured apply channel must be a text channel")
        embed = discord.Embed(
            title=form.title,
            description=form.description or "Click Apply to begin.",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Applications are handled privately.")
        return await channel.send(
            embed=embed,
            view=ApplyView(form.id, self.session_factory),
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FormsCog(bot))
