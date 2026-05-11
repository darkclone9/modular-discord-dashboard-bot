from collections.abc import Sequence
from dataclasses import dataclass
import re
from typing import Any

SUPPORTED_FIELD_TYPES = {
    "short_text",
    "long_text",
    "select",
    "multi_select",
    "number",
    "boolean",
}


class FormValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class FieldDefinition:
    id: str
    label: str
    field_type: str
    required: bool
    options: list[str]


def coerce_field(field: Any) -> FieldDefinition:
    return FieldDefinition(
        id=str(getattr(field, "id", "") or getattr(field, "label", "")),
        label=str(field.label),
        field_type=str(field.field_type),
        required=bool(field.required),
        options=[str(option) for option in (getattr(field, "options", None) or [])],
    )


def validate_field_definitions(fields: Sequence[Any]) -> None:
    errors: list[str] = []
    for index, raw_field in enumerate(fields, start=1):
        field = coerce_field(raw_field)
        if field.field_type not in SUPPORTED_FIELD_TYPES:
            errors.append(f"Field {index} has unsupported type {field.field_type!r}")
        if field.field_type in {"select", "multi_select"} and not field.options:
            errors.append(f"Field {field.label!r} requires at least one option")
    if errors:
        raise FormValidationError(errors)


def validate_answers(fields: Sequence[Any], answers: dict[str, Any]) -> dict[str, object]:
    errors: list[str] = []
    normalized: dict[str, object] = {}

    for raw_field in fields:
        field = coerce_field(raw_field)
        value = answers.get(field.id, answers.get(field.label))

        if value in (None, "", []):
            if field.required:
                errors.append(f"{field.label} is required")
            continue

        try:
            normalized[field.id] = normalize_answer(field, value)
        except ValueError as exc:
            errors.append(f"{field.label}: {exc}")

    if errors:
        raise FormValidationError(errors)
    return normalized


def normalize_answer(field: FieldDefinition, value: Any) -> object:
    match field.field_type:
        case "short_text":
            return normalize_text(value, max_length=200)
        case "long_text":
            return normalize_text(value, max_length=4000)
        case "select":
            selected = normalize_text(value, max_length=100)
            if selected not in field.options:
                raise ValueError("must be one of the configured options")
            return selected
        case "multi_select":
            selected = normalize_multi_select(value)
            invalid = [item for item in selected if item not in field.options]
            if invalid:
                raise ValueError(f"invalid option(s): {', '.join(invalid)}")
            return selected
        case "number":
            return normalize_number(value)
        case "boolean":
            return normalize_boolean(value)
        case _:
            raise ValueError("unsupported field type")


def normalize_text(value: Any, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError("must be text")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"must be {max_length} characters or fewer")
    return value


def normalize_multi_select(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,\n]+", value) if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ValueError("must be a list or comma-separated text")


def normalize_number(value: Any) -> int | float:
    if isinstance(value, bool):
        raise ValueError("must be a number")
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        try:
            parsed = float(value.strip())
        except ValueError as exc:
            raise ValueError("must be a number") from exc
        return int(parsed) if parsed.is_integer() else parsed
    raise ValueError("must be a number")


def normalize_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "1"}:
            return True
        if lowered in {"false", "no", "n", "0"}:
            return False
    raise ValueError("must be true or false")
