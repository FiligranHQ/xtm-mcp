import json
from typing import Any

from mcp import types as mcp_types


def error_response(message: str) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": message}, indent=2),
        )
    ]


def success_response(data: Any) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": True, "data": data}, indent=2),
        )
    ]


def ensure_arguments_dict(arguments: Any) -> str | None:
    if isinstance(arguments, dict):
        return None
    return f"arguments must be a dictionary, got {type(arguments)}"


def normalize_non_empty_string(
    value: Any, field_name: str, *, required: bool = False
) -> tuple[str | None, str | None]:
    if value is None:
        if required:
            return None, f"{field_name} is required"
        return None, None
    if not isinstance(value, str):
        return None, f"{field_name} must be a string"
    cleaned = value.strip()
    if required and not cleaned:
        return None, f"{field_name} is required and cannot be empty"
    if not required and not cleaned:
        return None, None
    return cleaned, None


def normalize_string_list(
    value: Any, field_name: str, *, required: bool = False
) -> tuple[list[str] | None, str | None]:
    if value is None:
        if required:
            return None, f"{field_name} is required"
        return None, None
    if not isinstance(value, list):
        return None, f"{field_name} must be a list of strings"

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return None, f"{field_name} must only contain strings"
        cleaned = item.strip()
        if not cleaned:
            return None, f"{field_name} cannot contain empty strings"
        normalized.append(cleaned)

    if required and not normalized:
        return None, f"{field_name} cannot be empty"
    return normalized, None


def normalize_first(value: Any, default: int = 50) -> tuple[int | None, str | None]:
    if value is None:
        return default, None
    if isinstance(value, bool) or not isinstance(value, int):
        return None, "first must be an integer between 1 and 500"
    if value < 1 or value > 500:
        return None, "first must be an integer between 1 and 500"
    return value, None


def normalize_confidence(value: Any, default: int = 80) -> tuple[int | None, str | None]:
    if value is None:
        return default, None
    if isinstance(value, bool) or not isinstance(value, int):
        return None, "confidence must be an integer between 0 and 100"
    if value < 0 or value > 100:
        return None, "confidence must be an integer between 0 and 100"
    return value, None
