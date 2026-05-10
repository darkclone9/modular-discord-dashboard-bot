import pytest
from core.config import Settings
from core.security import sign_state, verify_state


def test_signed_state_round_trip() -> None:
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DISCORD_BOT_TOKEN="test-token",
        DISCORD_CLIENT_ID="client-id",
        DISCORD_CLIENT_SECRET="client-secret",
        DISCORD_REDIRECT_URI="http://localhost/callback",
        SESSION_SECRET="secret",
    )

    token = sign_state(settings, {"nonce": "abc"})

    assert verify_state(settings, token) == {"nonce": "abc"}


def test_signed_state_rejects_bad_token() -> None:
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DISCORD_BOT_TOKEN="test-token",
        DISCORD_CLIENT_ID="client-id",
        DISCORD_CLIENT_SECRET="client-secret",
        DISCORD_REDIRECT_URI="http://localhost/callback",
        SESSION_SECRET="secret",
    )

    with pytest.raises(ValueError, match="Invalid OAuth state"):
        verify_state(settings, "bad-token")
