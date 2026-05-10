import re
from datetime import UTC, datetime

import discord
import structlog
from core.config import get_settings
from core.db import get_session_factory
from discord import app_commands
from discord.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
        self._refreshed_form_post_ids: set[str] = set()
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
        viewer_role="Optional role that can view and discuss review threads without approving.",
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
        viewer_role: discord.Role | None = None,
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
        if interaction.guild.me is None:
            await interaction.response.send_message(
                "I could not read my server permissions. Try again in a moment.",
                ephemeral=True,
            )
            return

        missing_permissions = missing_setup_permissions(
            interaction.guild.me,
            apply_channel=apply_channel,
            review_channel=review_channel,
            reviewer_role=reviewer_role,
            viewer_role=viewer_role,
            auto_role=auto_role,
        )
        if missing_permissions:
            await interaction.response.send_message(
                format_missing_permissions(missing_permissions),
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
            viewer_role_ids=[str(viewer_role.id)] if viewer_role else [],
            auto_role_id=str(auto_role.id) if auto_role else None,
            questions=[question_1, question_2, question_3],
        )

        async with self.session_factory() as db:
            service = FormsService(db)
            form: Form | None = None
            try:
                form = await service.create_form(str(interaction.guild_id), payload)
                message = await self._publish_form_now(db, form)
            except Exception as exc:
                await db.rollback()
                if form is not None and form.published_message_id is None:
                    try:
                        await service.delete_form(str(interaction.guild_id), form.id)
                    except Exception as cleanup_exc:
                        log.warning(
                            "server_form_setup_cleanup_failed",
                            guild_id=interaction.guild_id,
                            form_id=form.id,
                            error=str(cleanup_exc),
                        )
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
                select(Form)
                .options(selectinload(Form.fields))
                .where(
                    Form.is_published.is_(True),
                    Form.is_archived.is_(False),
                )
            )
            forms = list(result.scalars())
            for form in forms:
                should_publish = (
                    form.published_message_id is None
                    or form.published_at is None
                    or form.id not in self._refreshed_form_post_ids
                )
                if not should_publish:
                    continue
                try:
                    await self._publish_form_now(db, form)
                except Exception as exc:
                    log.warning("form_publish_failed", form_id=form.id, error=str(exc))
                    continue
                self._refreshed_form_post_ids.add(form.id)

    async def _publish_form_now(self, db: AsyncSession, form: Form) -> discord.Message:
        view = ApplyView(form.id, self.session_factory)
        if form.published_message_id:
            channel = await self._fetch_apply_channel(form)
            try:
                message = await channel.fetch_message(int(form.published_message_id))
            except discord.NotFound:
                form.published_message_id = None
            else:
                await message.edit(
                    embed=build_apply_embed(form),
                    view=view,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                form.published_at = datetime.now(UTC)
                await db.commit()
                return message

        message = await self._post_apply_message(form)
        form.is_published = True
        form.published_message_id = str(message.id)
        form.published_at = datetime.now(UTC)
        self.bot.add_view(ApplyView(form.id, self.session_factory))
        await db.commit()
        return message

    async def _post_apply_message(self, form: Form) -> discord.Message:
        channel = await self._fetch_apply_channel(form)
        return await channel.send(
            embed=build_apply_embed(form),
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


def missing_setup_permissions(
    bot_member: discord.Member,
    *,
    apply_channel: discord.TextChannel,
    review_channel: discord.TextChannel,
    reviewer_role: discord.Role,
    viewer_role: discord.Role | None,
    auto_role: discord.Role | None,
) -> list[str]:
    missing: list[str] = []
    apply_permissions = apply_channel.permissions_for(bot_member)
    if not apply_permissions.view_channel:
        missing.append(f"{apply_channel.mention}: View Channel")
    if not apply_permissions.send_messages:
        missing.append(f"{apply_channel.mention}: Send Messages")
    if not apply_permissions.embed_links:
        missing.append(f"{apply_channel.mention}: Embed Links")

    review_permissions = review_channel.permissions_for(bot_member)
    if not review_permissions.view_channel:
        missing.append(f"{review_channel.mention}: View Channel")
    if not review_permissions.create_private_threads:
        missing.append(f"{review_channel.mention}: Create Private Threads")
    if not review_permissions.send_messages_in_threads:
        missing.append(f"{review_channel.mention}: Send Messages in Threads")
    if not review_permissions.manage_threads:
        missing.append(f"{review_channel.mention}: Manage Threads")
    if not reviewer_role.mentionable and not review_permissions.mention_everyone:
        missing.append(
            f"{review_channel.mention}: Mention @everyone, @here, and All Roles "
            f"or make {reviewer_role.mention} mentionable"
        )
    if (
        viewer_role is not None
        and not viewer_role.mentionable
        and not review_permissions.mention_everyone
    ):
        missing.append(
            f"{review_channel.mention}: Mention @everyone, @here, and All Roles "
            f"or make {viewer_role.mention} mentionable"
        )

    if auto_role is not None:
        if not bot_member.guild_permissions.manage_roles:
            missing.append("Server: Manage Roles")
        elif bot_member.top_role <= auto_role:
            missing.append(f"Move my bot role above {auto_role.mention} in the role list")
    return missing


def format_missing_permissions(missing_permissions: list[str]) -> str:
    missing_lines = "\n".join(f"- {permission}" for permission in missing_permissions)
    return (
        "I need these permissions before I can publish that form:\n"
        f"{missing_lines}\n\n"
        "After you update the server or channel permissions, run `/forms setup` again."
    )


def build_apply_embed(form: Form) -> discord.Embed:
    intro, sections = split_apply_description(form.description)
    embed = discord.Embed(
        title=form.title,
        description=truncate_embed_value(
            intro or "Ready to apply? Click the Apply button below to begin.",
            4096,
        ),
        color=discord.Color.blurple(),
    )
    for title, body in sections[:8]:
        embed.add_field(name=title, value=truncate_embed_value(body), inline=False)

    questions = format_question_list(form)
    if questions:
        embed.add_field(name=f"Questions ({len(form.fields)})", value=questions, inline=False)
    embed.add_field(
        name="How to submit",
        value="Click **Apply** below. Your answers open a private review thread for the team.",
        inline=False,
    )
    embed.set_footer(text="Applications are handled privately by the reviewer team.")
    return embed


def split_apply_description(description: str) -> tuple[str, list[tuple[str, str]]]:
    text = normalize_embed_text(description)
    if not text:
        return "", []

    paragraph_sections = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(paragraph_sections) > 1:
        return paragraph_sections[0], [
            (f"Details {index}", paragraph)
            for index, paragraph in enumerate(paragraph_sections[1:], 1)
        ]

    heading_pattern = re.compile(
        r"\b(What officers do|What we're looking for|What we are looking for|"
        r"Time commitment|How to apply|Requirements|Eligibility|What happens next|Deadline)"
        r"\s*[:.]\s+",
        re.IGNORECASE,
    )
    matches = list(heading_pattern.finditer(text))
    if not matches:
        return split_long_intro(text)

    intro = text[: matches[0].start()].strip()
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((canonical_section_title(match.group(1)), body))
    return intro, sections


def split_long_intro(text: str) -> tuple[str, list[tuple[str, str]]]:
    if len(text) <= 900:
        return text, []
    split_at = text.rfind(". ", 0, 700)
    if split_at == -1:
        split_at = 700
    return text[: split_at + 1].strip(), [("Details", text[split_at + 1 :].strip())]


def normalize_embed_text(value: str) -> str:
    return re.sub(r"[ \t]+", " ", value.replace("\r\n", "\n").replace("\r", "\n")).strip()


def canonical_section_title(value: str) -> str:
    normalized = value.strip().lower()
    titles = {
        "what officers do": "What officers do",
        "what we're looking for": "What we're looking for",
        "what we are looking for": "What we're looking for",
        "time commitment": "Time commitment",
        "how to apply": "How to apply",
        "requirements": "Requirements",
        "eligibility": "Eligibility",
        "what happens next": "What happens next",
        "deadline": "Deadline",
    }
    return titles.get(normalized, value.strip())


def format_question_list(form: Form) -> str:
    if not form.fields:
        return ""
    lines = [f"{index}. {field.label}" for index, field in enumerate(form.fields, 1)]
    return truncate_embed_value("\n".join(lines))


def truncate_embed_value(value: str, limit: int = 1024) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FormsCog(bot))
