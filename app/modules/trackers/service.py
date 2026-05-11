from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from random import Random
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.trackers.models import (
    GameActivitySnapshot,
    GameSuggestionPick,
    GameSuggestionSettings,
    SocialTracker,
)
from app.modules.trackers.schemas import (
    GameSuggestionPickRead,
    GameSuggestionSettingsRead,
    GameSuggestionSettingsUpdate,
    SocialTrackerCreate,
    SocialTrackerRead,
    SocialTrackerUpdate,
)


class NotFoundError(LookupError):
    pass


DEFAULT_GAME_MESSAGE = (
    "This week's community game pick is **{game}** from {player}! "
    "{player_mention}, you were picked and received the reward."
)


@dataclass(frozen=True)
class TrackerItem:
    external_id: str
    title: str
    url: str
    published_at: datetime | None = None


@dataclass(frozen=True)
class GameCandidate:
    user_id: str
    username: str
    game_name: str


class TrackerNotificationGateway(Protocol):
    async def send_tracker_message(self, *, channel_id: str, content: str) -> str | None: ...

    async def send_game_pick(
        self,
        *,
        guild_id: str,
        channel_id: str,
        user_id: str,
        reward_role_id: str | None,
        content: str,
        mention_everyone: bool,
    ) -> str | None: ...


