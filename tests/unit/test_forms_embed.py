from app.modules.forms.cog import split_apply_description, truncate_embed_value


def test_split_apply_description_uses_named_sections() -> None:
    intro, sections = split_apply_description(
        "Join the officer team. "
        "What officers do. Plan events and welcome members. "
        "What we're looking for. Reliable people who communicate. "
        "Time commitment. About one hour per week. "
        "How to apply. Click the button and answer honestly."
    )

    assert intro == "Join the officer team."
    assert sections == [
        ("What officers do", "Plan events and welcome members."),
        ("What we're looking for", "Reliable people who communicate."),
        ("Time commitment", "About one hour per week."),
        ("How to apply", "Click the button and answer honestly."),
    ]


def test_truncate_embed_value_respects_discord_field_limit() -> None:
    value = truncate_embed_value("x" * 1200)

    assert len(value) == 1024
    assert value.endswith("...")
