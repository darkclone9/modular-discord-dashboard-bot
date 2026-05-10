import discord
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.forms.discord_gateway import DiscordFormsGateway, role_ids_from_member
from app.modules.forms.models import FormField
from app.modules.forms.service import (
    FormsService,
    NotFoundError,
    PendingSubmissionError,
    ReviewerPermissionError,
)
from app.modules.forms.validators import FormValidationError


class FormApplicationModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        form_id: str,
        fields: list[FormField],
        session_factory: async_sessionmaker[AsyncSession],
        page: int = 0,
        answers: dict[str, object] | None = None,
    ) -> None:
        super().__init__(title=truncate("Application", 45))
        self.form_id = form_id
        self.fields = fields
        self.session_factory = session_factory
        self.page = page
        self.answers = answers or {}

        for field in self.current_fields:
            self.add_item(
                discord.ui.TextInput(
                    label=truncate(field.label, 45),
                    custom_id=field.id,
                    required=field.required,
                    style=discord.TextStyle.paragraph
                    if field.field_type == "long_text"
                    else discord.TextStyle.short,
                    placeholder=placeholder_for(field),
                    max_length=4000 if field.field_type == "long_text" else 200,
                )
            )

    @property
    def current_fields(self) -> list[FormField]:
        start = self.page * 5
        return self.fields[start : start + 5]

    async def on_submit(self, interaction: discord.Interaction) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.TextInput):
                self.answers[child.custom_id] = child.value

        if (self.page + 1) * 5 < len(self.fields):
            await interaction.response.send_modal(
                FormApplicationModal(
                    form_id=self.form_id,
                    fields=self.fields,
                    session_factory=self.session_factory,
                    page=self.page + 1,
                    answers=self.answers,
                )
            )
            return

        async with self.session_factory() as db:
            service = FormsService(db)
            gateway = DiscordFormsGateway(interaction.client, self.session_factory)
            try:
                await service.submit_form_and_create_thread(
                    form_id=self.form_id,
                    user_id=str(interaction.user.id),
                    username=interaction.user.display_name,
                    answers=self.answers,
                    gateway=gateway,
                )
            except PendingSubmissionError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
            except (FormValidationError, NotFoundError) as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return

        await interaction.response.send_message("Application submitted.", ephemeral=True)


class DenyReasonModal(discord.ui.Modal):
    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    def __init__(
        self,
        *,
        submission_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(title="Deny application")
        self.submission_id = submission_id
        self.session_factory = session_factory

    async def on_submit(self, interaction: discord.Interaction) -> None:
        async with self.session_factory() as db:
            try:
                await FormsService(db).deny_submission(
                    submission_id=self.submission_id,
                    actor_id=str(interaction.user.id),
                    actor_role_ids=role_ids_from_member(interaction.user),
                    reason=str(self.reason.value),
                    gateway=DiscordFormsGateway(interaction.client, self.session_factory),
                )
            except ReviewerPermissionError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
        await interaction.response.send_message("Application denied.", ephemeral=True)


class ApproveConfirmationModal(discord.ui.Modal):
    confirmation = discord.ui.TextInput(
        label="Type APPROVE to confirm",
        placeholder="APPROVE",
        max_length=20,
    )

    def __init__(
        self,
        *,
        submission_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(title="Confirm approval")
        self.submission_id = submission_id
        self.session_factory = session_factory

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if str(self.confirmation.value).strip().upper() != "APPROVE":
            await interaction.response.send_message(
                "Approval cancelled. Type APPROVE exactly to approve an application.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        async with self.session_factory() as db:
            try:
                await FormsService(db).approve_submission(
                    submission_id=self.submission_id,
                    actor_id=str(interaction.user.id),
                    actor_role_ids=role_ids_from_member(interaction.user),
                    gateway=DiscordFormsGateway(interaction.client, self.session_factory),
                    actor_name=interaction.user.display_name,
                )
            except ReviewerPermissionError as exc:
                await interaction.followup.send(str(exc), ephemeral=True)
                return
        await interaction.followup.send("Application approved.", ephemeral=True)


class RequestInfoModal(discord.ui.Modal):
    question = discord.ui.TextInput(
        label="Question",
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    def __init__(
        self,
        *,
        submission_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(title="Request more info")
        self.submission_id = submission_id
        self.session_factory = session_factory

    async def on_submit(self, interaction: discord.Interaction) -> None:
        async with self.session_factory() as db:
            try:
                await FormsService(db).request_more_info(
                    submission_id=self.submission_id,
                    actor_id=str(interaction.user.id),
                    actor_role_ids=role_ids_from_member(interaction.user),
                    question=str(self.question.value),
                    gateway=DiscordFormsGateway(interaction.client, self.session_factory),
                )
            except ReviewerPermissionError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
        await interaction.response.send_message("Request posted.", ephemeral=True)


def placeholder_for(field: FormField) -> str | None:
    if field.field_type in {"select", "multi_select"}:
        return truncate("Options: " + ", ".join(field.options), 100)
    if field.field_type == "boolean":
        return "true or false"
    if field.field_type == "number":
        return "Number"
    return None


def truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 3] + "..."
