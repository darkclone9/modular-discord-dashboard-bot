import pytest
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
