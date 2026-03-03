from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import CREATE_GROUPING_MUTATION
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

    name, name_error = normalize_non_empty_string(arguments.get("name"), "name", required=True)
    if name_error:
        return error_response(name_error)

    context, context_error = normalize_non_empty_string(
        arguments.get("context"),
        "context",
        required=True,
    )
    if context_error:
        return error_response(context_error)
    assert name is not None
    assert context is not None

    description, description_error = normalize_non_empty_string(
        arguments.get("description"), "description"
    )
    if description_error:
        return error_response(description_error)

    content, content_error = normalize_non_empty_string(arguments.get("content"), "content")
    if content_error:
        return error_response(content_error)

    objects, objects_error = normalize_string_list(arguments.get("objects"), "objects")
    if objects_error:
        return error_response(objects_error)

    object_marking, object_marking_error = normalize_string_list(
        arguments.get("object_marking"),
        "object_marking",
    )
    if object_marking_error:
        return error_response(object_marking_error)

    object_label, object_label_error = normalize_string_list(
        arguments.get("object_label"),
        "object_label",
    )
    if object_label_error:
        return error_response(object_label_error)

    external_references, external_references_error = normalize_string_list(
        arguments.get("external_references"),
        "external_references",
    )
    if external_references_error:
        return error_response(external_references_error)

    confidence, confidence_error = normalize_confidence(arguments.get("confidence"), default=80)
    if confidence_error:
        return error_response(confidence_error)

    update = arguments.get("update", False)
    if not isinstance(update, bool):
        return error_response("update must be a boolean")

    input_payload: dict[str, Any] = {
        "name": name,
        "context": context,
        "confidence": confidence,
        "update": update,
    }
    if description:
        input_payload["description"] = description
    if content:
        input_payload["content"] = content
    if objects:
        input_payload["objects"] = objects
    if object_marking:
        input_payload["objectMarking"] = object_marking
    if object_label:
        input_payload["objectLabel"] = object_label
    if external_references:
        input_payload["externalReferences"] = external_references

    try:
        result = await session.execute(
            gql(CREATE_GROUPING_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    return success_response(result.get("groupingAdd", {}))
