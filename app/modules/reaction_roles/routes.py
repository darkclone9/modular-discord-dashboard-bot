from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reaction_roles.schemas import (
    ReactionRoleMenuCreate,
    ReactionRoleMenuRead,
    ReactionRoleMenuUpdate,
)
from app.modules.reaction_roles.service import (
    NotFoundError,
    ReactionRolesService,
    ReactionRoleValidationError,
    menu_to_read,
)
from app.web.dependencies import get_db, require_guild_manager

router = APIRouter(prefix="/guilds/{guild_id}/reaction-roles", tags=["reaction-roles"])


def not_found(exc: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def validation_failed(exc: ReactionRoleValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors)


@router.get("", response_model=list[ReactionRoleMenuRead])
async def list_menus(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReactionRoleMenuRead]:
    menus = await ReactionRolesService(db).list_menus(guild_id)
    return [menu_to_read(menu) for menu in menus]


@router.post("", response_model=ReactionRoleMenuRead, status_code=status.HTTP_201_CREATED)
async def create_menu(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    payload: ReactionRoleMenuCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReactionRoleMenuRead:
    try:
        menu = await ReactionRolesService(db).create_menu(guild_id, payload)
    except ReactionRoleValidationError as exc:
        raise validation_failed(exc) from exc
    return menu_to_read(menu)


@router.patch("/{menu_id}", response_model=ReactionRoleMenuRead)
async def update_menu(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    menu_id: str,
    payload: ReactionRoleMenuUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReactionRoleMenuRead:
    try:
        menu = await ReactionRolesService(db).update_menu(guild_id, menu_id, payload)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    except ReactionRoleValidationError as exc:
        raise validation_failed(exc) from exc
    return menu_to_read(menu)


@router.post("/{menu_id}/publish", response_model=ReactionRoleMenuRead)
async def mark_menu_ready_to_publish(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    menu_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReactionRoleMenuRead:
    try:
        menu = await ReactionRolesService(db).enable_menu(guild_id, menu_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    except ReactionRoleValidationError as exc:
        raise validation_failed(exc) from exc
    return menu_to_read(menu)


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    menu_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await ReactionRolesService(db).delete_menu(guild_id, menu_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