class TrackersService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_social_trackers(self, guild_id: str) -> list[SocialTracker]:
        result = await self.db.execute(
            select(SocialTracker)
            .where(SocialTracker.guild_id == guild_id)
            .order_by(SocialTracker.created_at.desc())
        )
        return list(result.scalars())

    async def create_social_tracker(
        self, guild_id: str, payload: SocialTrackerCreate
    ) -> SocialTracker:
        tracker = SocialTracker(
            guild_id=guild_id,
            provider=payload.provider,
            label=payload.label,
            source_id=payload.source_id,
            source_url=payload.source_url,
            notification_channel_id=payload.notification_channel_id,
            custom_message=payload.custom_message,
            is_enabled=payload.is_enabled,
        )
        self.db.add(tracker)
        await self.db.commit()
        await self.db.refresh(tracker)
        return tracker

    async def get_social_tracker(self, guild_id: str, tracker_id: str) -> SocialTracker:
        result = await self.db.execute(
            select(SocialTracker).where(
                SocialTracker.guild_id == guild_id,
                SocialTracker.id == tracker_id,
            )
        )
        tracker = result.scalar_one_or_none()
        if tracker is None:
            raise NotFoundError("Tracker not found")
        return tracker

    async def update_social_tracker(
        self,
        guild_id: str,
        tracker_id: str,
        payload: SocialTrackerUpdate,
    ) -> SocialTracker:
        tracker = await self.get_social_tracker(guild_id, tracker_id)
        if payload.provider is not None:
            tracker.provider = payload.provider
        if payload.label is not None:
            tracker.label = payload.label
        if payload.source_id is not None:
            tracker.source_id = payload.source_id
            tracker.last_seen_external_id = None
            tracker.last_seen_url = None
        if payload.source_url is not None:
            tracker.source_url = payload.source_url
        if payload.notification_channel_id is not None:
            tracker.notification_channel_id = payload.notification_channel_id
        if payload.custom_message is not None:
            tracker.custom_message = payload.custom_message
        if payload.is_enabled is not None:
            tracker.is_enabled = payload.is_enabled
        await self.db.commit()
        await self.db.refresh(tracker)
        return tracker

    async def delete_social_tracker(self, guild_id: str, tracker_id: str) -> None:
        tracker = await self.get_social_tracker(guild_id, tracker_id)
        await self.db.delete(tracker)
        await self.db.commit()

    async def list_enabled_social_trackers(self) -> list[SocialTracker]:
        result = await self.db.execute(
            select(SocialTracker).where(SocialTracker.is_enabled.is_(True))
        )
        return list(result.scalars())

    async def mark_tracker_checked(
        self,
        tracker: SocialTracker,
        *,
        latest: TrackerItem | None,
    ) -> None:
        tracker.last_checked_at = datetime.now(UTC)
        if latest is not None:
            tracker.last_seen_external_id = latest.external_id
            tracker.last_seen_url = latest.url
        await self.db.commit()

    async def get_game_settings(self, guild_id: str) -> GameSuggestionSettings:
        result = await self.db.execute(
            select(GameSuggestionSettings).where(GameSuggestionSettings.guild_id == guild_id)
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = GameSuggestionSettings(
                guild_id=guild_id,
                custom_message=DEFAULT_GAME_MESSAGE,
            )
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings

    async def update_game_settings(
        self,
        guild_id: str,
        payload: GameSuggestionSettingsUpdate,
    ) -> GameSuggestionSettings:
        settings = await self.get_game_settings(guild_id)
        settings.enabled = payload.enabled
        settings.announcement_channel_id = payload.announcement_channel_id
        settings.reward_role_id = payload.reward_role_id
        settings.mention_everyone = payload.mention_everyone
        settings.announcement_weekday = payload.announcement_weekday
        settings.announcement_hour_utc = payload.announcement_hour_utc
        settings.custom_message = payload.custom_message
        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def list_game_picks(self, guild_id: str) -> list[GameSuggestionPick]:
        result = await self.db.execute(
            select(GameSuggestionPick)
            .where(GameSuggestionPick.guild_id == guild_id)
            .order_by(GameSuggestionPick.announced_at.desc())
        )
        return list(result.scalars())

    async def observe_game_activity(
        self,
        *,
        guild_id: str,
        candidates: Sequence[GameCandidate],
    ) -> None:
        if not candidates:
            return
        now = datetime.now(UTC)
        for candidate in candidates:
            existing = await self.db.execute(
                select(GameActivitySnapshot).where(
                    GameActivitySnapshot.guild_id == guild_id,
                    GameActivitySnapshot.user_id == candidate.user_id,
                    GameActivitySnapshot.game_name == candidate.game_name,
                )
            )
            snapshot = existing.scalar_one_or_none()
            if snapshot is None:
                self.db.add(
                    GameActivitySnapshot(
                        guild_id=guild_id,
                        user_id=candidate.user_id,
                        username=candidate.username,
                        game_name=candidate.game_name,
                        observed_at=now,
                    )
                )
            else:
                snapshot.username = candidate.username
                snapshot.observed_at = now
        await self.db.commit()

    async def create_weekly_game_pick(
        self,
        *,
        guild_id: str,
        now: datetime,
        gateway: TrackerNotificationGateway,
        candidates: Sequence[GameCandidate] = (),
    ) -> GameSuggestionPick | None:
        settings = await self.get_game_settings(guild_id)
        if not should_announce_this_hour(settings, now):
            return None

        week = iso_week_key(now)
        if settings.last_announced_week == week:
            return None

        if candidates:
            await self.observe_game_activity(guild_id=guild_id, candidates=candidates)

        candidate = await self._pick_candidate(guild_id, week)
        if candidate is None or not settings.announcement_channel_id:
            return None

        content = format_game_message(settings.custom_message, candidate)
        if settings.mention_everyone:
            content = f"@everyone {content}"
        message_id = await gateway.send_game_pick(
            guild_id=guild_id,
            channel_id=settings.announcement_channel_id,
            user_id=candidate.user_id,
            reward_role_id=settings.reward_role_id,
            content=content,
            mention_everyone=settings.mention_everyone,
        )
        pick = GameSuggestionPick(
            guild_id=guild_id,
            user_id=candidate.user_id,
            username=candidate.username,
            game_name=candidate.game_name,
            channel_id=settings.announcement_channel_id,
            message_id=message_id,
            announced_week=week,
        )
        settings.last_announced_week = week
        self.db.add(pick)
        await self.db.commit()
        await self.db.refresh(pick)
        return pick

    async def reset_old_game_snapshots(self, guild_id: str, *, before: datetime) -> None:
        await self.db.execute(
            delete(GameActivitySnapshot).where(
                GameActivitySnapshot.guild_id == guild_id,
                GameActivitySnapshot.observed_at < before,
            )
        )
        await self.db.commit()

    async def _pick_candidate(self, guild_id: str, week: str) -> GameCandidate | None:
        already_picked = await self.db.execute(
            select(GameSuggestionPick.user_id, GameSuggestionPick.game_name).where(
                GameSuggestionPick.guild_id == guild_id
            )
        )
        excluded = {(user_id, game_name) for user_id, game_name in already_picked}
        result = await self.db.execute(
            select(GameActivitySnapshot).where(GameActivitySnapshot.guild_id == guild_id)
        )
        snapshots = [
            snapshot
            for snapshot in result.scalars()
            if (snapshot.user_id, snapshot.game_name) not in excluded
        ]
        if not snapshots:
            return None
        selected = Random(week).choice(snapshots)
        return GameCandidate(
            user_id=selected.user_id,
            username=selected.username,
            game_name=selected.game_name,
        )


def social_tracker_to_read(tracker: SocialTracker) -> SocialTrackerRead:
    return SocialTrackerRead.model_validate(tracker)


def game_settings_to_read(settings: GameSuggestionSettings) -> GameSuggestionSettingsRead:
    return GameSuggestionSettingsRead.model_validate(settings)


def game_pick_to_read(pick: GameSuggestionPick) -> GameSuggestionPickRead:
    return GameSuggestionPickRead.model_validate(pick)


def format_tracker_message(tracker: SocialTracker, item: TrackerItem) -> str:
    values = {
        "provider": tracker.provider.title(),
        "source": tracker.label,
        "title": item.title,
        "url": item.url,
    }
    return tracker.custom_message.format_map(SafeFormatDict(values))


def format_game_message(template: str, candidate: GameCandidate) -> str:
    return template.format_map(
        SafeFormatDict(
            {
                "game": candidate.game_name,
                "player": candidate.username,
                "player_mention": f"<@{candidate.user_id}>",
            }
        )
    )


def should_announce_this_hour(settings: GameSuggestionSettings, now: datetime) -> bool:
    return (
        settings.enabled
        and bool(settings.announcement_channel_id)
        and now.weekday() == settings.announcement_weekday
        and now.hour == settings.announcement_hour_utc
    )


def iso_week_key(now: datetime) -> str:
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


class SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
