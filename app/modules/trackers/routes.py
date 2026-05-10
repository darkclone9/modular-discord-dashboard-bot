from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.trackers.schemas import (
    GameSuggestionPickRead,
    GameSuggestionSettingsRead,
    GameSuggestionSettingsUpdate,
    SocialTrackerCreate,
    SocialTrackerRead,
    SocialTrackerUpdate,
)
from app.modules.trackers.service import (
    NotFoundError,
    TrackersService,
    game_pick_to_read,
    game_settings_to_read,
    social_tracker_to_read,
)
from app.web.dependencies import get_db, require_guild_manager

router = APIRouter(prefix="/guilds/{guild_id}/trackers", tags=["trackers"])


def not_found(exc: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=list[SocialTrackerRead])
async def list_social_trackers(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SocialTrackerRead]:
    trackers = await TrackersService(db).list_social_trackers(guild_id)
    return [social_tracker_to_read(tracker) for tracker in trackers]


@router.post("", response_model=SocialTrackerRead, status_code=status.HTTP_201_CREATED)
async def create_social_tracker(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    payload: SocialTrackerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SocialTrackerRead:
    tracker = await TrackersService(db).create_social_tracker(guild_id, payload)
    return social_tracker_to_read(tracker)


@router.patch("/{tracker_id}", response_model=SocialTrackerRead)
async def update_social_tracker(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    tracker_id: str,
    payload: SocialTrackerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SocialTrackerRead:
    try:
        tracker = await TrackersService(db).update_social_tracker(guild_id, tracker_id, payload)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return social_tracker_to_read(tracker)


@router.delete("/{tracker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_tracker(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    tracker_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await TrackersService(db).delete_social_tracker(guild_id, tracker_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/games/settings", response_model=GameSuggestionSettingsRead)
async def get_game_settings(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GameSuggestionSettingsRead:
    settings = await TrackersService(db).get_game_settings(guild_id)
    return game_settings_to_read(settings)


@router.put("/games/settings", response_model=GameSuggestionSettingsRead)
async def update_game_settings(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    payload: GameSuggestionSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GameSuggestionSettingsRead:
    settings = await TrackersService(db).update_game_settings(guild_id, payload)
    return game_settings_to_read(settings)


@router.get("/games/picks", response_model=list[GameSuggestionPickRead])
async def list_game_picks(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[GameSuggestionPickRead]:
    picks = await TrackersService(db).list_game_picks(guild_id)
    return [game_pick_to_read(pick) for pick in picks]
