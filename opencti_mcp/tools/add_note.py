from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import ADD_NOTE_MUTATION
from opencti_mcp.tools.tool_helpers import (
    ensure_arguments_dict,
    error_response,
    normalize_confidence,
    normalize_non_empty_string,
    normalize_string_list,
    success_response,
)
from opencti_mcp.utils.mutations import mutations_enabled

_MUTATIONS_DISABLED_MESSAGE = (
    "Mutations are disabled. Start the server with --enable-mutations "
    "or set OPENCTI_ENABLE_MUTATIONS=true."
)


async def handle(session: Any, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    if not mutations_enabled():
        return error_response(_MUTATIONS_DISABLED_MESSAGE)

    args_error = ensure_arguments_dict(arguments)
    if args_error:
        return error_response(args_error)

    content, content_error = normalize_non_empty_string(
        arguments.get("content"),
        "content",
        required=True,
    )
    if content_error:
        return error_response(content_error)
    assert content is not None

    objects, objects_error = normalize_string_list(
        arguments.get("objects"),
        "objects",
        required=True,
    )
    if objects_error:
        return error_response(objects_error)
    assert objects is not None

    note_types, note_types_error = normalize_string_list(arguments.get("note_types"), "note_types")
    if note_types_error:
        return error_response(note_types_error)
    if note_types is None:
        note_types = ["external"]

    confidence, confidence_error = normalize_confidence(arguments.get("confidence"), default=80)
    if confidence_error:
        return error_response(confidence_error)
    assert confidence is not None

    input_payload: dict[str, Any] = {
        "content": content,
        "objects": objects,
        "note_types": note_types,
        "confidence": confidence,
    }

    attribute_abstract_raw = arguments.get("attribute_abstract")
    attribute_abstract, attribute_abstract_error = normalize_non_empty_string(
        attribute_abstract_raw,
        "attribute_abstract",
    )
    if attribute_abstract_error:
        return error_response(attribute_abstract_error)
    if attribute_abstract_raw is not None and attribute_abstract is None:
        return error_response("attribute_abstract must be a non-empty string when provided")
    if attribute_abstract:
        input_payload["attribute_abstract"] = attribute_abstract

    try:
        result = await session.execute(
            gql(ADD_NOTE_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    note_data = result.get("noteAdd", {})
    return success_response(note_data)
