from datetime import UTC, datetime

import pytest
from app.modules.trackers import models as tracker_models  # noqa: F401
from app.modules.trackers.schemas import GameSuggestionSettingsUpdate
from app.modules.trackers.service import GameCandidate, TrackersService
from core import sessions as session_models  # noqa: F401
from core.db import Base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class FakeTrackerGateway:
    def __init__(self) -> None:
        self.game_picks: list[dict[str, object]] = []

    async def send_tracker_message(self, *, channel_id: str, content: str) -> str | None:
        return "tracker-message"

    async def send_game_pick(
        self,
        *,
        guild_id: str,
        channel_id: str,
        user_id: str,
        reward_role_id: str | None,
        content: str,
        mention_everyone: bool,
    ) -> str | None:
        self.game_picks.append(
            {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "user_id": user_id,
                "reward_role_id": reward_role_id,
                "content": content,
                "mention_everyone": mention_everyone,
            }
        )
        return "game-message"


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
async def test_weekly_game_pick_announces_once_and_records_reward(db_session) -> None:
    service = TrackersService(db_session)
    await service.update_game_settings(
        "guild-1",
        GameSuggestionSettingsUpdate(
            enabled=True,
            announcement_channel_id="100",
            reward_role_id="200",
            mention_everyone=True,
            announcement_weekday=0,
            announcement_hour_utc=18,
            custom_message="Game night pick: {game} from {player_mention}",
        ),
    )
    gateway = FakeTrackerGateway()
    candidates = [
        GameCandidate(user_id="42", username="Gary", game_name="Satisfactory"),
        GameCandidate(user_id="43", username="Alex", game_name="Helldivers 2"),
    ]
    now = datetime(2026, 5, 11, 18, 0, tzinfo=UTC)

    pick = await service.create_weekly_game_pick(
        guild_id="guild-1",
        now=now,
        gateway=gateway,
        candidates=candidates,
    )
    duplicate = await service.create_weekly_game_pick(
        guild_id="guild-1",
        now=now,
        gateway=gateway,
        candidates=candidates,
    )

    assert pick is not None
    assert duplicate is None
    assert pick.message_id == "game-message"
    assert len(gateway.game_picks) == 1
    assert gateway.game_picks[0]["reward_role_id"] == "200"
    assert str(gateway.game_picks[0]["content"]).startswith("@everyone Game night pick:")
    assert "<@" in str(gateway.game_picks[0]["content"])


@pytest.mark.asyncio
async def test_manual_game_pick_can_run_outside_scheduled_hour(db_session) -> None:
    service = TrackersService(db_session)
    await service.update_game_settings(
        "guild-1",
        GameSuggestionSettingsUpdate(
            enabled=True,
            announcement_channel_id="100",
            reward_role_id=None,
            mention_everyone=False,
            announcement_weekday=4,
            announcement_hour_utc=3,
            custom_message="Manual pick: {game} from {player_mention}",
        ),
    )
    gateway = FakeTrackerGateway()

    pick = await service.create_weekly_game_pick(
        guild_id="guild-1",
        now=datetime(2026, 5, 11, 18, 0, tzinfo=UTC),
        gateway=gateway,
        candidates=[GameCandidate(user_id="42", username="Gary", game_name="Satisfactory")],
        force=True,
    )

    assert pick is not None
    assert gateway.game_picks[0]["content"] == "Manual pick: Satisfactory from <@42>"
