from datetime import UTC, datetime

import discord
import structlog
from core.config import get_settings
from core.db import get_session_factory
from discord import app_commands
from discord.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.forms.discord_views import ApplyView, ReviewActionsView
from app.modules.forms.models import Form, Submission
from app.modules.forms.service import (
    DEFAULT_SETUP_QUESTION,
    FormsService,
    build_server_setup_form_payload,
)

log = structlog.get_logger(__name__)


class FormsCog(commands.Cog):
    forms = app_commands.Group(name="forms", description="Configure application forms.")

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

    @forms.command(name="setup", description="Create and publish a starter application form.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.describe(
        title="The public form title members will see.",
        apply_channel="Where the bot should post the public Apply button.",
        review_channel="Where private review threads should be created.",
        reviewer_role="Role that can review submissions and will be pinged.",
        description="Optional public description shown on the application embed.",
        question_1="First required long-text question.",
        question_2="Optional second required long-text question.",
        question_3="Optional third required long-text question.",
        auto_role="Optional role to grant when a submission is approved.",
    )
    async def setup_form(
        self,
        interaction: discord.Interaction,
        title: str,
        apply_channel: discord.TextChannel,
        review_channel: discord.TextChannel,
        reviewer_role: discord.Role,
        description: str = "",
        question_1: str = DEFAULT_SETUP_QUESTION,
        question_2: str | None = None,
        question_3: str | None = None,
        auto_role: discord.Role | None = None,
    ) -> None:
        if interaction.guild_id is None or interaction.guild is None:
            await interaction.response.send_message(
                "Forms can only be set up inside a Discord server.",
                ephemeral=True,
            )
            return
        if not can_manage_guild(interaction.user):
            await interaction.response.send_message(
                "You need Manage Server to set up forms.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        payload = build_server_setup_form_payload(
            title=title,
            description=description,
            post_channel_id=str(apply_channel.id),
            review_channel_id=str(review_channel.id),
            reviewer_role_ids=[str(reviewer_role.id)],
            auto_role_id=str(auto_role.id) if auto_role else None,
            questions=[question_1, question_2, question_3],
        )

        async with self.session_factory() as db:
            try:
                service = FormsService(db)
                form = await service.create_form(str(interaction.guild_id), payload)
                message = await self._publish_form_now(db, form)
            except Exception as exc:
                log.warning(
                    "server_form_setup_failed",
                    guild_id=interaction.guild_id,
                    user_id=interaction.user.id,
                    error=str(exc),
                )
                await interaction.followup.send(
                    "I could not finish publishing that form. Check that I can send messages in "
                    f"{apply_channel.mention}, create private threads in {review_channel.mention}, "
                    f"and mention {reviewer_role.mention}.",
                    ephemeral=True,
                )
                return

        await interaction.followup.send(
            f"Created and published **{form.title}** in {apply_channel.mention} "
            f"as message `{message.id}`. "
            "You can fine-tune questions and messages in the dashboard.",
            ephemeral=True,
        )

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
                    await self._publish_form_now(db, form)
                except Exception as exc:
                    log.warning("form_publish_failed", form_id=form.id, error=str(exc))
                    continue

    async def _publish_form_now(self, db: AsyncSession, form: Form) -> discord.Message:
        if form.published_message_id:
            channel = await self._fetch_apply_channel(form)
            return await channel.fetch_message(int(form.published_message_id))

        message = await self._post_apply_message(form)
        form.is_published = True
        form.published_message_id = str(message.id)
        form.published_at = datetime.now(UTC)
        self.bot.add_view(ApplyView(form.id, self.session_factory))
        await db.commit()
        return message

    async def _post_apply_message(self, form: Form) -> discord.Message:
        channel = await self._fetch_apply_channel(form)
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

    async def _fetch_apply_channel(self, form: Form) -> discord.TextChannel:
        channel = self.bot.get_channel(int(form.post_channel_id))
        if channel is None:
            channel = await self.bot.fetch_channel(int(form.post_channel_id))
        if not isinstance(channel, discord.TextChannel):
            raise TypeError("Configured apply channel must be a text channel")
        return channel


def can_manage_guild(user: discord.Member | discord.User) -> bool:
    permissions = getattr(user, "guild_permissions", None)
    return bool(permissions and permissions.manage_guild)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FormsCog(bot))
