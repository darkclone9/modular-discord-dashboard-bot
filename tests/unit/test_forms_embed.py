from types import SimpleNamespace

from app.modules.forms.service import (
    build_application_question_payload,
    build_apply_embed_payload,
    split_apply_description,
    truncate_embed_value,
)


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


def test_apply_preview_payload_matches_public_embed_shape() -> None:
    form = SimpleNamespace(
        title="Officer Application",
        description="Join us.\n\nBring ideas.",
        fields=[SimpleNamespace(label="Why do you want to help?")],
    )

    payload = build_apply_embed_payload(form)

    assert payload["title"] == "Officer Application"
    assert payload["description"] == "Join us."
    assert payload["fields"][0] == {
        "name": "Details 1",
        "value": "Bring ideas.",
        "inline": False,
    }
    assert payload["fields"][1]["name"] == "Questions (1)"


def test_application_question_payload_shows_full_long_questions() -> None:
    question = (
        "Tell us about a time you took initiative on something nobody asked you to do. "
        "What was it, why did you do it, and what came of it?"
    )
    form = SimpleNamespace(
        title="Officer Application",
        fields=[
            SimpleNamespace(label=question, field_type="long_text", options=[]),
            SimpleNamespace(
                label="Which teams interest you?",
                field_type="multi_select",
                options=["Events", "Discord", "Socials"],
            ),
        ],
    )

    payload = build_application_question_payload(form)

    assert payload["fields"][0]["name"] == "Question 1"
    assert payload["fields"][0]["value"] == question
    assert "Choices:" in payload["fields"][1]["value"]
