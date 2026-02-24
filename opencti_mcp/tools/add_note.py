import json
from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import ADD_NOTE_MUTATION
from opencti_mcp.utils.mutations import mutations_enabled

_MUTATIONS_DISABLED_MESSAGE = (
    "Mutations are disabled. Start the server with --enable-mutations "
    "or set OPENCTI_ENABLE_MUTATIONS=true."
)


def _error_response(message: str) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": message}, indent=2),
        )
    ]


def _success_response(data: Any) -> list[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"success": True, "data": data}, indent=2),
        )
    ]


def _normalize_string_list(
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


def _normalize_confidence(value: Any) -> tuple[int | None, str | None]:
    if value is None:
        return 80, None
    if isinstance(value, bool) or not isinstance(value, int):
        return None, "confidence must be an integer between 0 and 100"
    if value < 0 or value > 100:
        return None, "confidence must be an integer between 0 and 100"
    return value, None


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    if not mutations_enabled():
        return _error_response(_MUTATIONS_DISABLED_MESSAGE)

    if not isinstance(arguments, dict):
        return _error_response(f"arguments must be a dictionary, got {type(arguments)}")

    content_raw = arguments.get("content")
    if not isinstance(content_raw, str) or not content_raw.strip():
        return _error_response("content is required and must be a non-empty string")
    content = content_raw.strip()

    objects, objects_error = _normalize_string_list(
        arguments.get("objects"),
        "objects",
        required=True,
    )
    if objects_error:
        return _error_response(objects_error)
    assert objects is not None  # appease type checker after required=True

    note_types, note_types_error = _normalize_string_list(arguments.get("note_types"), "note_types")
    if note_types_error:
        return _error_response(note_types_error)
    if note_types is None:
        note_types = ["external"]

    confidence, confidence_error = _normalize_confidence(arguments.get("confidence"))
    if confidence_error:
        return _error_response(confidence_error)

    input_payload: dict[str, Any] = {
        "content": content,
        "objects": objects,
        "note_types": note_types,
        "confidence": confidence,
    }

    attribute_abstract = arguments.get("attribute_abstract")
    if attribute_abstract is not None:
        if not isinstance(attribute_abstract, str) or not attribute_abstract.strip():
            return _error_response(
                "attribute_abstract must be a non-empty string when provided"
            )
        input_payload["attribute_abstract"] = attribute_abstract.strip()

    try:
        result = await session.execute(
            gql(ADD_NOTE_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return _error_response(str(error))

    note_data = result.get("noteAdd", {})
    return _success_response(note_data)
