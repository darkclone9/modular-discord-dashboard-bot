from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.forms.models import Form, FormField, Submission, SubmissionAction
from app.modules.forms.schemas import (
    FormCreate,
    FormFieldCreate,
    FormRead,
    FormUpdate,
    ReviewSettings,
)
from app.modules.forms.validators import (
    validate_answers,
    validate_field_definitions,
)


class NotFoundError(LookupError):
    pass


class PendingSubmissionError(ValueError):
    pass


class ReviewerPermissionError(PermissionError):
    pass


DEFAULT_SETUP_QUESTION = "Why do you want to apply?"


@dataclass(frozen=True)
class ThreadPost:
    message_id: str | None = None


class FormsDiscordGateway(Protocol):
    async def create_review_thread(
        self,
        *,
        form: Form,
        submission: Submission,
        thread_name: str,
        submitter_id: str,
    ) -> str: ...

    async def post_submission_review(
        self,
        *,
        thread_id: str,
        submission_id: str,
        content: str,
        embed: dict[str, object],
    ) -> ThreadPost: ...

    async def dm_user(self, *, user_id: str, content: str) -> None: ...

    async def assign_role(self, *, guild_id: str, user_id: str, role_id: str) -> None: ...

    async def lock_thread(self, *, thread_id: str) -> None: ...

    async def post_thread_message(self, *, thread_id: str, content: str) -> None: ...


class FormsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_form(self, guild_id: str, payload: FormCreate) -> Form:
        validate_field_definitions(payload.fields)
        form = Form(
            guild_id=guild_id,
            title=payload.title,
            description=payload.description,
            post_channel_id=payload.post_channel_id,
            review_channel_id=payload.review_settings.review_channel_id,
            reviewer_role_ids=payload.review_settings.reviewer_role_ids,
            auto_role_id=payload.review_settings.auto_role_id,
            approval_message=payload.review_settings.approval_message,
            denial_message=payload.review_settings.denial_message,
        )
        form.fields = [
            FormField(
                position=index,
                label=field.label,
                field_type=field.field_type,
                required=field.required,
                options=field.options,
            )
            for index, field in enumerate(payload.fields)
        ]
        self.db.add(form)
        await self.db.commit()
        await self.db.refresh(form, ["fields"])
        return form

    async def list_forms(self, guild_id: str, *, include_archived: bool = False) -> list[Form]:
        query = select(Form).options(selectinload(Form.fields)).where(Form.guild_id == guild_id)
        if not include_archived:
            query = query.where(Form.is_archived.is_(False))
        result = await self.db.execute(query.order_by(Form.created_at.desc()))
        return list(result.scalars().unique())

    async def get_form(self, guild_id: str, form_id: str) -> Form:
        result = await self.db.execute(
            select(Form)
            .options(selectinload(Form.fields))
            .where(Form.guild_id == guild_id, Form.id == form_id)
        )
        form = result.scalar_one_or_none()
        if form is None:
            raise NotFoundError("Form not found")
        return form

    async def update_form(self, guild_id: str, form_id: str, payload: FormUpdate) -> Form:
        form = await self.get_form(guild_id, form_id)
        if payload.title is not None:
            form.title = payload.title
        if payload.description is not None:
            form.description = payload.description
        if payload.post_channel_id is not None:
            form.post_channel_id = payload.post_channel_id
        if payload.review_settings is not None:
            apply_review_settings(form, payload.review_settings)
        if payload.fields is not None:
            validate_field_definitions(payload.fields)
            await self.db.execute(delete(FormField).where(FormField.form_id == form.id))
            form.fields = [
                FormField(
                    form_id=form.id,
                    position=index,
                    label=field.label,
                    field_type=field.field_type,
                    required=field.required,
                    options=field.options,
                )
                for index, field in enumerate(payload.fields)
            ]
        await self.db.commit()
        await self.db.refresh(form, ["fields"])
        return form

    async def duplicate_form(self, guild_id: str, form_id: str) -> Form:
        source = await self.get_form(guild_id, form_id)
        payload = FormCreate(
            title=f"{source.title} Copy",
            description=source.description,
            post_channel_id=source.post_channel_id,
            fields=[
                {
                    "label": field.label,
                    "fieldType": field.field_type,
                    "required": field.required,
                    "options": field.options,
                }
                for field in source.fields
            ],
            review_settings=form_review_settings(source),
        )
        return await self.create_form(guild_id, payload)

    async def archive_form(self, guild_id: str, form_id: str) -> Form:
        form = await self.get_form(guild_id, form_id)
        form.is_archived = True
        await self.db.commit()
        await self.db.refresh(form, ["fields"])
        return form

    async def delete_form(self, guild_id: str, form_id: str) -> None:
        form = await self.get_form(guild_id, form_id)
        await self.db.delete(form)
        await self.db.commit()

    async def publish_form(self, guild_id: str, form_id: str) -> Form:
        form = await self.get_form(guild_id, form_id)
        form.is_published = True
        await self.db.commit()
        await self.db.refresh(form, ["fields"])
        return form

    async def list_submissions(
        self, guild_id: str, form_id: str, *, status: str | None = None
    ) -> list[Submission]:
        query = (
            select(Submission)
            .options(selectinload(Submission.actions))
            .where(Submission.guild_id == guild_id, Submission.form_id == form_id)
            .order_by(Submission.created_at.desc())
        )
        if status:
            query = query.where(Submission.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().unique())

    async def submit_form_and_create_thread(
        self,
        *,
        form_id: str,
        user_id: str,
        username: str,
        answers: dict[str, object],
        gateway: FormsDiscordGateway,
    ) -> Submission:
        form = await self._get_form_by_id(form_id)
        if form.is_archived:
            raise NotFoundError("Form is archived")
        await self._ensure_no_pending_submission(form.id, user_id)

        normalized_answers = validate_answers(form.fields, answers)
        submission = Submission(
            form_id=form.id,
            guild_id=form.guild_id,
            user_id=user_id,
            username=username,
            status="pending",
            answers=normalized_answers,
        )
        self.db.add(submission)
        await self.db.flush()

        thread_name = build_thread_name(username, submission.id)
        thread_id = await gateway.create_review_thread(
            form=form,
            submission=submission,
            thread_name=thread_name,
            submitter_id=user_id,
        )
        submission.thread_id = thread_id
        await gateway.post_submission_review(
            thread_id=thread_id,
            submission_id=submission.id,
            content=build_reviewer_ping(form),
            embed=build_submission_embed(form, submission),
        )
        self._log_action(submission, actor_id=user_id, action="submitted")
        await self.db.commit()
        await self.db.refresh(submission, ["actions", "form"])
        return submission

    async def approve_submission(
        self,
        *,
        submission_id: str,
        actor_id: str,
        actor_role_ids: set[str],
        gateway: FormsDiscordGateway,
    ) -> Submission:
        submission = await self._get_submission(submission_id)
        ensure_reviewer(submission.form, actor_role_ids)
        submission.status = "approved"
        submission.decided_at = datetime.now(UTC)
        self._log_action(submission, actor_id=actor_id, action="approved")
        await gateway.dm_user(user_id=submission.user_id, content=submission.form.approval_message)
        if submission.form.auto_role_id:
            await gateway.assign_role(
                guild_id=submission.guild_id,
                user_id=submission.user_id,
                role_id=submission.form.auto_role_id,
            )
        if submission.thread_id:
            await gateway.lock_thread(thread_id=submission.thread_id)
        await self.db.commit()
        await self.db.refresh(submission, ["actions", "form"])
        return submission

    async def deny_submission(
        self,
        *,
        submission_id: str,
        actor_id: str,
        actor_role_ids: set[str],
        reason: str,
        gateway: FormsDiscordGateway,
    ) -> Submission:
        submission = await self._get_submission(submission_id)
        ensure_reviewer(submission.form, actor_role_ids)
        submission.status = "denied"
        submission.decided_at = datetime.now(UTC)
        self._log_action(submission, actor_id=actor_id, action="denied", note=reason)
        await gateway.dm_user(
            user_id=submission.user_id,
            content=f"{submission.form.denial_message}\n\nReason: {reason}",
        )
        if submission.thread_id:
            await gateway.lock_thread(thread_id=submission.thread_id)
        await self.db.commit()
        await self.db.refresh(submission, ["actions", "form"])
        return submission

    async def request_more_info(
        self,
        *,
        submission_id: str,
        actor_id: str,
        actor_role_ids: set[str],
        question: str,
        gateway: FormsDiscordGateway,
    ) -> Submission:
        submission = await self._get_submission(submission_id)
        ensure_reviewer(submission.form, actor_role_ids)
        self._log_action(submission, actor_id=actor_id, action="requested_more_info", note=question)
        if submission.thread_id:
            await gateway.post_thread_message(
                thread_id=submission.thread_id,
                content=f"<@{submission.user_id}> {question}",
            )
        await self.db.commit()
        await self.db.refresh(submission, ["actions", "form"])
        return submission

    async def _get_form_by_id(self, form_id: str) -> Form:
        result = await self.db.execute(
            select(Form).options(selectinload(Form.fields)).where(Form.id == form_id)
        )
        form = result.scalar_one_or_none()
        if form is None:
            raise NotFoundError("Form not found")
        return form

    async def _get_submission(self, submission_id: str) -> Submission:
        result = await self.db.execute(
            select(Submission)
            .options(
                selectinload(Submission.form).selectinload(Form.fields),
                selectinload(Submission.actions),
            )
            .where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if submission is None:
            raise NotFoundError("Submission not found")
        return submission

    async def _ensure_no_pending_submission(self, form_id: str, user_id: str) -> None:
        result = await self.db.execute(
            select(Submission.id).where(
                Submission.form_id == form_id,
                Submission.user_id == user_id,
                Submission.status == "pending",
            )
        )
        if result.scalar_one_or_none() is not None:
            raise PendingSubmissionError("You already have a pending submission for this form")

    def _log_action(
        self, submission: Submission, *, actor_id: str, action: str, note: str | None = None
    ) -> None:
        self.db.add(
            SubmissionAction(
                submission_id=submission.id,
                actor_id=actor_id,
                action=action,
                note=note,
            )
        )


def apply_review_settings(form: Form, settings: ReviewSettings) -> None:
    form.review_channel_id = settings.review_channel_id
    form.reviewer_role_ids = settings.reviewer_role_ids
    form.auto_role_id = settings.auto_role_id
    form.approval_message = settings.approval_message
    form.denial_message = settings.denial_message


def form_review_settings(form: Form) -> ReviewSettings:
    return ReviewSettings(
        reviewer_role_ids=form.reviewer_role_ids,
        review_channel_id=form.review_channel_id,
        auto_role_id=form.auto_role_id,
        approval_message=form.approval_message,
        denial_message=form.denial_message,
    )


def build_server_setup_form_payload(
    *,
    title: str,
    description: str,
    post_channel_id: str,
    review_channel_id: str,
    reviewer_role_ids: Sequence[str],
    auto_role_id: str | None,
    questions: Sequence[str | None],
) -> FormCreate:
    cleaned_questions = [
        question.strip() for question in questions if question and question.strip()
    ]
    if not cleaned_questions:
        cleaned_questions = [DEFAULT_SETUP_QUESTION]
    return FormCreate(
        title=title.strip(),
        description=description.strip(),
        post_channel_id=post_channel_id,
        fields=[
            FormFieldCreate(label=question, field_type="long_text", required=True)
            for question in cleaned_questions
        ],
        review_settings=ReviewSettings(
            reviewer_role_ids=[role_id for role_id in reviewer_role_ids if role_id],
            review_channel_id=review_channel_id,
            auto_role_id=auto_role_id,
        ),
    )


def form_to_read(form: Form) -> FormRead:
    return FormRead(
        id=form.id,
        guild_id=form.guild_id,
        title=form.title,
        description=form.description,
        post_channel_id=form.post_channel_id,
        fields=form.fields,
        review_settings=form_review_settings(form),
        is_archived=form.is_archived,
        is_published=form.is_published,
        published_message_id=form.published_message_id,
        published_at=form.published_at,
        created_at=form.created_at,
        updated_at=form.updated_at,
    )


def ensure_reviewer(form: Form, actor_role_ids: set[str]) -> None:
    if not actor_role_ids.intersection(set(form.reviewer_role_ids)):
        raise ReviewerPermissionError("Reviewer role required")


def build_reviewer_ping(form: Form) -> str:
    mentions = " ".join(f"<@&{role_id}>" for role_id in form.reviewer_role_ids)
    return f"{mentions} New application submitted for **{form.title}**.".strip()


def build_submission_embed(form: Form, submission: Submission) -> dict[str, object]:
    answer_lines = []
    fields_by_id = {field.id: field for field in form.fields}
    for field_id, answer in submission.answers.items():
        field = fields_by_id.get(field_id)
        label = field.label if field else field_id
        answer_lines.append({"name": label, "value": format_answer(answer), "inline": False})
    return {
        "title": form.title,
        "description": f"Application from {submission.username} (`{submission.user_id}`)",
        "fields": answer_lines,
        "footer": {"text": f"Submission {submission.id}"},
    }


def format_answer(answer: object) -> str:
    if isinstance(answer, list):
        return ", ".join(str(item) for item in answer) or "(empty)"
    return str(answer)


def build_thread_name(username: str, submission_id: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in username).strip("-")
    slug = "-".join(part for part in slug.split("-") if part)[:24] or "user"
    return f"application-{slug}-{submission_id[:6]}"
