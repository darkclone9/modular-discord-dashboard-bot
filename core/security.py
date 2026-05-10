import secrets
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from core.config import Settings


def random_token() -> str:
    return secrets.token_urlsafe(32)


def get_serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="discord-dashboard")


def sign_state(settings: Settings, payload: dict[str, Any]) -> str:
    return get_serializer(settings).dumps(payload)


def verify_state(settings: Settings, token: str, *, max_age: int = 600) -> dict[str, Any]:
    try:
        value = get_serializer(settings).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired) as exc:
        raise ValueError("Invalid OAuth state") from exc
    if not isinstance(value, dict):
        raise ValueError("Invalid OAuth state payload")
    return value
