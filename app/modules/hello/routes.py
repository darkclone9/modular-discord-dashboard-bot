from fastapi import APIRouter

router = APIRouter(prefix="/modules/hello", tags=["hello"])


@router.get("")
async def hello() -> dict[str, str]:
    return {"message": "hello from a discovered module"}
