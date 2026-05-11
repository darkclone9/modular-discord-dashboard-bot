from collections.abc import Awaitable, Callable

import discord
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.forms.discord_gateway import to_discord_embed
from app.modules.forms.discord_modals import (
    ApproveConfirmationModal,
    DenyReasonModal,
    FormApplicationModal,
    RequestInfoModal,
)
from app.modules.forms.models import Form
from app.modules.forms.service import (
    FormsService,
    NotFoundError,
    build_application_question_payload,
)


class ApplyView(discord.ui.View):
    def __init__(self, form_id: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(timeout=None)
        self.form_id = form_id
        self.session_factory = session_factory
        button = discord.ui.Button(
            label="Apply",
            style=discord.ButtonStyle.primary,
            custom_id=f"forms:apply:{form_id}",
        )
        button.callback = self.apply
        self.add_item(button)

    async def apply(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("Applications must be submitted in a server.")
            return
        async with self.session_factory() as db:
            try:
                form = await FormsService(db).get_form(str(interaction.guild_id), self.form_id)
            except NotFoundError:
                await interaction.response.send_message("This form is no longer available.")
                return
            await interaction.response.send_message(
                embed=to_discord_embed(build_application_question_payload(form)),
                view=ApplicationStartView(
                    form=form,
                    user_id=str(interaction.user.id),
                    session_factory=self.session_factory,
                ),
                ephemeral=True,
            )


class ApplicationStartView(discord.ui.View):
    def __init__(
        self,
        *,
        form: Form,
        user_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(timeout=900)
        self.form_id = form.id
        self.user_id = user_id
        self.fields = list(form.fields)
        self.session_factory = session_factory
        button = discord.ui.Button(
            label="Start application",
            style=discord.ButtonStyle.primary,
            custom_id=f"forms:start:{form.id}:{user_id}",
        )
        button.callback = self.start
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.user_id:
            return True
        await interaction.response.send_message(
            "This application prompt belongs to someone else. Click Apply to start your own.",
            ephemeral=True,
        )
        return False

    async def start(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            FormApplicationModal(
                form_id=self.form_id,
                fields=self.fields,
                session_factory=self.session_factory,
            )
        )


class ReviewActionsView(discord.ui.View):
    def __init__(
        self,
        submission_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(timeout=None)
        self.submission_id = submission_id
        self.session_factory = session_factory
        self._add_button("Approve", discord.ButtonStyle.success, "approve", self.approve)
        self._add_button("Deny", discord.ButtonStyle.danger, "deny", self.deny)
        self._add_button(
            "Request more info",
            discord.ButtonStyle.secondary,
            "request_info",
            self.request_info,
        )

    def _add_button(
        self,
        label: str,
        style: discord.ButtonStyle,
        action: str,
        callback: Callable[[discord.Interaction], Awaitable[None]],
    ) -> None:
        button = discord.ui.Button(
            label=label,
            style=style,
            custom_id=f"forms:review:{action}:{self.submission_id}",
        )
        button.callback = callback
        self.add_item(button)

    async def approve(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            ApproveConfirmationModal(
                submission_id=self.submission_id,
                session_factory=self.session_factory,
            )
        )

    async def deny(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            DenyReasonModal(
                submission_id=self.submission_id,
                session_factory=self.session_factory,
            )
        )

    async def request_info(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            RequestInfoModal(
                submission_id=self.submission_id,
                session_factory=self.session_factory,
            )
        )
