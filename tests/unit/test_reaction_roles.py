import pytest
from app.modules.reaction_roles import models as reaction_role_models  # noqa: F401
from app.modules.reaction_roles.schemas import ReactionRoleMenuCreate, ReactionRoleOptionCreate
from app.modules.reaction_roles.service import (
    ReactionRolesService,
    ReactionRoleValidationError,
)
from core import sessions as session_models  # noqa: F401
from core.db import Base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class FakeReactionRolesGateway:
    def __init__(self) -> None:
        self.assigned: list[tuple[str, str]] = []
        self.removed: list[tuple[str, str]] = []
        self.published: list[str] = []

    async def publish_menu(self, menu) -> str:
        self.published.append(menu.id)
        return "message-1"

    async def assign_role(self, *, guild_id: str, user_id: str, role_id: str, reason: str) -> None:
        self.assigned.append((user_id, role_id))

    async def remove_role(self, *, guild_id: str, user_id: str, role_id: str, reason: str) -> None:
        self.removed.append((user_id, role_id))


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
async def test_reaction_role_menu_rejects_duplicate_emoji_and_roles(db_session) -> None:
    service = ReactionRolesService(db_session)
    payload = menu_payload(
        options=[
            ReactionRoleOptionCreate(label="One", role_id="100", emoji="A"),
            ReactionRoleOptionCreate(label="Two", role_id="100", emoji="A"),
        ]
    )

    with pytest.raises(ReactionRoleValidationError) as exc:
        await service.create_menu("guild-1", payload)

    assert "Duplicate role" in str(exc.value)
    assert "Duplicate emoji" in str(exc.value)


@pytest.mark.asyncio
async def test_reaction_add_and_remove_toggle_role(db_session) -> None:
    service = ReactionRolesService(db_session)
    menu = await service.create_menu("guild-1", menu_payload())
    gateway = FakeReactionRolesGateway()
    await service.publish_menu("guild-1", menu.id, gateway)

    await service.handle_reaction_add(
        guild_id="guild-1",
        message_id="message-1",
        user_id="user-1",
        emoji="A",
        gateway=gateway,
    )
    await service.handle_reaction_remove(
        guild_id="guild-1",
        message_id="message-1",
        user_id="user-1",
        emoji="A",
        gateway=gateway,
    )

    assert gateway.assigned == [("user-1", "100")]
    assert gateway.removed == [("user-1", "100")]


@pytest.mark.asyncio
async def test_add_only_reaction_remove_keeps_role(db_session) -> None:
    service = ReactionRolesService(db_session)
    menu = await service.create_menu("guild-1", menu_payload(behavior="add_only"))
    gateway = FakeReactionRolesGateway()
    await service.publish_menu("guild-1", menu.id, gateway)

    await service.handle_reaction_remove(
        guild_id="guild-1",
        message_id="message-1",
        user_id="user-1",
        emoji="A",
        gateway=gateway,
    )

    assert gateway.removed == []


@pytest.mark.asyncio
async def test_single_choice_component_removes_other_menu_roles(db_session) -> None:
    service = ReactionRolesService(db_session)
    menu = await service.create_menu(
        "guild-1",
        menu_payload(
            picker_style="buttons",
            behavior="single",
            options=[
                ReactionRoleOptionCreate(label="One", role_id="100", emoji=None),
                ReactionRoleOptionCreate(label="Two", role_id="200", emoji=None),
            ],
        ),
    )
    gateway = FakeReactionRolesGateway()

    await service.handle_component_selection(
        guild_id="guild-1",
        menu_id=menu.id,
        user_id="user-1",
        option_ids=[menu.options[1].id],
        gateway=gateway,
    )

    assert gateway.removed == [("user-1", "100")]
    assert gateway.assigned == [("user-1", "200")]


def menu_payload(
    *,
    picker_style: str = "reactions",
    behavior: str = "toggle",
    options: list[ReactionRoleOptionCreate] | None = None,
) -> ReactionRoleMenuCreate:
    return ReactionRoleMenuCreate(
        name="Roles",
        channel_id="10",
        picker_style=picker_style,
        behavior=behavior,
        title="Pick roles",
        options=options
        or [ReactionRoleOptionCreate(label="One", role_id="100", emoji="A")],
    )
