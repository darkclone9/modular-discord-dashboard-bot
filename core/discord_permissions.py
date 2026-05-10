MANAGE_GUILD = 1 << 5


def has_manage_guild(permissions: int, *, owner: bool = False) -> bool:
    return owner or bool(permissions & MANAGE_GUILD)


def filter_manageable_guilds(guilds: list[dict]) -> list[dict]:
    manageable: list[dict] = []
    for guild in guilds:
        permissions = int(guild.get("permissions", 0))
        if has_manage_guild(permissions, owner=bool(guild.get("owner", False))):
            manageable.append(guild)
    return manageable
