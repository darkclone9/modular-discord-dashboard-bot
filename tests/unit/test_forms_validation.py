import pytest
from app.modules.forms.schemas import FormFieldCreate
from app.modules.forms.service import build_server_setup_form_payload
from app.modules.forms.validators import FieldDefinition, FormValidationError, validate_answers


def test_validate_answers_normalizes_supported_field_types() -> None:
    fields = [
        FieldDefinition("name", "Name", "short_text", True, []),
        FieldDefinition("about", "About", "long_text", False, []),
        FieldDefinition("rank", "Rank", "select", True, ["A", "B"]),
        FieldDefinition("roles", "Roles", "multi_select", True, ["Builder", "Helper"]),
        FieldDefinition("age", "Age", "number", True, []),
        FieldDefinition("agree", "Agree", "boolean", True, []),
    ]

    normalized = validate_answers(
        fields,
        {
            "name": " Gary ",
            "about": "",
            "rank": "A",
            "roles": "Builder, Helper",
            "age": "42",
            "agree": "yes",
        },
    )

    assert normalized == {
        "name": "Gary",
        "rank": "A",
        "roles": ["Builder", "Helper"],
        "age": 42,
        "agree": True,
    }


def test_validate_answers_rejects_missing_required_field() -> None:
    fields = [FieldDefinition("name", "Name", "short_text", True, [])]

    with pytest.raises(FormValidationError, match="Name is required"):
        validate_answers(fields, {})


def test_validate_answers_rejects_invalid_select_option() -> None:
    fields = [FieldDefinition("rank", "Rank", "select", True, ["A", "B"])]

    with pytest.raises(FormValidationError, match="configured options"):
        validate_answers(fields, {"rank": "C"})


def test_build_server_setup_payload_creates_required_long_text_questions() -> None:
    payload = build_server_setup_form_payload(
        title=" Staff Application ",
        description=" Apply for staff. ",
        post_channel_id="100",
        review_channel_id="200",
        reviewer_role_ids=["300"],
        auto_role_id="400",
        questions=[" Name and age? ", None, "Why do you want to help?"],
    )

    assert payload.title == "Staff Application"
    assert payload.description == "Apply for staff."
    assert payload.post_channel_id == "100"
    assert payload.review_settings.review_channel_id == "200"
    assert payload.review_settings.reviewer_role_ids == ["300"]
    assert payload.review_settings.auto_role_id == "400"
    assert [field.label for field in payload.fields] == [
        "Name and age?",
        "Why do you want to help?",
    ]
    assert all(field.field_type == "long_text" and field.required for field in payload.fields)


def test_build_server_setup_payload_uses_default_question_when_blank() -> None:
    payload = build_server_setup_form_payload(
        title="Quick Form",
        description="",
        post_channel_id="100",
        review_channel_id="200",
        reviewer_role_ids=["300"],
        auto_role_id=None,
        questions=[""],
    )

    assert [field.label for field in payload.fields] == ["Why do you want to apply?"]


def test_form_field_accepts_long_application_question() -> None:
    question = (
        "Tell us about a time you took initiative on something nobody asked you to do. "
        "What was it, why did you do it, and what came of it?"
    )

    field = FormFieldCreate(label=question, field_type="long_text", required=True)

    assert field.label == question
