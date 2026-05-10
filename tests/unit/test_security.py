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


def test_local_admin_guilds_parse_configured_servers() -> None:
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DISCORD_BOT_TOKEN="test-token",
        DISCORD_CLIENT_ID="client-id",
        DISCORD_CLIENT_SECRET="client-secret",
        DISCORD_REDIRECT_URI="http://localhost/callback",
        SESSION_SECRET="secret",
        LOCAL_ADMIN_USERNAME="admin",
        LOCAL_ADMIN_PASSWORD="password",
        LOCAL_ADMIN_GUILDS="1172343996954193990:BU Gaming Club,123",
    )

    assert settings.local_admin_enabled
    assert settings.local_admin_session_user_id == "local-admin"
    assert settings.local_admin_can_manage_guild("1172343996954193990")
    assert settings.local_admin_guild_list == [
        {
            "id": "1172343996954193990",
            "name": "BU Gaming Club",
            "icon": None,
            "owner": True,
            "permissions": "32",
        },
        {
            "id": "123",
            "name": "Server 123",
            "icon": None,
            "owner": True,
            "permissions": "32",
        },
    ]
