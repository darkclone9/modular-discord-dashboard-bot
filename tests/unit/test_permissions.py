from core.discord_permissions import MANAGE_GUILD, filter_manageable_guilds, has_manage_guild


def test_manage_guild_permission_bit_allows_dashboard_edits() -> None:
    assert has_manage_guild(MANAGE_GUILD)
    assert has_manage_guild(0, owner=True)
    assert not has_manage_guild(0)


def test_filter_manageable_guilds() -> None:
    guilds = [
        {"id": "1", "permissions": str(MANAGE_GUILD), "owner": False},
        {"id": "2", "permissions": "0", "owner": True},
        {"id": "3", "permissions": "0", "owner": False},
    ]

    assert [guild["id"] for guild in filter_manageable_guilds(guilds)] == ["1", "2"]
