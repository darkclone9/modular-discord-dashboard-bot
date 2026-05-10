import pytest
from app.modules.forms import models as forms_models  # noqa: F401
from app.modules.forms.models import Form, Submission
from app.modules.forms.schemas import FormCreate, FormFieldCreate, ReviewSettings
from app.modules.forms.service import FormsService, PendingSubmissionError, ThreadPost
from core import sessions as session_models  # noqa: F401
from core.db import Base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class FakeDiscordGateway:
    def __init__(self) -> None:
        self.created_threads: list[dict[str, object]] = []
        self.review_posts: list[dict[str, object]] = []

    async def create_review_thread(
        self,
        *,
        form: Form,
        submission: Submission,
        thread_name: str,
        submitter_id: str,
    ) -> str:
        self.created_threads.append(
            {
                "form_id": form.id,
                "submission_id": submission.id,
                "thread_name": thread_name,
                "submitter_id": submitter_id,
            }
        )
        return "999999"

    async def post_submission_review(
        self,
        *,
        thread_id: str,
        submission_id: str,
        content: str,
        embed: dict[str, object],
    ) -> ThreadPost:
        self.review_posts.append(
            {
                "thread_id": thread_id,
                "submission_id": submission_id,
                "content": content,
                "embed": embed,
            }
        )
        return ThreadPost(message_id="123")

    async def dm_user(self, *, user_id: str, content: str) -> None:
        raise AssertionError("not used in submission flow")

    async def assign_role(self, *, guild_id: str, user_id: str, role_id: str) -> None:
        raise AssertionError("not used in submission flow")

    async def lock_thread(self, *, thread_id: str) -> None:
        raise AssertionError("not used in submission flow")

    async def post_thread_message(self, *, thread_id: str, content: str) -> None:
        raise AssertionError("not used in submission flow")


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_submission_creates_thread_embed_and_role_ping(db_session) -> None:
    service = FormsService(db_session)
    form = await service.create_form(
        "guild-1",
        FormCreate(
            title="Staff Application",
            description="Apply for staff.",
            post_channel_id="100",
            fields=[
                FormFieldCreate(label="Name", field_type="short_text", required=True),
                FormFieldCreate(label="Experience", field_type="long_text", required=True),
            ],
            review_settings=ReviewSettings(
                reviewer_role_ids=["777"],
                review_channel_id="200",
                auto_role_id="888",
            ),
        ),
    )
    gateway = FakeDiscordGateway()

    submission = await service.submit_form_and_create_thread(
        form_id=form.id,
        user_id="42",
        username="Gary",
        answers={
            form.fields[0].id: "Gary",
            form.fields[1].id: "Built communities.",
        },
        gateway=gateway,
    )

    assert submission.status == "pending"
    assert submission.thread_id == "999999"
    assert gateway.created_threads[0]["thread_name"] == f"application-gary-{submission.id[:6]}"
    assert "<@&777>" in str(gateway.review_posts[0]["content"])
    embed = gateway.review_posts[0]["embed"]
    assert embed["title"] == "Staff Application"
    assert {"name": "Name", "value": "Gary", "inline": False} in embed["fields"]

    with pytest.raises(PendingSubmissionError):
        await service.submit_form_and_create_thread(
            form_id=form.id,
            user_id="42",
            username="Gary",
            answers={
                form.fields[0].id: "Gary",
                form.fields[1].id: "Again.",
            },
            gateway=gateway,
        )
