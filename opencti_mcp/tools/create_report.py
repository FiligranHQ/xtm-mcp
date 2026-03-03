from typing import Any

from gql import gql
from mcp import types as mcp_types

from opencti_mcp.graphql_queries import CREATE_REPORT_MUTATION
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
    assert name is not None

    description, description_error = normalize_non_empty_string(
        arguments.get("description"),
        "description",
        required=True,
    )
    if description_error:
        return error_response(description_error)
    assert description is not None

    report_types, report_types_error = normalize_string_list(
        arguments.get("report_types"),
        "report_types",
    )
    if report_types_error:
        return error_response(report_types_error)
    if report_types is None:
        report_types = ["threat-report"]

    confidence, confidence_error = normalize_confidence(arguments.get("confidence"), default=80)
    if confidence_error:
        return error_response(confidence_error)
    assert confidence is not None

    objects, objects_error = normalize_string_list(arguments.get("objects"), "objects")
    if objects_error:
        return error_response(objects_error)

    labels, labels_error = normalize_string_list(arguments.get("labels"), "labels")
    if labels_error:
        return error_response(labels_error)

    input_payload: dict[str, Any] = {
        "name": name,
        "description": description,
        "report_types": report_types,
        "confidence": confidence,
    }

    published_raw = arguments.get("published")
    published, published_error = normalize_non_empty_string(published_raw, "published")
    if published_error:
        return error_response(published_error)
    if published_raw is not None and published is None:
        return error_response("published must be a non-empty ISO date string when provided")
    if published:
        input_payload["published"] = published

    if objects:
        input_payload["objects"] = objects
    if labels:
        input_payload["objectLabel"] = labels

    try:
        result = await session.execute(
            gql(CREATE_REPORT_MUTATION),
            variable_values={"input": input_payload},
        )
    except Exception as error:  # noqa: BLE001
        return error_response(str(error))

    report_data = result.get("reportAdd", {})
    return success_response(report_data)
