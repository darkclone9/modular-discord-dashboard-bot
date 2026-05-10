from fastapi import APIRouter

router = APIRouter(prefix="/guilds/{guild_id}/forms", tags=["forms"])


@router.get("")
async def forms_placeholder() -> list[dict]:
    return []
