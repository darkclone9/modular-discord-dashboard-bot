from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.forms.schemas import FormCreate, FormRead, FormUpdate, SubmissionRead
from app.modules.forms.service import (
    FormsService,
    NotFoundError,
    form_to_read,
)
from app.modules.forms.validators import FormValidationError
from app.web.dependencies import get_db, require_guild_manager

router = APIRouter(prefix="/guilds/{guild_id}/forms", tags=["forms"])


def not_found(exc: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def validation_failed(exc: FormValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors)


@router.get("", response_model=list[FormRead])
async def list_forms(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_archived: Annotated[bool, Query(alias="includeArchived")] = False,
) -> list[FormRead]:
    forms = await FormsService(db).list_forms(guild_id, include_archived=include_archived)
    return [form_to_read(form) for form in forms]


@router.post("", response_model=FormRead, status_code=status.HTTP_201_CREATED)
async def create_form(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    payload: FormCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FormRead:
    try:
        form = await FormsService(db).create_form(guild_id, payload)
    except FormValidationError as exc:
        raise validation_failed(exc) from exc
    return form_to_read(form)


@router.get("/{form_id}", response_model=FormRead)
async def get_form(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    form_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FormRead:
    try:
        form = await FormsService(db).get_form(guild_id, form_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return form_to_read(form)


@router.patch("/{form_id}", response_model=FormRead)
async def update_form(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    form_id: str,
    payload: FormUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FormRead:
    try:
        form = await FormsService(db).update_form(guild_id, form_id, payload)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    except FormValidationError as exc:
        raise validation_failed(exc) from exc
    return form_to_read(form)


@router.post("/{form_id}/duplicate", response_model=FormRead)
async def duplicate_form(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    form_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FormRead:
    try:
        form = await FormsService(db).duplicate_form(guild_id, form_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return form_to_read(form)


@router.post("/{form_id}/archive", response_model=FormRead)
async def archive_form(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    form_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FormRead:
    try:
        form = await FormsService(db).archive_form(guild_id, form_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return form_to_read(form)


@router.post("/{form_id}/publish", response_model=FormRead)
async def publish_form(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    form_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FormRead:
    try:
        form = await FormsService(db).publish_form(guild_id, form_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return form_to_read(form)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    form_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await FormsService(db).delete_form(guild_id, form_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{form_id}/submissions", response_model=list[SubmissionRead])
async def list_submissions(
    guild_id: Annotated[str, Depends(require_guild_manager)],
    form_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    submission_status: Annotated[str | None, Query(alias="status")] = None,
) -> list[SubmissionRead]:
    try:
        await FormsService(db).get_form(guild_id, form_id)
    except NotFoundError as exc:
        raise not_found(exc) from exc
    return await FormsService(db).list_submissions(guild_id, form_id, status=submission_status)
